# Canal — atendimento-v1 (só acrescentar; nunca reescrever)

Conhecimento do projeto que a compactação perde: fatos descobertos, aprendizados, glossário, armadilhas, onde estão as coisas.
Não é estado da tarefa (isso vai em state/plan/progress). Preencha cedo — o hook avisa na faixa 1 (~50% do contexto).

Formato: `- AAAA-MM-DD HH:MM · fato|aprendizado|glossário|armadilha · texto`

- 2026-10-05 00:30 · fato · Primeira leitura integral de docs/ESPECIFICACAO.md e tests/conftest.py concluída. A fixture remove variáveis de integração herdadas; só api_int fornece servidores falsos locais.
- 2026-10-05 00:30 · armadilha · test_telefone_normalizado_e_duplicado também exige GET /api/pacientes/{id}/dados (LGPD); sua falha atual não indica erro na normalização.
- 2026-10-05 00:30 · fato · src/core.py contém domínio/SQLite; src/server.py concentra CLI/transporte/roteamento. Lock e transação externos envolvem todas as operações de cada requisição; Erro causa rollback.
- 2026-10-05 00:30 · armadilha · HTTP localhost via servidor falso é permitido para integrações; não configurar variáveis reais. Estado de presença/cancelamento ainda precisa criar retornos/disparar espera.
