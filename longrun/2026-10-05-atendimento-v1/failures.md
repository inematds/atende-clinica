# Falhas (só acrescentar; ao fim, a menor correção vira linha no FALHAS.md do projeto)

| data | o que quebrou | tentativa | resultado | prompt \| infra |
|---|---|---|---|---|
| 2026-10-05 00:30 | 73 testes falham por funcionalidades ainda ausentes (inclusive LGPD no teste de telefone) → implementada base/agenda → 20 passed, restante registrado no plano; sem conflito com spec identificado | base executável + suíte inteira | checkpoint parcial | infra |
| 2026-10-05 00:30 | `tail -20` com vários arquivos rejeitado → usado `tail -n 20` → leitura concluída | opção explícita -n | corrigido | prompt |
| 2026-10-05 00:33 | tail abreviado e caminhos inferidos inexistentes → tail -n e nomes conferidos em rg --files → leituras corrigidas, lição em CLAUDE.md | leitura explícita | corrigido | prompt |
| 2026-10-05 00:33 | 50 testes ainda falham por páginas, cadastros, campanhas, DELETE LGPD/Raio-X, integrações e Docker ausentes → implementada conversa/lembretes → 43 passed / 50 failed, nenhuma regressão observada ou contradição identificada | próximo escopo documentado | parcial | infra |
| 2026-10-05 00:39 | Leitura inicial repetiu tail abreviado e buscou diretórios de contexto ausentes → tail -n e arquivos existentes → leitura concluída; lições já constam em CLAUDE.md | corrigir comando de leitura | corrigido | prompt |
| 2026-10-05 00:39 | 30 testes falham por páginas/cadastros/bloqueios/backup/integrações/Docker ausentes → campanhas/LGPD/Raio-X implementados → 63 passed / 30 failed, sem regressão ou conflito de contrato identificado | próximo escopo registrado no plano | parcial | infra |
| 2026-10-05 00:52 | tail abreviado repetido na leitura inicial → corrigido para tail -n → leitura concluída; lição existente em CLAUDE.md | sintaxe explícita | corrigido | prompt |
| 2026-10-05 00:52 | 20 testes falham por integrações/páginas/Docker/README ausentes → implementados cadastros/bloqueios/backup → 73 passed / 20 failed, sem regressão ou conflito identificado | próximo escopo no plano | parcial | infra |
| 2026-10-05 00:52 | git diff --check global sinalizou whitespace no ciclo-1.log gerado pelo loop → verificação restrita aos arquivos editados → sem problema no código; log preservado | não editar saída do loop | log externo preservado | infra |
| 2026-10-05 01:00 | tail abreviado rejeitado na leitura inicial → corrigido para tail -n → leitura concluída; lição já registrada em CLAUDE.md | sintaxe explícita | corrigido | prompt |
| 2026-10-05 01:00 | integrações ausentes e 20 falhas anteriores → implementados Evolution/Telegram → 88 passed / 5 failed; restantes páginas/Docker/README, sem conflito identificado | próximo escopo no plano | parcial | infra |
| 2026-10-05 01:04 | tail abreviado novamente rejeitado → tail -n → leitura concluída; lição existente em CLAUDE.md | sintaxe explícita -n | corrigido | prompt |
| 2026-10-05 01:04 | Docker/documentação ausentes → entrega e remoção da restrição indevida de --host → 92 passed / 1 failed; test_paginas segue 404 por interface ainda ausente, sem contradição de contrato | implementar páginas no próximo ciclo | parcial | infra |
| 2026-10-05 01:13 | test_paginas retornava 404 por páginas ausentes → adicionadas páginas e rotas explícitas; revisão detectou nascimento vazio enviado como string → convertido para null nos formulários → 93 passed / 0 failed e cadastro real pelo navegador aprovado | implementação de interface e normalização do campo opcional | corrigido, sem conflito teste/spec | infra |
