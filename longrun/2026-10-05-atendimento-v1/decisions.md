# Decisões (só acrescentar)

| data | decisão | motivo | alternativa descartada |
|---|---|---|---|
| 2026-10-05 00:30 | SQLite com RLock reentrante e transação envolvendo cada requisição de domínio | checagem de disponibilidade e escrita atômicas; concorrência comprovada pelo teste de 10 pedidos | validar fora da transação |
| 2026-10-05 00:30 | Catálogo JSON em tabela SQLite com marcador de semeadura único; pacientes/agendamentos relacionais | preserva ordem da configuração e futuros CRUDs, sem repovoar itens apagados | reler os cadastros do JSON a cada boot |
| 2026-10-05 00:33 | Sessões JSON por telefone; histórico separado da caixa de saída, vinculado ao paciente ao cadastrar pelo chat | preservar mensagens de desconhecidos e dar continuidade após reinício; saída só contém notificações contratadas | guardar conversa em memória ou misturar respostas do chat na caixa de saída |
| 2026-10-05 00:33 | Cancelamento comum entre API e chat; retorno único por agendamento; oferta de espera guarda o horário original | efeitos consistentes e idempotentes, aceite revalida disponibilidade na mesma transação | reservar vaga apenas porque foi ofertada |
