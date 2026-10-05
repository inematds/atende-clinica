# Decisões (só acrescentar)

| data | decisão | motivo | alternativa descartada |
|---|---|---|---|
| 2026-10-05 00:30 | SQLite com RLock reentrante e transação envolvendo cada requisição de domínio | checagem de disponibilidade e escrita atômicas; concorrência comprovada pelo teste de 10 pedidos | validar fora da transação |
| 2026-10-05 00:30 | Catálogo JSON em tabela SQLite com marcador de semeadura único; pacientes/agendamentos relacionais | preserva ordem da configuração e futuros CRUDs, sem repovoar itens apagados | reler os cadastros do JSON a cada boot |
