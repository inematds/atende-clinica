# Decisões (só acrescentar)

| data | decisão | motivo | alternativa descartada |
|---|---|---|---|
| 2026-10-05 00:30 | SQLite com RLock reentrante e transação envolvendo cada requisição de domínio | checagem de disponibilidade e escrita atômicas; concorrência comprovada pelo teste de 10 pedidos | validar fora da transação |
| 2026-10-05 00:30 | Catálogo JSON em tabela SQLite com marcador de semeadura único; pacientes/agendamentos relacionais | preserva ordem da configuração e futuros CRUDs, sem repovoar itens apagados | reler os cadastros do JSON a cada boot |
| 2026-10-05 00:33 | Sessões JSON por telefone; histórico separado da caixa de saída, vinculado ao paciente ao cadastrar pelo chat | preservar mensagens de desconhecidos e dar continuidade após reinício; saída só contém notificações contratadas | guardar conversa em memória ou misturar respostas do chat na caixa de saída |
| 2026-10-05 00:33 | Cancelamento comum entre API e chat; retorno único por agendamento; oferta de espera guarda o horário original | efeitos consistentes e idempotentes, aceite revalida disponibilidade na mesma transação | reservar vaga apenas porque foi ofertada |
| 2026-10-05 00:39 | Campanhas validam todas as regras antes de criar saída; pontuação preservada após remover acentos | detectar r$ e 100% e impedir envio parcial | reutilizar normalizador de conversa que remove pontuação |
| 2026-10-05 00:39 | LGPD desvincula contato antes de cancelar agenda, apaga identificadores/textos de sessão/fila/saída e conserva registros quantitativos | impedir ofertas ao excluído sem perder agregados nem manter telefone reconhecido | apagar paciente e quebrar referências da agenda |
| 2026-10-05 00:39 | Raio-X usa calendário e horários de cada profissional; exportação mescla mês anterior cronológico/base e substitui JSON atomicamente | números independem do fixture; preservar campos não medidos e evitar arquivo parcial | constantes do mês ou gravação direta do JSON |
| 2026-10-05 00:52 | Bloqueios entram no cálculo de candidatos com intervalos semiabertos; cadastros mantêm ordem de inserção e desativação lógica | reserva em bloqueio retorna 422 e agenda histórica permanece | tratar bloqueio como agendamento ocupado (409) |
| 2026-10-05 00:52 | Backup ZIP inclui clinica.json e snapshot feito por sqlite3.Connection.backup; arquivo final substituído com os.replace | cópia consistente com servidor ligado; restauração valida antes de substituir e exige servidor parado | copiar SQLite diretamente durante escrita ou extrair caminhos arbitrários de ZIP |
