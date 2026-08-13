#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y ca-certificates curl gnupg unattended-upgrades

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu %s stable\n' "$(dpkg --print-architecture)" "$VERSION_CODENAME" > /etc/apt/sources.list.d/docker.list

curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg -o /etc/apt/keyrings/google-cloud-cli.asc
printf 'deb [signed-by=/etc/apt/keyrings/google-cloud-cli.asc] https://packages.cloud.google.com/apt cloud-sdk main\n' > /etc/apt/sources.list.d/google-cloud-sdk.list

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin google-cloud-cli
systemctl enable --now docker

curl -fsSLO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
bash add-google-cloud-ops-agent-repo.sh --also-install
rm -f add-google-cloud-ops-agent-repo.sh

install -d -m 0750 /srv/corpus
install -d -m 0750 -o 10001 -g 10001 /srv/corpus/state /srv/corpus/data
install -d -m 0750 /srv/corpus/deploy /srv/corpus/backups
install -d -m 0750 /srv/corpus/caddy/data /srv/corpus/caddy/config
install -d -m 0700 /run/corpus

dpkg-reconfigure -f noninteractive unattended-upgrades

docker --version
docker compose version
gcloud --version | head -n 1

