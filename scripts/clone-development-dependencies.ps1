param(
    [string]$ManifestPath = (
        Join-Path $PSScriptRoot "..\contracts\dependency-provenance\development-source-checkouts.json"
    )
)

$ErrorActionPreference = "Stop"
$CorpusRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$WorkspaceRoot = [IO.Path]::GetFullPath((Join-Path $CorpusRoot ".."))
$ResolvedManifest = [IO.Path]::GetFullPath($ManifestPath)

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is required."
}
if (-not (Test-Path -LiteralPath $ResolvedManifest -PathType Leaf)) {
    throw "Development source manifest not found: $ResolvedManifest"
}

$Manifest = Get-Content -LiteralPath $ResolvedManifest -Raw | ConvertFrom-Json
if ($Manifest.schema_version -ne 1 -or -not $Manifest.dependencies) {
    throw "Unsupported or empty development source manifest."
}

foreach ($Dependency in $Manifest.dependencies) {
    $Directory = [string]$Dependency.directory
    $Repository = [string]$Dependency.repository
    $Commit = [string]$Dependency.commit
    if ($Directory -notmatch '^[a-z0-9][a-z0-9-]+$') {
        throw "Unsafe dependency directory: $Directory"
    }
    if ($Repository -notmatch '^https://github\.com/saastoagent/[a-z0-9-]+\.git$') {
        throw "Unsupported dependency repository: $Repository"
    }
    if ($Commit -notmatch '^[0-9a-f]{40}$') {
        throw "Invalid pinned commit for $Directory."
    }

    $Target = [IO.Path]::GetFullPath((Join-Path $WorkspaceRoot $Directory))
    $ExpectedTarget = [IO.Path]::GetFullPath("$WorkspaceRoot\$Directory")
    if ($Target -ne $ExpectedTarget -or $Target -eq $CorpusRoot) {
        throw "Dependency target escaped the workspace root: $Target"
    }
    if (Test-Path -LiteralPath $Target) {
        throw "Dependency target already exists; refusing to modify it: $Target"
    }

    Write-Output "Cloning $($Dependency.name) at $Commit into $Target"
    & git clone --no-checkout $Repository $Target
    if ($LASTEXITCODE -ne 0) {
        throw "Clone failed for $Repository. A partial directory may remain at $Target."
    }
    & git -C $Target checkout --detach $Commit
    if ($LASTEXITCODE -ne 0) {
        throw "Pinned checkout failed for $Directory at $Commit."
    }
    $ActualCommit = (& git -C $Target rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $ActualCommit -ne $Commit) {
        throw "Pinned checkout verification failed for $Directory."
    }
}

Write-Output "Corpus development source dependencies are pinned and ready."
