# Estado — atualizado 2026-10-05 00:33

## Funciona
- Base: CLI serve com PORTA, bind 127.0.0.1, auth X-Token, SQLite, configuração e catálogo semeado uma vez; agenda transacional e persistente, normalização e cadastro de pacientes.
- Conversa em src/conversa.py: emergência, opt-out, encaminhamento humano, FAQ por percentual, fallback consecutivo e fluxo de agendamento (nome, serviço, 3 horários), opções inválidas e cancelamento. Sessões e histórico persistem; cadastro pelo chat associa o histórico anterior ao paciente.
- Atendimento aberto silencia o bot, exceto emergência; emergência eleva prioridade. Fila GET já inclui id/status/nome, mas responder/encerrar e Telegram ainda faltam.
- Confirmação idempotente e respostas, oferta FIFO de espera disparada por cancelamento API/chat, aceite com nova validação de disponibilidade; retornos criados na presença e avisados uma vez. Saída simulada e GET dos dados do paciente funcionam.
- Versão 0.2.0. Suíte inteira: **43 passed / 50 failed**, sem errors, em 64.77s; log pytest-ciclo-2.log. Ganho de 23 testes sobre o ciclo anterior; todos os testes de conversa e lembretes passaram.
- Verificação local adicional: sessão retomada após fechar/reabrir SQLite, histórico anterior ao cadastro associado, silêncio humano e emergência prioritária passaram.
- Verificador: **LIMITES OK**, 93 testes e contrato intacto.

## Falta
- Campanhas com trava por conselho e consentimento; LGPD DELETE/anonimização; Raio-X HTTP/CLI.
- CRUD de pacientes/profissionais/serviços/FAQ, bloqueios, backup/restauração.
- Evolution e Telegram, inclusive respostas humanas/encerramento, notificações e reenvio de pendentes. Nenhuma chamada de rede de integração foi implementada neste ciclo.
- Docker, compose, .env.exemplo, README e páginas web.
- Rever casos de borda: opt-out de desconhecido cadastrado depois pela API (preferência atualmente em sessão); resposta a confirmação de agendamento alterado após envio; reinício de fluxo com opções antigas de catálogo.
- Nenhum conflito teste/spec identificado neste ciclo. Restrição de bind local prevalece durante o loop; conciliar Docker ao implementar entrega.

## Como retomar
1. Ler goal → state → plan → canal e fins de progress/failures. Especificação inteira e conftest lidos neste ciclo.
2. Ler src/core.py, src/conversa.py e src/server.py. conversa.iniciar cria novas tabelas após Clinica; operações HTTP continuam sob lock/transação únicos.
3. Implementar campanhas e LGPD DELETE; em seguida Raio-X. Consultar tests/test_campanhas.py e tests/test_lgpd_raiox.py sem alterá-los.
4. Rodar suíte completa, ler só tail -n 30 do log, executar verificar-limites.sh e atualizar registros. Não fazer commit.
