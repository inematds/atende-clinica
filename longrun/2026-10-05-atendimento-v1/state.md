# Estado — atualizado 2026-10-05

## Funciona
- (nada implementado ainda) — contrato e 62 testes de aceitação escritos; harness conferido com stub

## Falta
- responder docs/DECISOES-ABERTAS.md → rodar congelar.sh → iniciar o loop/goal
- toda a implementação (atende, src/, web/)

## Como retomar (comandos exatos)
```
cd ~/projetos/atende-clinica
python3 -m pytest -q tests/ | tail -3
bash longrun/2026-10-05-atendimento-v1/verificar-limites.sh
```

Ao retomar/após compactação: ler goal.md → state.md → plan.md → fim de progress.md e failures.md.
