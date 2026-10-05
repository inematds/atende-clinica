# atende-clinica

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Atende Clínica](guia/assets/banner-es.jpg)](https://inematds.github.io/atende-clinica/guia/es/)

## 📖 Guía de uso

Guía completa (landing + paso a paso): **https://inematds.github.io/atende-clinica/guia/es/**

Atención de una clínica con Python 3 y biblioteca estándar: agenda, conversación por reglas, preguntas frecuentes, cola humana, recordatorios, espera, retornos, campañas, LGPD (ley de privacidad de Brasil) y exportación al Raio-X. Estado persistente en SQLite. Evolution y Telegram son opcionales y se configuran exclusivamente por el entorno. Las reglas integradas (LGPD y consejos profesionales de Brasil: CFM, CFO, COFFITO) son brasileñas, y la interfaz está en portugués.

El contrato está en `docs/ESPECIFICACAO.md`. El chat del paciente está en `/` y la recepción en `/recepcao`. En la recepción, ingresa el token de `clinica.json`: queda solo en la memoria de la pestaña. Usa Sair (salir) al terminar. Registros, agenda, bloqueos, cola humana, bandeja de salida, campañas e indicadores están disponibles en la página. Usa Atualizar dados (actualizar datos) para traer mensajes nuevos. La respuesta humana al chat se envía al teléfono mediante la integración configurada; sin Evolution, consulta la bandeja de salida simulada.

## Ejecutar localmente

```sh
mkdir -p dados
cp exemplos/clinica.json dados/clinica.json
# Edita dados/clinica.json antes del primer inicio.
./atende serve --porta 8080 --dados dados
```

Requiere Python 3.10 o superior; no hace falta instalar paquetes para ejecutarlo. La primera línea informa `PORTA=8080`; `--porta 0` elige un puerto libre. La dirección predeterminada es `127.0.0.1`. El estado de salud está en `GET /api/saude`. Envía el token de `clinica.json` en el header `X-Token` para las rutas de la recepción. Los ejemplos son demostrativos: cambia nombre, token, profesionales, servicios, preguntas frecuentes, feriados y horarios antes de usarlos.

Los profesionales, servicios y preguntas frecuentes del JSON solo siembran la base inicial; después se mantienen mediante las APIs de registro. Los demás ajustes se vuelven a leer al reiniciar. No uses `ATENDE_AGORA` en producción: fija el reloj para pruebas. Las fechas y horas usan la hora local de la clínica; configura la zona horaria de la máquina o `TZ` en el compose.

`POST /api/tarefas/rodar` ejecuta las confirmaciones, retornos y reenvíos pendientes. Programa una llamada periódica autenticada en el entorno de operación: no existe un programador integrado. La operación es idempotente. Sin Evolution, los mensajes quedan en `/api/saida` con estado `simulado`; los errores de envío quedan `pendente` para la próxima ronda. Las campañas exigen consentimiento; el opt-out impide las notificaciones automáticas.

## Despliegue en la VPS

Los comandos de esta sección son para que el operador los ejecute en la VPS. Requiere Docker con Compose y un proxy inverso con HTTPS.

1. Copia el proyecto a la VPS. Crea `dados/clinica.json` según el ejemplo y configura un token propio antes del primer inicio.
2. Copia `.env.exemplo` a `.env`. Deja los valores vacíos para operar sin integraciones; protege el archivo con `chmod 600 .env`. Ninguna credencial debe entrar en Git.
3. Ejecuta `docker compose up -d --build`. El servicio usa el directorio persistente `./dados`, se reinicia con `unless-stopped` y publica solo el puerto local `127.0.0.1:8080` de la VPS.
4. Verifica `docker compose ps` y el estado de salud en `/api/saude`. Configura el proxy HTTPS para reenviar a la dirección local del puerto 8080, incluyendo las rutas `/api/` y `/webhook/`. El proxy debe preservar `X-Token` y `X-Telegram-Bot-Api-Secret-Token`. El bind amplio existe solo en el comando del contenedor; no publiques el puerto directamente en Internet.

El siguiente ejemplo es un fragmento de Nginx para un servidor HTTPS ya configurado con el dominio y los certificados del operador:

```nginx
location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 60s;
}
```

### WhatsApp / Evolution

Completa `EVOLUTION_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCIA` y `WEBHOOK_SEGREDO`. La URL debe ser accesible desde dentro del contenedor; localhost dentro de él no apunta al host. En la instancia de Evolution, configura el webhook con la dirección HTTPS pública de la aplicación seguida de `/webhook/evolution/<segredo>` y habilita el evento `MESSAGES_UPSERT` (payload `messages.upsert`). Usa en la ruta el mismo valor de `WEBHOOK_SEGREDO`. La aplicación ignora grupos, mensajes propios e IDs duplicados; acepta texto simple y `extendedTextMessage`.

### Telegram / equipo

Completa `TELEGRAM_API_URL`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` (el grupo autorizado) y `TELEGRAM_SEGREDO`. Agrega el bot al grupo. Mediante el servicio configurado en `TELEGRAM_API_URL`, registra `POST /bot<token>/setWebhook` con un cuerpo JSON que contenga `url` (dirección HTTPS pública seguida de `/webhook/telegram`) y `secret_token` (igual a `TELEGRAM_SEGREDO`). Este registro lo hace el operador; la aplicación no lo hace automáticamente.

El equipo responde al mensaje de la atención o usa `/responder <id> <texto>` (responder), `/encerrar <id>` (cerrar), `/fila` (cola) y `/agenda [AAAA-MM-DD]`. Mientras haya una atención humana abierta, el bot permanece en silencio, excepto en caso de emergencia. Sin Telegram, las mismas acciones están disponibles mediante las rutas de la recepción.

Tras modificar `.env`, recrea el servicio con `docker compose up -d --force-recreate`. Configura llamadas autenticadas a `POST /api/tarefas/rodar` desde tu programador, por ejemplo cada cinco minutos. Nunca guardes el token en archivos públicos.

### Respaldo diario y restauración

`./atende backup` usa una instantánea de SQLite e incluye `clinica.json`; puede ejecutarse con el servidor encendido. El respaldo contiene datos personales y el token de la recepción: mantenlo con acceso restringido y con una copia fuera de la VPS. No incluye `.env`, que exige un resguardo aparte.

```sh
mkdir -p backups
chmod 700 backups
./atende backup --dados dados --saida backups/clinica.zip
```

Ejemplo de cron diario en el host (adapta `/opt/atende-clinica`; Python 3 debe estar instalado en el host):

```cron
0 3 * * * cd /opt/atende-clinica && umask 077 && ./atende backup --dados dados --saida "backups/clinica-$(date +\%F).zip"
```

Para restaurar, detén el servidor antes de reemplazar los datos:

```sh
docker compose stop atende
./atende restaurar --dados dados --entrada backups/clinica.zip
docker compose up -d
```

Verifica el estado de salud y los registros restaurados antes de retomar la atención. Define la retención y monitorea el espacio y las fallas del cron.

## Exportación y validación

```sh
./atende raiox --dados dados --mes 2026-10 --acompanhamento acompanhamento.json
python3 -m pytest -q tests/
```

La v1 se construyó con una ejecución larga de agente (`longrun/2026-10-05-atendimento-v1/`): `verificar-limites.sh` fue el control de esa ejecución (alcance de archivos del agente) y `verificar-independente.py` prueba una clínica nunca vista y el `docker build`.

La exportación combina el mes sobre los indicadores anteriores del archivo de seguimiento, preservando lo que el sistema no mide. Pytest es una herramienta del entorno de desarrollo, no una dependencia de la aplicación. Las pruebas usan únicamente servidores falsos locales para Evolution y Telegram.
