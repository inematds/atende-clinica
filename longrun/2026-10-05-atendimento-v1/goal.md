# Goal — atendimento-v1

- **Início:** 2026-10-05 00:27 · **Agente:** `codex exec` (gpt-6-astra, assinatura) em loop headless — `tools/loop-longrun.sh` · alternativa: `/goal` no Codex TUI ou no Claude Code
- **Tetos:** 20 ciclos × 30 min (≤ 10 h) · memória 8G por ciclo · estagnação 3 ciclos

## Resultado
`./atende` sobe um sistema de atendimento ao paciente para uma clínica — agenda, confirmação, lista de espera, retorno, FAQ, fila humana, emergência, campanhas com trava de conselho/LGPD, cadastros (pacientes, profissionais, serviços, FAQ), gestão de agenda (horário por profissional, bloqueios), backup do banco, WhatsApp pela Evolution API, atendimento interno pelo Telegram, exportação para o Painel do Raio-X e entrega em Docker para VPS —, conforme `docs/ESPECIFICACAO.md`.

## Especificação
**`docs/ESPECIFICACAO.md`** (contrato completo, congelado). Contexto: `docs/MAPA-RAIO-X.md`. Fora do escopo: seção 12 da especificação.

## Critérios de pronto (verificáveis)

**Função**
- [ ] `python3 -m pytest -q tests/` → **93 passed**, 0 failed, 0 errors, 0 skipped

**Regressão**
- [ ] a mesma suíte inteira no teste final (o loop só fecha se todas passam juntas; teste que passava e voltou a falhar impede o fecho)
- [ ] `./atende serve` reiniciado com o mesmo `--dados` mantém o estado (coberto por `test_estado_persiste_ao_reiniciar` e `test_confirmacao_sobrevive_a_reinicio`)

**Limite**
- [ ] `bash longrun/2026-10-05-atendimento-v1/verificar-limites.sh` → `LIMITES OK` (hash do contrato = `hash-congelado.txt`, nº de testes coletados igual, só arquivos do escopo — `atende`, `src/`, `web/`, `exemplos/`, `README.md`, `VERSION`, `Dockerfile`, `docker-compose.yml`, `.env.exemplo`, `.dockerignore`, `.gitignore`, `CLAUDE.md`, `FALHAS.md`, esta pasta —, sem SDK/dependência externa, sem URL externa, sem chave de API, sem `0.0.0.0`)

**Teste rápido por ciclo**: `python3 -m pytest -q tests/`
**Teste completo no final**: `python3 -m pytest -q tests/ && bash longrun/2026-10-05-atendimento-v1/verificar-limites.sh`

**Depois do "concluído" (humano, nível 4):** `python3 longrun/2026-10-05-atendimento-v1/verificar-independente.py` → `INDEPENDENTE OK` (sem valores do fixture no código + clínica nunca vista + `docker build` e healthcheck do container) e abrir `/` e `/recepcao` no navegador.

## Restrições
- só pela assinatura; nenhuma API, nenhuma rede externa, nenhuma dependência fora da biblioteca padrão do Python (decisão 2 de `docs/DECISOES-ABERTAS.md`)
- não mexer em: `tests/`, `pytest.ini`, `docs/` (inclusive `ESPECIFICACAO.md`), `goal.md`, `hash-congelado.txt`, `congelar.sh`, `verificar-*.{sh,py}`
- servidor só em `127.0.0.1`; ao testar à mão, porta 0 e matar só o PID que subiu
- no loop headless não fazer commit (o loop faz); no /goal interativo, commit local a cada checkpoint; nunca criar repo remoto nem fazer push

## Portões humanos (parar e perguntar)
- teste que contradiz a especificação (registrar em `failures.md` com o trecho exato e parar — não "ajustar" o teste)
- qualquer chamada a API real (Evolution, Telegram, LLM, Pix) — durante a execução só os servidores falsos locais dos testes; dependência externa
- deploy na VPS (é do humano, com as credenciais dele)
- mudança de contrato, criar repo, push, publicar
