# Canal — atendimento-v1 (só acrescentar; nunca reescrever)

Conhecimento do projeto que a compactação perde: fatos descobertos, aprendizados, glossário, armadilhas, onde estão as coisas.
Não é estado da tarefa (isso vai em state/plan/progress). Preencha cedo — o hook avisa na faixa 1 (~50% do contexto).

Formato: `- AAAA-MM-DD HH:MM · fato|aprendizado|glossário|armadilha · texto`

- 2026-10-05 00:30 · fato · Primeira leitura integral de docs/ESPECIFICACAO.md e tests/conftest.py concluída. A fixture remove variáveis de integração herdadas; só api_int fornece servidores falsos locais.
- 2026-10-05 00:30 · armadilha · test_telefone_normalizado_e_duplicado também exige GET /api/pacientes/{id}/dados (LGPD); sua falha atual não indica erro na normalização.
- 2026-10-05 00:30 · fato · src/core.py contém domínio/SQLite; src/server.py concentra CLI/transporte/roteamento. Lock e transação externos envolvem todas as operações de cada requisição; Erro causa rollback.
- 2026-10-05 00:30 · armadilha · HTTP localhost via servidor falso é permitido para integrações; não configurar variáveis reais. Estado de presença/cancelamento ainda precisa criar retornos/disparar espera.
- 2026-10-05 00:33 · fato · src/conversa.py inicializa sessoes, historico, humanos, saida, espera, retornos. Inicialização chamada por server.main; futuros comandos CLI precisam inicializar essas tabelas quando criarem banco novo.
- 2026-10-05 00:33 · armadilha · Seção 18 exige silêncio enquanto humano aberto mesmo sem Telegram configurado. Emergência continua respondendo; PARAR atualiza preferência silenciosamente nesse caso.
- 2026-10-05 00:33 · fato · Confirmações verificam saída existente por agendamento; retorno UNIQUE por agendamento; oferta JSON em saida preserva horário e profissional; confirmação usa somente a última saída do telefone, sem resposta.
- 2026-10-05 00:33 · fato · Suíte demora cerca de 65s agora porque testes Telegram chegam a esperar avisos ainda não implementados; 43 passed, 50 failed. Teste local adicional de retomada da sessão e histórico passou.
