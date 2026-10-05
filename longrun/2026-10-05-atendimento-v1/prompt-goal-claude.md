Rode numa sessão NOVA do Claude Code aberta em ~/projetos/atende-clinica (o /goal não roda de dentro de outra sessão de agente).

1) Cole como condição:

/goal A saída do terminal mostra `python3 -m pytest -q tests/` com "93 passed" e nenhuma falha/erro, seguida de `bash longrun/2026-10-05-atendimento-v1/verificar-limites.sh` imprimindo "LIMITES OK", e longrun/2026-10-05-atendimento-v1/state.md diz "concluído".

(O avaliador do Claude só enxerga a conversa: os dois comandos precisam aparecer executados e impressos no fim.)

2) Depois cole como primeira mensagem o bloco de prompt-goal-codex.md a partir de "RESULTADO:".
