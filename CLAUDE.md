# CLAUDE.md — atende-clinica

Sistema de atendimento ao paciente para clínicas: agenda, confirmação, lista de espera, retorno, FAQ, fila humana, campanhas com trava de conselho/LGPD e exportação para o Painel do Raio-X de Margem.

- Repo local (sem remoto ainda). Autor de commit: `inematds <inematds@gmail.com>` (config local).
- **Contrato:** `docs/ESPECIFICACAO.md`. Testes caixa-preta em `tests/` (pytest sobe `./atende serve --porta 0`). Contrato e testes são **protegidos** durante a execução longa — só humano altera, e aí recongela o hash no `goal.md`.
- Decisões pendentes: `docs/DECISOES-ABERTAS.md`. Relação com o Raio-X: `docs/MAPA-RAIO-X.md`.
- Execução longa: `longrun/2026-10-05-atendimento-v1/` (método em `~/projetos/execucao-longa`).
- `python3` (não existe `python` neste host). Sem dependência externa no v1.
- Nenhuma API (WhatsApp/Meta, LLM pago, Pix/PSP, OpenRouter, Groq) sem autorização explícita. Sem rede externa no código.
- Servidor de teste: só `127.0.0.1`, porta 0; matar só o PID que subiu.
- Versão em `VERSION` (semver do CLAUDE global: minor carrega o patch).

## Self-learning

When I correct you, or you catch yourself making a mistake: before continuing, add the lesson as a one-line rule under ## Lessons, so it never happens again.

## Lessons
- Ao ler o fim de vários arquivos, usar `tail -n 20`, evitando a sintaxe antiga `tail -20`.
- Confirmar nomes de arquivos com `rg --files` antes de tentar lê-los; para vários arquivos, usar sempre `tail -n N`.
