param(
    [string]$RouteDeckPath = (Join-Path $PSScriptRoot "..\..\routedeck")
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$ResolvedRouteDeck = [IO.Path]::GetFullPath($RouteDeckPath)
$VirtualEnvironment = Join-Path $RepositoryRoot ".venv"
$PythonExecutable = Join-Path $VirtualEnvironment "Scripts\python.exe"
$RuntimeDirectory = Join-Path $RepositoryRoot ".runtime"
$EnvironmentPath = Join-Path $RepositoryRoot ".env.local"
$BackendPackage = (Join-Path $RepositoryRoot "backend") + "[testing]"

if (-not (Test-Path -LiteralPath (Join-Path $ResolvedRouteDeck "pyproject.toml"))) {
    throw "RouteDeck source checkout not found at $ResolvedRouteDeck"
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.11 is required."
}
if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    throw "pnpm is required."
}
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw "Ollama is required."
}

if (-not (Test-Path -LiteralPath $PythonExecutable)) {
    & python -m venv $VirtualEnvironment
}

& $PythonExecutable -m pip install --disable-pip-version-check -e "$ResolvedRouteDeck[fastapi,langgraph,persistence,testing]"
& $PythonExecutable -m pip install --disable-pip-version-check "fastapi-users[sqlalchemy]==15.0.5" "fastapi-users-db-sqlalchemy==7.0.0" "sqlalchemy==2.0.51" "aiosqlite==0.22.1" "alembic==1.18.5" "email-validator==2.3.0"
& $PythonExecutable -m pip install --disable-pip-version-check -e $BackendPackage
& pnpm --dir (Join-Path $RepositoryRoot "frontend") install --frozen-lockfile

New-Item -ItemType Directory -Force -Path $RuntimeDirectory | Out-Null
if (-not (Test-Path -LiteralPath $EnvironmentPath)) {
    $EncryptionKey = & $PythonExecutable -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    $DatabasePath = (Join-Path $RuntimeDirectory "routedeck.sqlite").Replace("\", "/")
    $CorpusDatabasePath = (Join-Path $RuntimeDirectory "corpus.sqlite3").Replace("\", "/")
    $JobQueuePath = (Join-Path $RuntimeDirectory "corpus-jobs.sqlite3").Replace("\", "/")
    $SourceDataPath = (Join-Path $RuntimeDirectory "sources").Replace("\", "/")
    $ResetSecret = & $PythonExecutable -c "import secrets; print(secrets.token_urlsafe(48))"
    $VerificationSecret = & $PythonExecutable -c "import secrets; print(secrets.token_urlsafe(48))"
    $CredentialVaultKey = & $PythonExecutable -c "import base64; from nacl.secret import SecretBox; from nacl.utils import random; print(base64.urlsafe_b64encode(random(SecretBox.KEY_SIZE)).decode())"
    $EnvironmentLines = @(
        "ROUTEDECK_DATABASE_URL=sqlite+pysqlite:///$DatabasePath"
        "ROUTEDECK_STATE_ENCRYPTION_KEY=$EncryptionKey"
        "ROUTEDECK_INSTANCE_ID=corpus-local"
        "ROUTEDECK_REVIEW_TTL_SECONDS=900"
        "ROUTEDECK_RESUME_CAPABILITY_TTL_SECONDS=86400"
        "ROUTEDECK_WORKER_COUNT=1"
        "ROUTEDECK_BROWSER_ORIGINS=http://127.0.0.1:5199"
        "OLLAMA_BASE_URL=http://127.0.0.1:11434"
        "OLLAMA_MODEL=gemma4:latest"
        "CORPUS_SOURCE_DATA_ROOT=$SourceDataPath"
        "CORPUS_API_SOURCE_MAX_UPLOAD_BYTES=20971520"
        "CORPUS_TOOLROUTER_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2"
        "CORPUS_TOOLROUTER_EMBEDDING_REVISION=1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
        "CORPUS_TOOLROUTER_EMBEDDING_DEVICE=cpu"
        "CORPUS_TOOLROUTER_EMBEDDING_BATCH_SIZE=64"
        "CORPUS_TOOLROUTER_EMBEDDING_LOCAL_FILES_ONLY=true"
        "CORPUS_TOOLROUTER_OLLAMA_URL=http://127.0.0.1:11434"
        "CORPUS_TOOLROUTER_GENERATOR_MODEL=gemma4:latest"
        "CORPUS_TOOLROUTER_REVIEWER_MODEL=qwen2.5-coder:7b"
        "CORPUS_TOOLROUTER_EVALSET_TIMEOUT_SECONDS=240"
        "CORPUS_DATABASE_URL=sqlite+aiosqlite:///$CorpusDatabasePath"
        "CORPUS_MIGRATION_REVISION=0019_builder_assembly_lifecycle"
        "CORPUS_JOB_QUEUE_PATH=$JobQueuePath"
        "CORPUS_CREDENTIAL_VAULT_KEY=$CredentialVaultKey"
        "CORPUS_RESET_SECRET=$ResetSecret"
        "CORPUS_VERIFICATION_SECRET=$VerificationSecret"
        "CORPUS_AUTH_ACCESS_TOKEN_MINUTES=15"
        "CORPUS_AUTH_IDLE_SESSION_DAYS=7"
        "CORPUS_AUTH_ABSOLUTE_SESSION_DAYS=30"
        "CORPUS_VERIFICATION_TOKEN_HOURS=24"
        "CORPUS_RESET_TOKEN_HOURS=1"
        "CORPUS_PUBLIC_FRONTEND_URL=http://127.0.0.1:5199"
        "CORPUS_TRUSTED_PROXIES=127.0.0.1"
        "CORPUS_SMTP_HOST=smtp.gmail.com"
        "CORPUS_SMTP_PORT=587"
        "CORPUS_SMTP_STARTTLS=true"
        "CORPUS_SMTP_USERNAME=no-reply@saastoagent.com"
        "CORPUS_SMTP_FROM_ADDRESS=no-reply@saastoagent.com"
        "CORPUS_SMTP_TIMEOUT_SECONDS=5"
    )
    [IO.File]::WriteAllLines($EnvironmentPath, $EnvironmentLines)
} else {
    $CurrentEnvironmentLines = [IO.File]::ReadAllLines($EnvironmentPath)
    $CurrentEnvironmentLines = @(
        foreach ($Line in $CurrentEnvironmentLines) {
            if ($Line -match '^\s*CORPUS_MIGRATION_REVISION=') {
                "CORPUS_MIGRATION_REVISION=0019_builder_assembly_lifecycle"
            } else {
                $Line
            }
        }
    )
    [IO.File]::WriteAllLines($EnvironmentPath, [string[]]$CurrentEnvironmentLines)
    $ExistingNames = @{}
    foreach ($Line in [IO.File]::ReadAllLines($EnvironmentPath)) {
        if ($Line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=') {
            $ExistingNames[$Matches[1]] = $true
        }
    }
    $CorpusDatabasePath = (Join-Path $RuntimeDirectory "corpus.sqlite3").Replace("\", "/")
    $JobQueuePath = (Join-Path $RuntimeDirectory "corpus-jobs.sqlite3").Replace("\", "/")
    $SourceDataPath = (Join-Path $RuntimeDirectory "sources").Replace("\", "/")
    $ResetSecret = & $PythonExecutable -c "import secrets; print(secrets.token_urlsafe(48))"
    $VerificationSecret = & $PythonExecutable -c "import secrets; print(secrets.token_urlsafe(48))"
    $CredentialVaultKey = & $PythonExecutable -c "import base64; from nacl.secret import SecretBox; from nacl.utils import random; print(base64.urlsafe_b64encode(random(SecretBox.KEY_SIZE)).decode())"
    $RequiredRuntimeLines = [ordered]@{
        CORPUS_DATABASE_URL = "sqlite+aiosqlite:///$CorpusDatabasePath"
        CORPUS_MIGRATION_REVISION = "0019_builder_assembly_lifecycle"
        CORPUS_JOB_QUEUE_PATH = $JobQueuePath
        CORPUS_CREDENTIAL_VAULT_KEY = $CredentialVaultKey
        CORPUS_RESET_SECRET = $ResetSecret
        CORPUS_VERIFICATION_SECRET = $VerificationSecret
        CORPUS_AUTH_ACCESS_TOKEN_MINUTES = "15"
        CORPUS_AUTH_IDLE_SESSION_DAYS = "7"
        CORPUS_AUTH_ABSOLUTE_SESSION_DAYS = "30"
        CORPUS_VERIFICATION_TOKEN_HOURS = "24"
        CORPUS_RESET_TOKEN_HOURS = "1"
        CORPUS_PUBLIC_FRONTEND_URL = "http://127.0.0.1:5199"
        CORPUS_TRUSTED_PROXIES = "127.0.0.1"
        CORPUS_SMTP_HOST = "smtp.gmail.com"
        CORPUS_SMTP_PORT = "587"
        CORPUS_SMTP_STARTTLS = "true"
        CORPUS_SMTP_USERNAME = "no-reply@saastoagent.com"
        CORPUS_SMTP_FROM_ADDRESS = "no-reply@saastoagent.com"
        CORPUS_SMTP_TIMEOUT_SECONDS = "5"
        CORPUS_SOURCE_DATA_ROOT = $SourceDataPath
        CORPUS_API_SOURCE_MAX_UPLOAD_BYTES = "20971520"
        CORPUS_TOOLROUTER_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
        CORPUS_TOOLROUTER_EMBEDDING_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
        CORPUS_TOOLROUTER_EMBEDDING_DEVICE = "cpu"
        CORPUS_TOOLROUTER_EMBEDDING_BATCH_SIZE = "64"
        CORPUS_TOOLROUTER_EMBEDDING_LOCAL_FILES_ONLY = "true"
        CORPUS_TOOLROUTER_OLLAMA_URL = "http://127.0.0.1:11434"
        CORPUS_TOOLROUTER_GENERATOR_MODEL = "gemma4:latest"
        CORPUS_TOOLROUTER_REVIEWER_MODEL = "qwen2.5-coder:7b"
        CORPUS_TOOLROUTER_EVALSET_TIMEOUT_SECONDS = "240"
    }
    $MissingLines = @(
        foreach ($Entry in $RequiredRuntimeLines.GetEnumerator()) {
            if (-not $ExistingNames.ContainsKey($Entry.Key)) {
                "$($Entry.Key)=$($Entry.Value)"
            }
        }
    )
    if ($MissingLines.Count -gt 0) {
        [IO.File]::AppendAllLines($EnvironmentPath, [string[]]$MissingLines)
    }
}

& $PythonExecutable -m corpus.persistence.migrations

$Models = (& ollama list) -join "`n"
if ($Models -notmatch "(?m)^gemma4:latest\s") {
    throw "Required model gemma4:latest is not installed. Run: ollama pull gemma4:latest"
}
if ($Models -notmatch "(?m)^qwen2\.5-coder:7b\s") {
    throw "Required evalset reviewer qwen2.5-coder:7b is not installed. Run: ollama pull qwen2.5-coder:7b"
}

& $PythonExecutable -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', revision='1110a243fdf4706b3f48f1d95db1a4f5529b4d41', device='cpu'); print('Pinned MiniLM embedding model is cached.')"

Write-Output "Corpus local environment is ready."
Write-Output "Backend: scripts/run-backend.ps1"
Write-Output "Frontend: scripts/run-frontend.ps1"
