# atende-clinica

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Atende Clínica](guia/assets/banner-en.jpg)](https://inematds.github.io/atende-clinica/guia/en/)

## 📖 User guide

Full guide (landing page + step by step): **https://inematds.github.io/atende-clinica/guia/en/**

Clinic patient service built with Python 3 and its standard library: scheduling, rule-based conversation, FAQ, human queue, reminders, waitlist, recalls, campaigns, LGPD (Brazil's privacy law) and export to Raio-X. Persistent state in SQLite. Evolution and Telegram are optional and configured exclusively through the environment.

The contract is in `docs/ESPECIFICACAO.md`. The patient chat is at `/` and the front desk at `/recepcao`. At the front desk, enter the token from `clinica.json`: it is kept only in the tab's memory. Use Sair (log out) when you finish. Records, schedule, blocks, human queue, outbox, campaigns and indicators are available on the page. Use Atualizar dados (refresh data) to fetch new messages. The human reply back to the chat is sent to the phone through the configured integration; without Evolution, check the simulated outbox. The interface is in Portuguese. The built-in rules (LGPD, and the CFM, CFO and COFFITO Brazilian medical, dental and physiotherapy councils) are Brazilian.

## Run locally

```sh
mkdir -p dados
cp exemplos/clinica.json dados/clinica.json
# Edit dados/clinica.json before the first start.
./atende serve --porta 8080 --dados dados
```

Requires Python 3.10 or higher; no packages need to be installed to run. The first line prints `PORTA=8080`; `--porta 0` picks a free port. The default address is `127.0.0.1`. Health is at `GET /api/saude`. Send the token from `clinica.json` in the `X-Token` header for the front-desk routes. The examples are demonstrations: change the name, token, professionals, services, FAQ, holidays and hours before using them.

Professionals, services and FAQ in the JSON only seed the initial database; afterwards they are maintained through the record APIs. The other settings are re-read on restart. Do not use `ATENDE_AGORA` in production: it freezes the clock for tests. Dates and times use the clinic's local time; set the machine's time zone or `TZ` in the compose file.

`POST /api/tarefas/rodar` runs pending confirmations, recalls and retries. Schedule an authenticated periodic call in the operating environment: there is no built-in scheduler. The operation is idempotent. Without Evolution, messages stay in `/api/saida` with status `simulado` (simulated); send errors stay `pendente` (pending) for the next round. Campaigns require consent; opt-out prevents automatic notifications.

## Deploy on a VPS

The commands in this section are for the operator to run on the VPS. Requires Docker with Compose and a reverse proxy with HTTPS.

1. Copy the project to the VPS. Create `dados/clinica.json` following the example and set your own token before the first start.
2. Copy `.env.exemplo` to `.env`. Leave the values empty to run without integrations; protect the file with `chmod 600 .env`. No credential should enter Git.
3. Run `docker compose up -d --build`. The service uses the persistent `./dados` directory, restarts with `unless-stopped` and publishes only the VPS's local port `127.0.0.1:8080`.
4. Check `docker compose ps` and the health at `/api/saude`. Configure the HTTPS proxy to forward to the local address on port 8080, including the `/api/` and `/webhook/` routes. The proxy must preserve `X-Token` and `X-Telegram-Bot-Api-Secret-Token`. The wide bind exists only in the container command; do not publish the port directly to the Internet.

The example below is an Nginx snippet for an HTTPS server already configured with the operator's domain and certificates:

```nginx
location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 60s;
}
```

### WhatsApp / Evolution

Fill in `EVOLUTION_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCIA` and `WEBHOOK_SEGREDO`. The URL must be reachable from inside the container; localhost inside it does not point to the host. In the Evolution instance, set the webhook to the application's public HTTPS address followed by `/webhook/evolution/<secret>` and enable the `MESSAGES_UPSERT` event (payload `messages.upsert`). Use the same value as `WEBHOOK_SEGREDO` in the path. The application ignores groups, its own messages and duplicate IDs; it accepts plain text and `extendedTextMessage`.

### Telegram / team

Fill in `TELEGRAM_API_URL`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` (the authorized group) and `TELEGRAM_SEGREDO`. Add the bot to the group. Through the service configured in `TELEGRAM_API_URL`, register `POST /bot<token>/setWebhook` with a JSON body containing `url` (the public HTTPS address followed by `/webhook/telegram`) and `secret_token` (equal to `TELEGRAM_SEGREDO`). The operator does this registration; the application does not do it automatically.

The team replies to the conversation message or uses `/responder <id> <text>` (reply), `/encerrar <id>` (close), `/fila` (queue) and `/agenda [YYYY-MM-DD]` (schedule; the date format is `AAAA-MM-DD` in the command). While a human conversation is open, the bot stays silent, except in an emergency. Without Telegram, the same actions are available through the front-desk routes.

After changing `.env`, recreate the service with `docker compose up -d --force-recreate`. Set up authenticated `POST /api/tarefas/rodar` calls in your scheduler, for example every five minutes. Never store the token in public files.

### Daily backup and restore

`./atende backup` uses a SQLite snapshot and includes `clinica.json`; it can run while the server is up. The backup contains personal data and the front-desk token: keep it under restricted access with a copy outside the VPS. It does not include `.env`, which needs separate safekeeping.

```sh
mkdir -p backups
chmod 700 backups
./atende backup --dados dados --saida backups/clinica.zip
```

Example of a daily cron job on the host (adapt `/opt/atende-clinica`; Python 3 must be installed on the host):

```cron
0 3 * * * cd /opt/atende-clinica && umask 077 && ./atende backup --dados dados --saida "backups/clinica-$(date +\%F).zip"
```

To restore, stop the server before replacing the data:

```sh
docker compose stop atende
./atende restaurar --dados dados --entrada backups/clinica.zip
docker compose up -d
```

Check the health and the restored records before resuming service. Define retention and monitor disk space and cron failures.

## Export and validation

```sh
./atende raiox --dados dados --mes 2026-10 --acompanhamento acompanhamento.json
python3 -m pytest -q tests/
```

Version 1 was built by a long agent run (`longrun/2026-10-05-atendimento-v1/`): `verificar-limites.sh` was the guard for that run (the agent's file scope), and `verificar-independente.py` tests a never-seen clinic plus the `docker build`.

The export merges the month over the tracking file's previous indicators, preserving what the system does not measure. Pytest is a development-environment tool, not an application dependency. The tests use only local fake servers for Evolution and Telegram.
