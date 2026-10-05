# Decisões — respondidas em 05/10/2026

**Resposta do Nei (05/10):** "pode rodar" + WhatsApp pela Evolution, tudo em Docker numa VPS, atendimento interno pelo Telegram, gestão de agenda e de banco de dados, cadastro de paciente, médico etc. Aplicado na spec (seções 14–19) e nos testes (93). Demais itens: valem as propostas padrão abaixo. Chamadas reais à Evolution/Telegram e o deploy na VPS ficam com o Nei (credenciais dele); na execução só servidores falsos locais.

## Propostas originais

Cada item tem uma **proposta padrão**. Responder "ok em tudo" já destrava a execução. Se mudar algo que afete o contrato (marcado ⚠), eu ajusto `docs/ESPECIFICACAO.md` e os testes **antes** de congelar o hash.

| # | Decisão | Proposta padrão | Por quê |
|---|---|---|---|
| 1 | Nome do projeto / repo | `atende-clinica` (pasta e futuro repo `inematds/atende-clinica`) | regra: repo = nome da pasta |
| 2 ⚠ | Linguagem | **Python 3, só biblioteca padrão** (`http.server` + `sqlite3`) | zero dependência, roda em qualquer máquina, igual ao piloto do `recall`. Os testes são caixa-preta (HTTP/CLI), então trocar para Node/FastAPI não invalida os testes — mas aí eu ajusto `verificar-limites.sh`, `goal.md` e `prompt.md` antes de congelar |
| 3 | Canal v1 | ~~chat web + simulado~~ → **chat web + WhatsApp pela Evolution API** (simulado quando não configurado); equipe pelo **Telegram** | resposta de 05/10 |
| 4 ⚠ | "Tirar dúvidas" | **FAQ da clínica por palavras-chave**, sem IA | determinístico = testável; bot de saúde não pode inventar resposta. LLM (Ollama local ou Claude/Codex pela assinatura) entra na fase 2 atrás de uma opção desligada |
| 5 | Uma clínica ou várias | **uma clínica por instalação** (`--dados DIR`; um container por clínica na VPS) | multi-clínica (SaaS) é outra ordem de complexidade; dá para rodar várias instâncias |
| 6 ⚠ | Conselho do piloto | exemplo/fixture = **odonto (CFO)**; os 4 perfis (CFM, CFO, COFFITO, estética) já estão no contrato | o Raio-X mostra que odonto tem as regras mais duras de publicidade |
| 7 | Idioma | **só PT no v1** | EN/ES depois, pelo processo trilíngue já testado (relatórios do WiFi) |
| 8 | Quem executa | **headless: `loop-longrun.sh` com Codex `gpt-6-astra`** (rota testada no piloto). Alternativa: colar o `/goal` no Codex TUI ou no Claude Code | o loop confere hash dos testes e para por estagnação sozinho. **Conferido em 05/10:** o sandbox `workspace-write` do Codex bloqueia até socket em 127.0.0.1; o `loop.env` já leva `CODEX_ARGS="-c sandbox_workspace_write.network_access=true"` (testado: servidor local responde 200). No TUI: `codex -c sandbox_workspace_write.network_access=true` |
| 9 | Tetos | 15 ciclos × 30 min, 8 GB por ciclo, parar após 3 ciclos sem avanço | ~7,5 h no pior caso; o piloto fechou em 1 ciclo com spec deste nível |
| 10 | GitHub / VPS | **não criar agora**; deploy na VPS pelo Nei com o README; repo local. Criar `inematds/atende-clinica` + guia só depois do v1 aprovado | criar repo é ação externa → você confirma |
| 11 ⚠ | Regras do bot | emergência → SAMU 192 + fila humana alta; "PARAR" bloqueia todo contato; 2 "não entendi" seguidos → humano | conferir se a lista de palavras de emergência (seção 6) está boa para a clínica-alvo |
| 12 ⚠ | Sinal por Pix / plano | **fora do v1** (só a política escrita) | precisa de PSP/API de pagamento = portão humano |

## Perguntas que só você responde

- Isto é **produto para vender/implantar em clínicas** (via kit do Raio-X) ou **projeto aberto/curso**? Muda o que vem depois do v1 (guia, licença, deploy), não o v1.
- Tem uma **clínica real** para o piloto (horários, serviços, FAQ verdadeiros)? Se sim, eu troco o `exemplos/clinica.json`.
- Quer que o **painel da recepção** seja só funcional (padrão) ou já com o visual INEMA?
