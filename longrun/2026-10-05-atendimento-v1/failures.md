# Falhas (só acrescentar; ao fim, a menor correção vira linha no FALHAS.md do projeto)

| data | o que quebrou | tentativa | resultado | prompt \| infra |
|---|---|---|---|---|
| 2026-10-05 00:30 | 73 testes falham por funcionalidades ainda ausentes (inclusive LGPD no teste de telefone) → implementada base/agenda → 20 passed, restante registrado no plano; sem conflito com spec identificado | base executável + suíte inteira | checkpoint parcial | infra |
| 2026-10-05 00:30 | `tail -20` com vários arquivos rejeitado → usado `tail -n 20` → leitura concluída | opção explícita -n | corrigido | prompt |
