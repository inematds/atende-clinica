# atende-clinica

Atendimento ao paciente para clínicas (consultório, odonto, fisio, estética): **agenda online, confirmação automática, lista de espera, retorno programado, tirar dúvidas (FAQ), passagem para humano, alerta de emergência, campanhas com trava de conselho e LGPD**, e exportação mensal para o **Painel de Recuperação do [Raio-X de Margem](../raio-x-margem)**.

> Estado: **planejado, não implementado.** Contrato em [`docs/ESPECIFICACAO.md`](docs/ESPECIFICACAO.md) + 62 testes de aceitação em `tests/`. A implementação sai de uma execução longa (`/goal`) — ver abaixo.

## Documentos

| Arquivo | O que é |
|---|---|
| [`docs/ESPECIFICACAO.md`](docs/ESPECIFICACAO.md) | contrato v1 (API, conversa, regras de agenda, trava de conselho, LGPD, Raio-X, fora do v1) |
| [`docs/DECISOES-ABERTAS.md`](docs/DECISOES-ABERTAS.md) | **responder antes de rodar** — cada item tem proposta padrão |
| [`docs/MAPA-RAIO-X.md`](docs/MAPA-RAIO-X.md) | vazamentos da clínica no Raio-X × peça do sistema |
| [`longrun/2026-10-05-atendimento-v1/`](longrun/2026-10-05-atendimento-v1/) | goal (nível 3 + verificação independente nível 4), prompts, loop, scripts de trava |

## Como rodar a execução longa

```bash
cd ~/projetos/atende-clinica
L=longrun/2026-10-05-atendimento-v1

# 0. decisões respondidas (docs/DECISOES-ABERTAS.md) e tudo commitado
# 1. congelar o contrato (grava hash dos testes + spec e o commit-base)
bash $L/congelar.sh

# 2a. headless (recomendado; Codex pela assinatura, 15 ciclos × 30 min, para sozinho)
~/projetos/execucao-longa/tools/loop-longrun.sh $L          # acompanhar: tail -f $L/loop.log

# 2b. ou interativo: colar $L/prompt-goal-codex.md no Codex TUI,
#     ou seguir $L/prompt-goal-claude.md numa sessão nova do Claude Code

# 3. quando state.md disser "concluído": verificação independente
python3 $L/verificar-independente.py        # → INDEPENDENTE OK
./atende serve --porta 8811 --dados /tmp/atende-demo   # abrir http://127.0.0.1:8811/ e /recepcao
```

Saídas do loop: `0` concluído · `1` teto de ciclos · `2` estagnação (ver `failures.md`) · `3` outro loop já roda.

## Restrições

Python 3 só biblioteca padrão, sem rede externa, sem API (WhatsApp/Meta, LLM pago, Pix/PSP) sem autorização explícita. Canal v1 = chat web + caixa de saída simulada.
