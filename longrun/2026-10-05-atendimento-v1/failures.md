# Falhas (só acrescentar; ao fim, a menor correção vira linha no FALHAS.md do projeto)

| data | o que quebrou | tentativa | resultado | prompt \| infra |
|---|---|---|---|---|
| 2026-10-05 00:30 | 73 testes falham por funcionalidades ainda ausentes (inclusive LGPD no teste de telefone) → implementada base/agenda → 20 passed, restante registrado no plano; sem conflito com spec identificado | base executável + suíte inteira | checkpoint parcial | infra |
| 2026-10-05 00:30 | `tail -20` com vários arquivos rejeitado → usado `tail -n 20` → leitura concluída | opção explícita -n | corrigido | prompt |
| 2026-10-05 00:33 | tail abreviado e caminhos inferidos inexistentes → tail -n e nomes conferidos em rg --files → leituras corrigidas, lição em CLAUDE.md | leitura explícita | corrigido | prompt |
| 2026-10-05 00:33 | 50 testes ainda falham por páginas, cadastros, campanhas, DELETE LGPD/Raio-X, integrações e Docker ausentes → implementada conversa/lembretes → 43 passed / 50 failed, nenhuma regressão observada ou contradição identificada | próximo escopo documentado | parcial | infra |
| 2026-10-05 00:39 | Leitura inicial repetiu tail abreviado e buscou diretórios de contexto ausentes → tail -n e arquivos existentes → leitura concluída; lições já constam em CLAUDE.md | corrigir comando de leitura | corrigido | prompt |
| 2026-10-05 00:39 | 30 testes falham por páginas/cadastros/bloqueios/backup/integrações/Docker ausentes → campanhas/LGPD/Raio-X implementados → 63 passed / 30 failed, sem regressão ou conflito de contrato identificado | próximo escopo registrado no plano | parcial | infra |
