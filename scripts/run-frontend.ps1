$ErrorActionPreference = "Stop"
$RepositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$FrontendRoot = Join-Path $RepositoryRoot "frontend"

if (-not (Test-Path -LiteralPath (Join-Path $FrontendRoot "node_modules"))) {
    throw "Frontend dependencies are missing. Run scripts/init-local.ps1 first."
}

& pnpm --dir $FrontendRoot dev
