# Plano

## Estratégia atual
Python 3 stdlib, HTTP local, SQLite com lock/transação por requisição. Catálogo/agenda em core.py, CRUD/bloqueios em cadastros.py, backup em backup.py, conversa/notificações em conversa.py, campanhas/LGPD/Raio-X em gestao.py. Contrato e testes intactos.

## Próximos 3 passos
1. Evolution: webhook com segredo e deduplicação persistente, conversa compartilhada, saída com status e reenvio de pendentes. Somente variáveis contratadas e servidor falso local. Revisar bordas de conversa anotadas no state.
2. Telegram: abertura/repasse, respostas vinculadas ao atendimento, comandos, notificações e responder/encerrar pela recepção. Testar exclusivamente no falso local; garantir silêncio do bot com atendimento aberto.
3. Docker/compose/.env.exemplo/README e páginas web completas. Rodar suíte e limites; atualizar registros sem commit e sem marcar concluído antes dos dois portões passarem.
