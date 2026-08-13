#!/usr/bin/env bash
set -euo pipefail

project_id="saastoagent"
destination="/run/corpus/runtime.env"
temporary="/run/corpus/runtime.env.tmp"

umask 077
install -d -m 0700 /run/corpus
rm -f "$temporary"
touch "$temporary"
chmod 600 "$temporary"

append_secret() {
    local environment_name="$1"
    local secret_name="$2"
    local value
    value="$(gcloud secrets versions access latest --secret="$secret_name" --project="$project_id")"
    if [[ -z "$value" || "$value" == *$'\n'* || "$value" == *$'\r'* ]]; then
        printf 'Invalid value retrieved for %s.\n' "$secret_name" >&2
        exit 1
    fi
    printf '%s=%s\n' "$environment_name" "$value" >> "$temporary"
    unset value
}

append_secret OPENAI_API_KEY corpus-openai-api-key
append_secret CORPUS_SMTP_APP_PASSWORD corpus-smtp-app-password
append_secret ROUTEDECK_STATE_ENCRYPTION_KEY corpus-routedeck-state-encryption-key
append_secret CORPUS_CREDENTIAL_VAULT_KEY corpus-credential-vault-key
append_secret CORPUS_RESET_SECRET corpus-reset-secret
append_secret CORPUS_VERIFICATION_SECRET corpus-verification-secret

[[ "$(wc -l < "$temporary")" -eq 6 ]]
chmod 600 "$temporary"
mv -f "$temporary" "$destination"
printf 'Retrieved 6 Corpus runtime secrets into a mode-0600 environment file.\n'

