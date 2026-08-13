[CmdletBinding()]
param([string]$ProjectId = "saastoagent")

$ErrorActionPreference = "Continue"
if ($ProjectId -ne "saastoagent") {
    throw "This deployment script is restricted to project saastoagent."
}

$region = "asia-south1"
$serviceAccountName = "corpus-vm"
$serviceAccountEmail = "corpus-vm@saastoagent.iam.gserviceaccount.com"
$repository = "corpus"
$bucket = "saastoagent-corpus-backups-42047064897"
$instance = "corpus-vm-1"
$address = "corpus-origin-ip"
$snapshotPolicy = "corpus-daily-snapshots"
$zones = @("asia-south1-a", "asia-south1-b", "asia-south1-c")
$lifecyclePath = Join-Path $PSScriptRoot "bucket-lifecycle.json"

function Invoke-Gcloud {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$CommandArguments)
    & gcloud.cmd @CommandArguments
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud command failed: $($CommandArguments -join ' ')"
    }
}

$serviceAccounts = @(& gcloud.cmd iam service-accounts list --project=$ProjectId --format="value(email)")
if ($LASTEXITCODE -ne 0) { throw "Could not list service accounts." }
if ($serviceAccounts -notcontains $serviceAccountEmail) {
    Invoke-Gcloud iam service-accounts create $serviceAccountName --project=$ProjectId --display-name="Corpus production VM"
}

$repositories = @(& gcloud.cmd artifacts repositories list --project=$ProjectId --location=$region --format="value(name.basename())")
if ($LASTEXITCODE -ne 0) { throw "Could not list Artifact Registry repositories." }
if ($repositories -notcontains $repository) {
    Invoke-Gcloud artifacts repositories create $repository --project=$ProjectId --location=$region --repository-format=docker --immutable-tags --description="Corpus production images"
}
Invoke-Gcloud artifacts repositories add-iam-policy-binding $repository --project=$ProjectId --location=$region --member="serviceAccount:$serviceAccountEmail" --role="roles/artifactregistry.reader" 1>$null

$buckets = @(& gcloud.cmd storage buckets list --project=$ProjectId --format="value(name)")
if ($LASTEXITCODE -ne 0) { throw "Could not list Cloud Storage buckets." }
if (($buckets -notcontains $bucket) -and ($buckets -notcontains "gs://$bucket")) {
    Invoke-Gcloud storage buckets create "gs://$bucket" --project=$ProjectId --location=$region --uniform-bucket-level-access --public-access-prevention
}
Invoke-Gcloud storage buckets update "gs://$bucket" --project=$ProjectId --versioning "--lifecycle-file=$lifecyclePath" 1>$null
Invoke-Gcloud storage buckets add-iam-policy-binding "gs://$bucket" --project=$ProjectId --member="serviceAccount:$serviceAccountEmail" --role="roles/storage.objectCreator" 1>$null
Invoke-Gcloud storage buckets add-iam-policy-binding "gs://$bucket" --project=$ProjectId --member="serviceAccount:$serviceAccountEmail" --role="roles/storage.objectViewer" 1>$null

foreach ($secretName in @(
    "corpus-openai-api-key",
    "corpus-smtp-app-password",
    "corpus-routedeck-state-encryption-key",
    "corpus-credential-vault-key",
    "corpus-reset-secret",
    "corpus-verification-secret"
)) {
    Invoke-Gcloud secrets add-iam-policy-binding $secretName --project=$ProjectId --member="serviceAccount:$serviceAccountEmail" --role="roles/secretmanager.secretAccessor" 1>$null
}
Invoke-Gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$serviceAccountEmail" --role="roles/logging.logWriter" --condition=None 1>$null
Invoke-Gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$serviceAccountEmail" --role="roles/monitoring.metricWriter" --condition=None 1>$null

$policies = @(& gcloud.cmd compute resource-policies list --project=$ProjectId --filter="name=$snapshotPolicy" --format="value(name)")
if ($LASTEXITCODE -ne 0) { throw "Could not list snapshot policies." }
if ($policies -notcontains $snapshotPolicy) {
    Invoke-Gcloud compute resource-policies create snapshot-schedule $snapshotPolicy --project=$ProjectId --region=$region --daily-schedule --start-time=03:00 --max-retention-days=7 --on-source-disk-delete=keep-auto-snapshots
}

$firewalls = @(& gcloud.cmd compute firewall-rules list --project=$ProjectId --format="value(name)")
if ($LASTEXITCODE -ne 0) { throw "Could not list firewall rules." }
if ($firewalls -notcontains "corpus-web-ipv4") {
    Invoke-Gcloud compute firewall-rules create corpus-web-ipv4 --project=$ProjectId --network=default --direction=INGRESS --priority=1000 --action=ALLOW "--rules=tcp:80,tcp:443" --source-ranges=0.0.0.0/0 --target-tags=corpus-web
}
if ($firewalls -notcontains "corpus-web-ipv6") {
    Invoke-Gcloud compute firewall-rules create corpus-web-ipv6 --project=$ProjectId --network=default --direction=INGRESS --priority=1000 --action=ALLOW "--rules=tcp:80,tcp:443" --source-ranges=::/0 --target-tags=corpus-web
}
if ($firewalls -notcontains "corpus-iap-ssh") {
    Invoke-Gcloud compute firewall-rules create corpus-iap-ssh --project=$ProjectId --network=default --direction=INGRESS --priority=1000 --action=ALLOW --rules=tcp:22 --source-ranges=35.235.240.0/20 --target-tags=corpus-iap-ssh
}
if ($firewalls -notcontains "corpus-deny-public-admin") {
    Invoke-Gcloud compute firewall-rules create corpus-deny-public-admin --project=$ProjectId --network=default --direction=INGRESS --priority=1100 --action=DENY "--rules=tcp:22,tcp:3389" --source-ranges=0.0.0.0/0 --target-tags=corpus-iap-ssh
}

$addresses = @(& gcloud.cmd compute addresses list --project=$ProjectId --regions=$region --format="value(name)")
if ($LASTEXITCODE -ne 0) { throw "Could not list regional addresses." }
if ($addresses -notcontains $address) {
    Invoke-Gcloud compute addresses create $address --project=$ProjectId --region=$region --network-tier=PREMIUM
}

$instances = @(& gcloud.cmd compute instances list --project=$ProjectId --filter="name=$instance" --format="value(name)")
if ($LASTEXITCODE -ne 0) { throw "Could not list Compute Engine instances." }
$selectedZone = $null
if ($instances -notcontains $instance) {
    $upZones = @(& gcloud.cmd compute zones list --project=$ProjectId --filter="region:($region) status=UP" --format="value(name)")
    if ($LASTEXITCODE -ne 0) { throw "Could not inspect Mumbai zones." }
    foreach ($zone in $zones) {
        if ($upZones -notcontains $zone) { continue }
        $createArguments = @(
            "compute", "instances", "create", $instance,
            "--project=$ProjectId", "--zone=$zone", "--machine-type=n2-standard-2",
            "--network-tier=PREMIUM", "--address=$address",
            "--image-family=ubuntu-2404-lts-amd64", "--image-project=ubuntu-os-cloud",
            "--boot-disk-size=160GB", "--boot-disk-type=pd-balanced", "--boot-disk-device-name=$instance",
            "--service-account=$serviceAccountEmail", "--scopes=https://www.googleapis.com/auth/cloud-platform",
            "--tags=corpus-web,corpus-iap-ssh",
            "--metadata=enable-oslogin=TRUE,block-project-ssh-keys=TRUE",
            "--shielded-secure-boot", "--shielded-vtpm", "--shielded-integrity-monitoring",
            "--deletion-protection"
        )
        $creationOutput = (& gcloud.cmd @createArguments 2>&1 | Out-String)
        if ($LASTEXITCODE -eq 0) {
            $selectedZone = $zone
            break
        }
        if ($creationOutput -notmatch "ZONE_RESOURCE_POOL_EXHAUSTED|resource pool|does not have enough resources") {
            throw "VM creation failed outside the allowed capacity fallback: $creationOutput"
        }
        Write-Host "$zone has no current N2 capacity; trying the next UP Mumbai zone."
    }
    if ($null -eq $selectedZone) {
        throw "No UP Mumbai zone had capacity for n2-standard-2."
    }
} else {
    $selectedZone = (& gcloud.cmd compute instances list --project=$ProjectId --filter="name=$instance" --format="value(zone.basename())").Trim()
}

$diskPolicies = @(& gcloud.cmd compute disks describe $instance --project=$ProjectId --zone=$selectedZone --format="value(resourcePolicies.basename())")
if ($LASTEXITCODE -ne 0) { throw "Could not inspect the VM boot disk." }
if ($diskPolicies -notcontains $snapshotPolicy) {
    Invoke-Gcloud compute disks add-resource-policies $instance --project=$ProjectId --zone=$selectedZone --resource-policies=$snapshotPolicy
}

Write-Host "Corpus infrastructure ready: one VM named $instance in $selectedZone."
