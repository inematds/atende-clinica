# Plano

## Estratégia atual
Python 3 stdlib, HTTP local, SQLite com lock reentrante/transação por requisição. Conversa e notificações no módulo src/conversa.py; catálogo e agenda em src/core.py. Nenhuma chamada externa e nenhum arquivo protegido alterado.

## Próximos 3 passos
1. Campanhas (todas as violações por conselho, opt-in/opt-out) e LGPD DELETE: anonimizar histórico, saída e sessões, cancelar agenda futura e manter agregados; fechar os casos de borda de opt-out/pendências descritos no state.
2. Raio-X HTTP/CLI com métricas mensais e mesclagem do acompanhamento. Em seguida CRUDs, bloqueios e backup/restauração.
3. Evolution/Telegram exclusivamente com falsos locais, depois Docker/README e páginas. Validar suíte e limites a cada ciclo, sem marcar concluído antes dos dois portões passarem.
