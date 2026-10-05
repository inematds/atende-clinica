# atende-clinica

Atendimento de uma clínica com Python 3 e biblioteca padrão: agenda, conversa por regras, FAQ, fila humana, lembretes, espera, retornos, campanhas, LGPD e exportação para o Raio-X. Estado persistente em SQLite. Evolution e Telegram são opcionais, configurados exclusivamente pelo ambiente.

O contrato está em `docs/ESPECIFICACAO.md`. O chat do paciente está em `/` e a recepção em `/recepcao`. Na recepção, informe o token de `clinica.json`: ele fica apenas na memória da aba. Use Sair ao finalizar. Cadastros, agenda, bloqueios, fila humana, caixa de saída, campanhas e indicadores estão disponíveis na página. Use Atualizar dados para buscar novas mensagens. O retorno humano ao chat é enviado ao telefone pela integração configurada; sem Evolution, consulte a caixa de saída simulada.

## Executar localmente

```sh
mkdir -p dados
cp exemplos/clinica.json dados/clinica.json
# Edite dados/clinica.json antes do primeiro início.
./atende serve --porta 8080 --dados dados
```

Requer Python 3.10 ou superior; não precisa instalar pacotes para executar. A primeira linha informa `PORTA=8080`; `--porta 0` escolhe uma porta livre. O endereço padrão é `127.0.0.1`. A saúde está em `GET /api/saude`. Envie o token de `clinica.json` no header `X-Token` para as rotas da recepção. Os exemplos são demonstrativos: troque nome, token, profissionais, serviços, FAQ, feriados e horários antes de usar.

Profissionais, serviços e FAQ do JSON apenas semeiam o banco inicial; depois são mantidos pelas APIs de cadastro. As demais configurações são relidas ao reiniciar. Não use `ATENDE_AGORA` em produção: ela fixa o relógio para testes. Datas e horas usam o horário local da clínica; configure o fuso da máquina ou `TZ` no compose.

`POST /api/tarefas/rodar` executa confirmações, retornos e reenvios pendentes. Agende uma chamada periódica autenticada no ambiente de operação: não existe agendador embutido. A operação é idempotente. Sem Evolution, as mensagens ficam em `/api/saida` com status `simulado`; erros de envio ficam `pendente` para a próxima rodada. Campanhas exigem consentimento; opt-out impede notificações automáticas.

## Deploy na VPS

Os comandos desta seção são para o operador executar na VPS. Requer Docker com Compose e um proxy reverso com HTTPS. Não foi realizado deploy nem build com download de imagem nesta execução local.

1. Copie o projeto para a VPS. Crie `dados/clinica.json` conforme o exemplo e configure um token próprio antes do primeiro início.
2. Copie `.env.exemplo` para `.env`. Deixe os valores vazios para operar sem integrações; proteja o arquivo com `chmod 600 .env`. Nenhuma credencial deve entrar no Git.
3. Execute `docker compose up -d --build`. O serviço usa o diretório persistente `./dados`, reinicia com `unless-stopped` e publica apenas a porta local `127.0.0.1:8080` da VPS.
4. Verifique `docker compose ps` e a saúde em `/api/saude`. Configure o proxy HTTPS para encaminhar ao endereço local da porta 8080, incluindo as rotas `/api/` e `/webhook/`. O proxy deve preservar `X-Token` e `X-Telegram-Bot-Api-Secret-Token`. O bind amplo existe somente no comando do container; não publique a porta diretamente na Internet.

O exemplo abaixo é um trecho de Nginx para um servidor HTTPS já configurado com domínio e certificados do operador:

```nginx
location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 60s;
}
```

### WhatsApp / Evolution

Preencha `EVOLUTION_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCIA` e `WEBHOOK_SEGREDO`. A URL precisa ser acessível de dentro do container; localhost dentro dele não aponta para o host. Na instância Evolution, configure o webhook para o endereço HTTPS público da aplicação seguido de `/webhook/evolution/<segredo>` e habilite o evento `MESSAGES_UPSERT` (payload `messages.upsert`). Use no caminho o mesmo valor de `WEBHOOK_SEGREDO`. O aplicativo ignora grupos, mensagens próprias e IDs duplicados; aceita texto simples e `extendedTextMessage`.

### Telegram / equipe

Preencha `TELEGRAM_API_URL`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` (o grupo autorizado) e `TELEGRAM_SEGREDO`. Adicione o bot ao grupo. Pelo serviço configurado em `TELEGRAM_API_URL`, registre `POST /bot<token>/setWebhook` com um corpo JSON contendo `url` (endereço HTTPS público seguido de `/webhook/telegram`) e `secret_token` (igual a `TELEGRAM_SEGREDO`). Esse registro é feito pelo operador; o aplicativo não o faz automaticamente.

A equipe responde à mensagem do atendimento ou usa `/responder <id> <texto>`, `/encerrar <id>`, `/fila` e `/agenda [AAAA-MM-DD]`. Enquanto houver atendimento humano aberto, o bot fica em silêncio, exceto em emergência. Sem Telegram, as mesmas ações estão disponíveis pelas rotas da recepção.

Após alterar `.env`, recrie o serviço com `docker compose up -d --force-recreate`. Configure chamadas autenticadas de `POST /api/tarefas/rodar` pelo seu agendador, por exemplo a cada cinco minutos. Nunca guarde o token em arquivos públicos.

### Backup diário e restauração

`./atende backup` usa snapshot SQLite e inclui `clinica.json`; pode rodar com o servidor ligado. O backup contém dados pessoais e o token da recepção: mantenha-o com acesso restrito e cópia fora da VPS. Não inclui `.env`, que exige guarda separada.

```sh
mkdir -p backups
chmod 700 backups
./atende backup --dados dados --saida backups/clinica.zip
```

Exemplo de cron diário no host (adapte `/opt/atende-clinica`; Python 3 deve estar instalado no host):

```cron
0 3 * * * cd /opt/atende-clinica && umask 077 && ./atende backup --dados dados --saida "backups/clinica-$(date +\%F).zip"
```

Para restaurar, pare o servidor antes de substituir os dados:

```sh
docker compose stop atende
./atende restaurar --dados dados --entrada backups/clinica.zip
docker compose up -d
```

Confira a saúde e os registros restaurados antes de retomar o atendimento. Defina retenção e monitore espaço e falhas do cron.

## Exportação e validação

```sh
./atende raiox --dados dados --mes 2026-10 --acompanhamento acompanhamento.json
python3 -m pytest -q tests/
bash longrun/2026-10-05-atendimento-v1/verificar-limites.sh
```

A exportação mescla o mês sobre os indicadores anteriores do arquivo de acompanhamento, preservando o que o sistema não mede. Pytest é ferramenta do ambiente de desenvolvimento, não dependência da aplicação. Os testes usam somente servidores falsos locais para Evolution e Telegram.
