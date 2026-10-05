# Estado — atualizado 2026-10-05 00:30

## Funciona
- `./atende serve --porta 0 --dados DIR`: primeira linha PORTA, bind em 127.0.0.1, configuração copiada do exemplo quando ausente, saúde com VERSION e autenticação X-Token.
- SQLite em DIR/estado.sqlite3; profissionais/serviços/FAQ semeados uma única vez, configuração operacional relida no início.
- Agenda: grade, duração, antecedência, feriados, seleção automática de profissional, conflitos, concorrência (um vencedor), listagem por data/período, cancelamento, remarcação e status de presença.
- Paciente: criação, normalização e deduplicação de telefone. Reinício conserva pacientes, agenda e ocupação.
- Suíte completa observada: **20 passed / 73 failed**, sem errors, em 20.98s. Log: `pytest-ciclo-1.log` nesta pasta.
- Verificador: **LIMITES OK**, contrato intacto e 93 testes coletados.

## Falta
- Conversa inteira, fila humana e histórico de mensagens persistido.
- Lembretes, espera e retorno (cancelamento/presença atuais só alteram o status; ainda faltam seus efeitos nessas filas).
- Campanhas, LGPD (inclusive GET dos dados do paciente, necessário ao teste de telefone) e Raio-X HTTP/CLI.
- CRUD dos cadastros, bloqueios, backup/restauração. Horários personalizados já são considerados pelo motor, mas ainda não editáveis por API.
- Evolution/Telegram, Docker/README e páginas em web/.
- Rotas não implementadas devolvem 404; nenhum stub simula sucesso. Teste de rotas públicas ainda falha em /api/mensagens; teste de páginas ainda falha.
- Nenhum conflito teste/spec identificado neste ciclo. Restrição de bind local prevalece durante o loop; requisito Docker deve ser conciliado no ciclo da entrega sem abrir listener externo.

## Como retomar
1. Ler goal.md → state.md → plan.md → canal.md → fins de progress.md/failures.md. Especificação inteira e tests/conftest.py já lidos no primeiro ciclo.
2. Ler `src/core.py`, `src/server.py`, `tests/test_conversa.py` e testes de lembretes para desenhar histórico/pendências sem refazer a agenda.
3. Implementar conversa e persistência de estado por telefone, seguindo a ordem do contrato. Usar a mesma transação/lock nas chamadas internas.
4. Executar `python3 -m pytest -q tests/ > longrun/2026-10-05-atendimento-v1/pytest-ciclo-2.log 2>&1` e `tail -30 longrun/2026-10-05-atendimento-v1/pytest-ciclo-2.log`.
5. Executar `bash longrun/2026-10-05-atendimento-v1/verificar-limites.sh`, atualizar registros. Não fazer commit.
