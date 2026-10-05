# Estado — atualizado 2026-10-05 01:04

## Funciona
- CLI serve imprime PORTA, autenticação X-Token, SQLite persistente e catálogo semeado uma vez. Agenda transacional, cadastros, horários próprios, bloqueios e backup/restauração.
- Conversa persistente: emergência, opt-out, FAQ, fallback, agendamento, confirmação, espera FIFO e retorno. Fila humana silencia o bot exceto emergência.
- Campanhas com regras dos quatro conselhos; LGPD exporta/anonimiza preservando agregados; Raio-X HTTP/CLI calcula e mescla indicadores.
- Evolution e Telegram opcionais pelo ambiente: webhooks autenticados, deduplicação/vínculos persistentes, respostas humanas, comandos e avisos; reenvio de pendentes respeita opt-out. Todos os testes de integração passam contra servidores falsos locais.
- Dockerfile Python 3.12 slim sem dependências, HEALTHCHECK stdlib, compose com volume ./dados e porta publicada só em loopback, .env.exemplo vazio, .dockerignore por lista de inclusão e README de operação/deploy/backup. CLI agora respeita --host (padrão loopback); bind amplo apenas no comando do Dockerfile. Nenhum servidor amplo foi iniciado.
- Versão 0.6.0. Suíte: **92 passed / 1 failed**, sem errors, 32.26s (pytest-ciclo-6.log). Quatro testes Docker/documentação passaram, sem regressão observada. **LIMITES OK**, contrato intacto e 93 testes.
- Verificação adicional: passagem de --host conferida com mock (sem socket); comando real do HEALTHCHECK executado contra servidor temporário em 127.0.0.1 passou. Sem APIs reais, rede externa ou commit.

## Falta
- Páginas em web/ e rotas HTML / e /recepcao: única falha atual test_paginas (GET / retorna 404). Implementar chat e recepção funcionais, não apenas marcadores HTML.
- Ao criar web/, adicionar COPY web/ ./web/ no Dockerfile. Foi omitido neste ciclo porque o diretório ainda não existe.
- Build/container Docker e revisão visual ficam sem evidência por enquanto; build pode exigir download externo e não foi executado neste ciclo. O verificador independente é etapa humana posterior.
- Revisar bordas anteriormente anotadas: preferência de desconhecido ao limpar sessão por emergência; confirmação antiga após mudança da agenda; catálogo desativado durante fluxo.
- Risco conhecido: envios síncronos com timeout 5s sob lock/transação; queda após envio remoto e antes do commit pode duplicar entrega posterior. Sem garantia exactly-once.
- Nenhum conflito teste/spec identificado. Ainda não concluído.

## Como retomar
1. Ler goal → state → plan → canal e fins de progress/failures. Especificação inteira e conftest já lidos.
2. Implementar páginas em web/ e transporte HTML em src/server.py; APIs já disponíveis. Usar skill de interface aplicável, respeitando escopo PT e páginas de aplicação (não landing).
3. Atualizar Dockerfile para copiar páginas e README para retirar aviso de páginas pendentes; validar fluxos locais e HTML.
4. Rodar pytest inteiro para arquivo e ler tail -n 30; rodar verificar-limites.sh; registrar resultados. Só marcar concluído se ambos passarem. Não alterar contrato/testes/verificadores, não fazer commit.
