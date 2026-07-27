$ErrorActionPreference = "Stop"
$RepositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$PythonExecutable = Join-Path $RepositoryRoot ".venv\Scripts\python.exe"
$EnvironmentPath = Join-Path $RepositoryRoot ".env.local"

if (-not (Test-Path -LiteralPath $PythonExecutable)) {
    throw "Local environment is missing. Run scripts/init-local.ps1 first."
}
if (-not (Test-Path -LiteralPath $EnvironmentPath)) {
    throw "Configuration is missing. Run scripts/init-local.ps1 first."
}

& $PythonExecutable -m uvicorn corpus.main:create_live_app --factory --host 127.0.0.1 --port 8099
