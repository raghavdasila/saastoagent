[CmdletBinding()]
param(
    [string]$ProjectId = "saastoagent",
    [string]$EnvironmentFile = ".env.local",
    [switch]$ForceNewCredentialVaultVersion
)

$ErrorActionPreference = "Stop"

if ($ProjectId -ne "saastoagent") {
    throw "This deployment script is restricted to project saastoagent."
}

function Read-EnvironmentFile {
    param([string]$Path)
    $values = @{}
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $values
    }
    foreach ($line in Get-Content -LiteralPath $Path) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.TrimStart().StartsWith("#") -or -not $line.Contains("=")) {
            continue
        }
        $name, $value = $line.Split("=", 2)
        $values[$name.Trim()] = $value.Trim()
    }
    return $values
}

function New-Base64UrlSecret {
    param([int]$ByteCount)
    $bytes = New-Object byte[] $ByteCount
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($bytes)
    }
    finally {
        $generator.Dispose()
    }
    return [Convert]::ToBase64String($bytes).Replace("+", "-").Replace("/", "_")
}

$inventory = @(
    @{ Secret = "corpus-openai-api-key"; Environment = "OPENAI_API_KEY"; RequiredLocal = $true; Bytes = 0 },
    @{ Secret = "corpus-smtp-app-password"; Environment = "CORPUS_SMTP_APP_PASSWORD"; RequiredLocal = $true; Bytes = 0 },
    @{ Secret = "corpus-routedeck-state-encryption-key"; Environment = "ROUTEDECK_STATE_ENCRYPTION_KEY"; RequiredLocal = $false; Bytes = 32 },
    @{ Secret = "corpus-credential-vault-key"; Environment = "CORPUS_CREDENTIAL_VAULT_KEY"; RequiredLocal = $false; Bytes = 32 },
    @{ Secret = "corpus-reset-secret"; Environment = "CORPUS_RESET_SECRET"; RequiredLocal = $false; Bytes = 48 },
    @{ Secret = "corpus-verification-secret"; Environment = "CORPUS_VERIFICATION_SECRET"; RequiredLocal = $false; Bytes = 48 }
)

$environment = Read-EnvironmentFile -Path $EnvironmentFile
$stagingDirectory = Join-Path $PSScriptRoot "../.runtime/deployment"
New-Item -ItemType Directory -Path $stagingDirectory -Force | Out-Null
$existingSecretNames = @(& gcloud.cmd secrets list --project=$ProjectId --format="value(name)")
if ($LASTEXITCODE -ne 0) {
    throw "Could not list Secret Manager inventory."
}

foreach ($item in $inventory) {
    $secretName = $item.Secret
    $secretExists = $existingSecretNames -contains $secretName
    $forceNewVersion = $ForceNewCredentialVaultVersion -and $secretName -eq "corpus-credential-vault-key"
    if ($secretExists -and -not $forceNewVersion) {
        $enabledVersion = & gcloud.cmd secrets versions list $secretName --project=$ProjectId --filter="state=ENABLED" --limit=1 --format="value(name)"
        if ($LASTEXITCODE -ne 0) {
            throw "Could not inspect versions for $secretName."
        }
        if (-not [string]::IsNullOrWhiteSpace(($enabledVersion | Out-String))) {
            Write-Host "${secretName}: present"
            continue
        }
    }

    $value = $environment[$item.Environment]
    if ($forceNewVersion) {
        $value = New-Base64UrlSecret -ByteCount 32
    }
    if ([string]::IsNullOrWhiteSpace($value)) {
        if ($item.RequiredLocal) {
            throw "$($item.Environment) is required in $EnvironmentFile."
        }
        $value = New-Base64UrlSecret -ByteCount $item.Bytes
    }

    if (-not $secretExists) {
        & gcloud.cmd secrets create $secretName --project=$ProjectId --replication-policy=user-managed --locations=asia-south1 --labels="application=corpus,environment=production" --quiet
        if ($LASTEXITCODE -ne 0) {
            throw "Could not create $secretName."
        }
        $existingSecretNames += $secretName
        Write-Host "${secretName}: created"
    }

    $temporaryPath = Join-Path $stagingDirectory "$secretName.upload"
    try {
        [System.IO.File]::WriteAllText($temporaryPath, $value, [System.Text.UTF8Encoding]::new($false))
        & icacls $temporaryPath /inheritance:r /grant:r "$($env:USERNAME):(R,W,D)" 1>$null
        & gcloud.cmd secrets versions add $secretName --project=$ProjectId --data-file=$temporaryPath --quiet 1>$null
        if ($LASTEXITCODE -ne 0) {
            throw "Could not add a value for $secretName."
        }
        Write-Host "${secretName}: new version added"
    }
    finally {
        $value = $null
        if (Test-Path -LiteralPath $temporaryPath) {
            Remove-Item -LiteralPath $temporaryPath -Force
        }
    }
}
