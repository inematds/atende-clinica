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
- 2026-10-05 00:39 · fato · src/gestao.py centraliza campanhas, remover_paciente, raiox e exportar. A CLI raiox inicializa as tabelas de conversa antes de consultar indicadores.
- 2026-10-05 00:39 · armadilha · Campanha normaliza acentos/caixa mas preserva pontuação; normalizar() da conversa remove r$ e 100%, portanto não serve para campanhas.
- 2026-10-05 00:39 · fato · Raio-X calcula minutos disponíveis de todas as janelas de todos os profissionais menos feriados, conforme seção 10; não subtrai bloqueios nem aplica antecedência do relógio. Novos = primeiro realizado global; retorno usa faixa inclusiva de ±30 dias.
- 2026-10-05 00:39 · fato · Suíte agora 63 passed / 30 failed (66.26s), +20 testes; somente cadastros/bloqueios/backup, integrações, Docker e páginas ainda falham. Verificação local adicional de anonimização e mesclagem passou; LIMITES OK.
- 2026-10-05 00:52 · fato · src/cadastros.py implementa CRUD/busca/bloqueios; src/backup.py usa ZIP com estado.sqlite3 e clinica.json. Backup não instancia Clinica nem ressemeia o banco; abre origem SQLite em modo somente leitura.
- 2026-10-05 00:52 · armadilha · Bloqueios devem sair de candidatos, não apenas livre: reserva bloqueada é inválida (422), enquanto sobreposição com consulta válida é ocupada (409). Intervalos usam inicio < fim_consulta e fim > inicio_consulta.
- 2026-10-05 00:52 · fato · Suíte 73 passed / 20 failed (65.80s), +10 testes; faltam integrações, páginas e Docker/README. LIMITES OK; teste local de backup validou também configuração/FAQ/bloqueio e arquivo inválido.
- 2026-10-05 01:00 · fato · src/integracoes.py usa somente URLs do ambiente. autorizar valida segredos dos webhooks antes de X-Token; rotas humano continuam protegidas pela recepção. Sem variáveis não há chamada de rede. Todos os 16 testes de integração passam.
- 2026-10-05 01:00 · armadilha · Reenviar somente pendentes já existentes antes de criar novas notificações: o teste espera primeiro status pendente e reenvio na rodada seguinte. Opt-out bloqueia também tentativas pendentes.
- 2026-10-05 01:00 · fato · Telegram persiste vínculos de abertura e repasses; humano desconhecido entra na saída com paciente_id NULL, histórico associa depois pelo cadastro. Mensagens humanas explícitas são diferentes das notificações automáticas bloqueadas por opt-out.
- 2026-10-05 01:00 · fato · Suíte 88 passed / 5 failed (32.00s); LIMITES OK. Pendências: páginas e 4 testes Docker/README. Script local adicional confirmou extendedText, deduplicação após reinício e supressão de reenvio após PARAR.
- 2026-10-05 01:04 · fato · Suíte 92 passed / 1 failed (test_paginas, GET / 404). LIMITES OK. Testes Docker são estáticos; healthcheck também foi executado localmente, mas build não realizado.
- 2026-10-05 01:04 · armadilha · Dockerfile ainda não copia web/ porque diretório não existe; adicionar COPY quando implementar páginas. README declara essa pendência e deve ser atualizado. O verificador permite endereço amplo no Dockerfile, mas não em atende/src/web.
- 2026-10-05 01:13 · fato · Critérios automáticos alcançados: 93 passed em 25.46s e LIMITES OK. VERSION 0.7.0. Páginas em web/, rotas HTML/assets por whitelist em server.Handler, COPY web no Dockerfile.
- 2026-10-05 01:13 · armadilha · Campo nascimento vazio em formulário deve virar null antes de POST/PUT: validar_paciente interpreta string vazia como data inválida. Corrigido e validado por cadastro em Chromium.
- 2026-10-05 01:13 · fato · Navegador Chromium instalado em ~/.cache/ms-playwright/chromium-1234/chrome-linux/chrome; verificação via CDP local exercitou login, cadastro, logout e chat. Capturas desktop/mobile na pasta longrun. Não houve instalação, API externa ou build Docker.
