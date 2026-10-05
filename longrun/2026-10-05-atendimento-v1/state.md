# Estado — atualizado 2026-10-05 00:39

## Funciona
- CLI serve com PORTA, bind 127.0.0.1, auth X-Token, SQLite persistente, configuração e catálogo semeado uma vez; agenda transacional, normalização e cadastro de pacientes.
- Conversa persistente: emergência, opt-out, FAQ, fallback, fila humana, fluxo de agendamento, confirmação, espera FIFO e retorno. Atendimento aberto silencia o bot, exceto emergência.
- Campanhas em src/gestao.py: regras dos quatro conselhos, lista completa de violações antes de enviar, consentimento e opt-out. Os 17 testes de campanhas passaram.
- LGPD: GET com histórico; DELETE anonimiza paciente/histórico/saída, limpa sessão e fila humana, desativa contato, cancela agendados/confirmados e conserva realizados/faltas e agregados. Telefone antigo volta a ser desconhecido.
- Raio-X HTTP e CLI: indicadores mensais calculados do banco/calendário, mesclagem sobre mês anterior/base, preservação de campos não medidos, substituição idempotente e gravação atômica do JSON.
- Cadastro pela API agora associa histórico anterior e respeita opt-out anterior ao cadastro. HTTP 204 sem corpo.
- Versão 0.3.0. Suíte completa: **63 passed / 30 failed**, sem errors, em 66.26s; pytest-ciclo-3.log. Ganho de 20 testes; nenhuma regressão observada.
- Verificação local adicional passou: opt-out antes de cadastro API; anonimização da saída, histórico, sessão e fila humana; Raio-X mescla mês anterior, ignora futuro, conserva campos e não duplica mês.
- Verificador: **LIMITES OK**, 93 testes e contrato intacto.

## Falta
- CRUD de pacientes/profissionais/serviços/FAQ, bloqueios, backup/restauração (listagem de agenda por período e horários próprios já têm base implementada).
- Evolution e Telegram: webhooks, envio/reenvio, responder/encerrar pela recepção, notificações à equipe. Ainda nenhuma chamada de integração implementada.
- Docker, compose, .env.exemplo, README e páginas web.
- Revisar bordas da conversa: preferências de desconhecido ao limpar sessão por emergência; respostas a confirmações depois de alteração do agendamento; opções antigas de catálogo durante um fluxo.
- Nenhum conflito teste/spec identificado neste ciclo. Restrição de bind local prevalece durante o loop; conciliar Docker ao implementar entrega.

## Como retomar
1. Ler goal → state → plan → canal e fins de progress/failures. Especificação inteira e conftest foram lidos neste ciclo.
2. Ler src/core.py, src/server.py, src/conversa.py e src/gestao.py. HTTP envolve operações em lock/transação; conversa.iniciar cria tabelas adicionais e já é chamado em serve e raiox.
3. Implementar cadastros, bloqueios e backup/restauração consultando tests/test_cadastros.py sem alterar testes. Depois integrações exclusivamente com falsos locais.
4. Rodar suíte inteira para arquivo, ler só tail -n 30, executar verificar-limites.sh e atualizar registros. Não fazer commit. Só marcar concluído quando os dois portões passarem.
