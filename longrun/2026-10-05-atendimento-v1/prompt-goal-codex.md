/goal
RESULTADO: `./atende` (Python 3, só biblioteca padrão; `src/` + `web/`) implementa docs/ESPECIFICACAO.md por inteiro — atendimento ao paciente para clínica com WhatsApp (Evolution), equipe no Telegram, cadastros, gestão de agenda, backup e Docker.

VERIFICAÇÃO (só termina quando todos passarem, mostrando a saída):
- `python3 -m pytest -q tests/` → 93 passed, 0 failed, 0 errors
- `bash longrun/2026-10-05-atendimento-v1/verificar-limites.sh` → LIMITES OK

RESTRIÇÕES: não altere tests/, pytest.ini, docs/, goal.md, hash-congelado.txt, congelar.sh, verificar-*. Só biblioteca padrão; nenhuma API, rede externa ou chave; servidor só em 127.0.0.1; matar só o PID que subiu (nunca `pkill -f`). Uso só pela assinatura. Commit local a cada checkpoint com autor inematds; sem push, sem repo remoto.

ESTADO: use longrun/2026-10-05-atendimento-v1/ (goal.md, plan.md, state.md, progress.md, failures.md, decisions.md, canal.md).
Após qualquer compactação ou retomada, releia goal.md, state.md, plan.md e canal.md antes de agir. Registre no canal.md (só acrescentar) fatos, aprendizados, glossário e armadilhas assim que surgirem.

CICLO: analisar → escolher a próxima ação útil → executar → testar → observar → corrigir → atualizar state/progress → commit no checkpoint → continuar.
Ordem sugerida: base (serve/PORTA/SQLite/auth) → agenda → conversa → lembretes/espera/retorno → campanhas → LGPD → raiox → cadastros/bloqueios/backup → Evolution → Telegram → Docker/README → páginas.
Evolution e Telegram: só pelas variáveis de ambiente, testados contra o servidor falso dos testes; nunca chamar API real.
Enquanto existir uma próxima ação objetiva, segura e alinhada ao objetivo, execute-a sem esperar nova instrução.
3 ciclos sem avanço mensurável (nº de testes passando) = parar, registrar em failures.md e me chamar.
Teste que contradiz a especificação = registrar em failures.md e me chamar; nunca alterar teste ou spec.

PARE E ME CHAME SÓ SE: gasto de crédito/API, ação irreversível ou externa (push, repo remoto, apagar), dependência externa, credencial ausente, decisão de negócio, conflito real entre teste e especificação.
