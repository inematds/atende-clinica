# Estado — atualizado 2026-10-05 01:00

## Funciona
- CLI serve imprime PORTA, bind 127.0.0.1, autenticação X-Token, SQLite persistente e catálogo semeado uma vez. Agenda transacional, cadastros completos, horários próprios, bloqueios e backup/restauração consistentes.
- Conversa persistente: emergência, opt-out, FAQ, fallback, agendamento, confirmação, lista de espera FIFO e retorno; fila humana silencia o bot exceto emergência.
- Campanhas com regras dos quatro conselhos, consentimento/opt-out; LGPD exporta e anonimiza preservando agregados; Raio-X HTTP/CLI calcula e mescla indicadores.
- Evolution em src/integracoes.py: webhook com segredo, filtros, deduplicação SQLite, conversation/extendedTextMessage, resposta para mídia e conversa compartilhada. Saída síncrona com status enviado/pendente/simulado; tarefas reenvia pendentes anteriores sem furar opt-out.
- Telegram: abertura com nome/telefone/motivo/ALTA, repasse vinculado, resposta à mensagem original ou repassada, comandos responder/encerrar/fila/agenda, avisos de agendamento/cancelamento pelo chat. Recepção responde/encerra pela API inclusive sem Telegram. Vínculos message_id persistidos.
- Versão 0.5.0. Suíte completa: **88 passed / 5 failed**, sem errors, em 32.00s; pytest-ciclo-5.log. Ganho de 15 testes, nenhuma regressão observada. Todos os testes de integração passam.
- **LIMITES OK**, 93 testes e contrato intacto. Verificação local adicional passou: extendedTextMessage, deduplicação após reinício e opt-out impedindo reenvio persistente. Só servidores falsos locais; nenhuma integração real ou commit.

## Falta
- Dockerfile, docker-compose.yml, .env.exemplo, README com Deploy na VPS e páginas web (5 falhas atuais).
- Resolver entrega Docker respeitando restrição de bind durante a execução: server.py atualmente rejeita qualquer host diferente de 127.0.0.1; contrato descreve bind amplo no container. Não alterar contrato/verificadores.
- Revisar bordas previamente anotadas: preferências de desconhecido ao limpar sessão por emergência; confirmação antiga após mudança da agenda; catálogo desativado durante um fluxo.
- Risco de entrega: HTTP externo síncrono tem timeout de 5s e ocorre sob lock/transação. Falha de processo após envio remoto e antes do commit pode duplicar uma entrega no próximo reenvio; não há garantia exactly-once do provedor.
- Nenhum conflito teste/spec identificado neste ciclo. Ainda não concluído.

## Como retomar
1. Ler goal → state → plan → canal e fins de progress/failures. Especificação inteira e conftest lidos.
2. Ler tests/test_docker.py, tests/test_basico.py e src/server.py; implementar próxima entrega Docker/README e depois páginas usando APIs já disponíveis.
3. src/integracoes.py concentra transporte opcional e humano; conversa.iniciar inicializa também tabelas das integrações. Webhooks usam segredos próprios, antes do X-Token.
4. Rodar pytest inteiro para arquivo, ler tail -n 30, verificar-limites.sh e atualizar registros. Não fazer commit nem marcar concluído antes de ambos os portões passarem.
