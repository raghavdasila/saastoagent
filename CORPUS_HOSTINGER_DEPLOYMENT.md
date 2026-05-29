# Hostinger Deployment Reference: Corpus SaaStoAgent

Last updated: 2026-05-28  
Public URL: https://corpus.saastoagent.com  
Repo: https://github.com/Highpolar-Softwares/saastoagent-corpus  
Server: Hostinger VPS `82.112.255.56`  
SSH: `ssh -p 22785 root@82.112.255.56`

## 1. Production topology

```text
App repo path:
/home/info_highpolar/saastoagent-v0.1

RouteDeck symlink:
/home/info_highpolar/routedeck
-> /home/info_highpolar/the-agent-lab-sparse/agent-lab-powered-projects/routedeck

RouteDeck sparse source:
/home/info_highpolar/the-agent-lab-sparse

Env file:
/etc/corpus-saastoagent/corpus.env

Compose files:
/home/info_highpolar/saastoagent-v0.1/docker-compose.yml
/home/info_highpolar/saastoagent-v0.1/docker-compose.hostinger.yml

Nginx:
/etc/nginx/conf.d/corpus.saastoagent.com.conf

Systemd:
/etc/systemd/system/corpus-saastoagent.service
```

## 2. Runtime ports

```text
Frontend: 127.0.0.1:3007 -> container 3000
Backend:  127.0.0.1:8085 -> container 8000
Postgres: Docker network only, no public host port

Nginx:
/      -> 127.0.0.1:3007
/api/  -> 127.0.0.1:8085/api/
```

The frontend/backend ports must remain localhost-only. Do not expose `3007` or `8085` publicly.

## 3. DNS

Hostinger DNS:

| Type | Name | Value |
|---|---|---|
| A | `corpus` | `82.112.255.56` |

Only ports `80` and `443` need to be public.

## 4. Files not to commit

Do not commit:

```text
/etc/corpus-saastoagent/corpus.env
/home/info_highpolar/saastoagent-v0.1/docker-compose.hostinger.yml
```

`docker-compose.hostinger.yml` is server-specific and remains untracked.

## 5. Hostinger compose override

File:

```text
/home/info_highpolar/saastoagent-v0.1/docker-compose.hostinger.yml
```

Content:

```yaml
services:
  backend:
    env_file:
      - /etc/corpus-saastoagent/corpus.env
    ports: !override
      - "127.0.0.1:8085:8000"
    restart: unless-stopped
    extra_hosts:
      - "host.docker.internal:host-gateway"

  frontend:
    env_file:
      - /etc/corpus-saastoagent/corpus.env
    ports: !override
      - "127.0.0.1:3007:3000"
    restart: unless-stopped
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

Important: `ports: !override` is required. Without it, Docker Compose can merge the base ports and override ports, causing duplicate port binding.

## 6. Env file

File:

```text
/etc/corpus-saastoagent/corpus.env
```

Create/edit:

```bash
sudo mkdir -p /etc/corpus-saastoagent
sudo chmod 700 /etc/corpus-saastoagent
sudo nano /etc/corpus-saastoagent/corpus.env
sudo chown root:root /etc/corpus-saastoagent/corpus.env
sudo chmod 600 /etc/corpus-saastoagent/corpus.env
```

Do not print this file with `cat`. Do not commit it.

## 7. Vite preview host fix

The deployed frontend requires this in:

```text
frontend/vite.config.ts
```

```ts
preview: {
  host: '0.0.0.0',
  port: 3000,
  allowedHosts: ['corpus.saastoagent.com'],
  proxy: apiProxy,
},
```

Committed fix:

```text
Commit: a8013de
Message: Allow corpus domain in Vite preview
```

## 8. Initial deployment commands

Clone standalone repo:

```bash
sudo -iu info_highpolar git clone https://github.com/Highpolar-Softwares/saastoagent-corpus.git /home/info_highpolar/saastoagent-v0.1
```

Clone RouteDeck dependency using sparse checkout:

```bash
sudo -iu info_highpolar git clone --filter=blob:none --sparse --branch saastoagent https://github.com/Highpolar-Softwares/the-agent-lab.git /home/info_highpolar/the-agent-lab-sparse

sudo -u info_highpolar git -C /home/info_highpolar/the-agent-lab-sparse sparse-checkout set agent-lab-powered-projects/routedeck test_targets

sudo -u info_highpolar ln -s /home/info_highpolar/the-agent-lab-sparse/agent-lab-powered-projects/routedeck /home/info_highpolar/routedeck
```

Verify:

```bash
ls -lah /home/info_highpolar/routedeck
ls -lah /home/info_highpolar/routedeck/react
```

Create env file as shown in section 6, then create the Hostinger compose override shown in section 5.

Build and start:

```bash
cd /home/info_highpolar/saastoagent-v0.1

sudo docker compose   -f docker-compose.yml   -f docker-compose.hostinger.yml   --env-file /etc/corpus-saastoagent/corpus.env   up -d --build db backend frontend
```

Validate locally:

```bash
cd /home/info_highpolar/saastoagent-v0.1
sudo docker compose -f docker-compose.yml -f docker-compose.hostinger.yml ps
sudo ss -tulnp | grep -E ":3007|:8085"
curl -i http://127.0.0.1:8085/api/health
curl -I http://127.0.0.1:3007
```

Expected:

```text
backend/db/frontend running
127.0.0.1:8085 listening
127.0.0.1:3007 listening
/api/health returns {"status":"ok"}
frontend returns 200 OK
```

## 9. Nginx config

File:

```text
/etc/nginx/conf.d/corpus.saastoagent.com.conf
```

Reference config:

```nginx
server {
    listen 80;
    server_name corpus.saastoagent.com;

    client_max_body_size 50M;

    access_log /var/log/nginx/corpus.saastoagent.com.access.log;
    error_log  /var/log/nginx/corpus.saastoagent.com.error.log;

    location /api/ {
        proxy_pass http://127.0.0.1:8085/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location / {
        proxy_pass http://127.0.0.1:3007;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

Validate/reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

SSL:

```bash
sudo certbot --nginx -d corpus.saastoagent.com
sudo nginx -t
sudo systemctl reload nginx
```

## 10. Systemd service

File:

```text
/etc/systemd/system/corpus-saastoagent.service
```

```ini
[Unit]
Description=Corpus SaaStoAgent Docker Compose App
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/info_highpolar/saastoagent-v0.1
EnvironmentFile=/etc/corpus-saastoagent/corpus.env
ExecStart=/usr/bin/docker compose -f docker-compose.yml -f docker-compose.hostinger.yml --env-file /etc/corpus-saastoagent/corpus.env up -d db backend frontend
ExecStop=/usr/bin/docker compose -f docker-compose.yml -f docker-compose.hostinger.yml --env-file /etc/corpus-saastoagent/corpus.env stop frontend backend db
TimeoutStartSec=300
TimeoutStopSec=120

[Install]
WantedBy=multi-user.target
```

Enable/start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable corpus-saastoagent.service
sudo systemctl start corpus-saastoagent.service
sudo systemctl status corpus-saastoagent.service --no-pager -l
```

Expected status:

```text
active (exited)
```

This is normal for a `Type=oneshot` Docker Compose service.

## 11. Final validation

```bash
echo "=== Corpus containers ==="
cd /home/info_highpolar/saastoagent-v0.1
sudo docker compose -f docker-compose.yml -f docker-compose.hostinger.yml ps

echo ""
echo "=== Public checks ==="
curl -I https://corpus.saastoagent.com
curl -i https://corpus.saastoagent.com/api/health

echo ""
echo "=== Systemd service ==="
sudo systemctl status corpus-saastoagent.service --no-pager -l

echo ""
echo "=== Nginx syntax ==="
sudo nginx -t
```

Expected:

```text
frontend/backend/db running
https://corpus.saastoagent.com -> 200
/api/health -> {"status":"ok"}
corpus-saastoagent.service -> active (exited)
nginx test -> successful
```

## 12. Future update procedure

```bash
sudo -u info_highpolar git -C /home/info_highpolar/saastoagent-v0.1 pull origin main

cd /home/info_highpolar/saastoagent-v0.1

sudo docker compose   -f docker-compose.yml   -f docker-compose.hostinger.yml   --env-file /etc/corpus-saastoagent/corpus.env   up -d --build db backend frontend

curl -I https://corpus.saastoagent.com
curl -i https://corpus.saastoagent.com/api/health
```

If RouteDeck changes are needed:

```bash
sudo -u info_highpolar git -C /home/info_highpolar/the-agent-lab-sparse pull origin saastoagent

cd /home/info_highpolar/saastoagent-v0.1

sudo docker compose   -f docker-compose.yml   -f docker-compose.hostinger.yml   --env-file /etc/corpus-saastoagent/corpus.env   up -d --build backend frontend
```

## 13. Logs

```bash
cd /home/info_highpolar/saastoagent-v0.1
sudo docker compose -f docker-compose.yml -f docker-compose.hostinger.yml ps
sudo docker compose -f docker-compose.yml -f docker-compose.hostinger.yml logs --tail=120 backend
sudo docker compose -f docker-compose.yml -f docker-compose.hostinger.yml logs --tail=120 frontend
sudo journalctl -u corpus-saastoagent.service -n 100 --no-pager
sudo tail -n 100 /var/log/nginx/corpus.saastoagent.com.error.log
```

## 14. Rollback only Corpus

```bash
cd /home/info_highpolar/saastoagent-v0.1

sudo docker compose   -f docker-compose.yml   -f docker-compose.hostinger.yml   --env-file /etc/corpus-saastoagent/corpus.env   stop frontend backend db

sudo systemctl disable corpus-saastoagent.service

sudo mkdir -p /etc/nginx/conf.d.disabled
sudo mv /etc/nginx/conf.d/corpus.saastoagent.com.conf /etc/nginx/conf.d.disabled/corpus.saastoagent.com.conf.$(date +%F-%H%M)

sudo nginx -t
sudo systemctl reload nginx
```
