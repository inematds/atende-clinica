# Plano

## Estratégia atual
Python 3 stdlib, HTTP local, SQLite com lock/transação por requisição. Catálogo/agenda em core.py, conversa/notificações em conversa.py, campanhas/LGPD/Raio-X em gestao.py. Contrato e testes intactos; nenhuma rede externa.

## Próximos 3 passos
1. Cadastros de pacientes/profissionais/serviços/FAQ, bloqueios e CLI backup/restaurar. Reutilizar catálogo SQLite e validar disponibilidade/bloqueios na mesma transação. Verificar regressão de campanhas e Raio-X.
2. Evolution e Telegram somente pelas variáveis contratadas e testes com servidores falsos locais; responder/encerrar pela recepção, silêncio e repasse enquanto aberto, reenvio de pendentes. Revisar bordas da conversa anotadas no state.
3. Docker/compose/.env.exemplo/README e páginas web completas. Rodar suíte e limites; atualizar registros, sem commit e sem marcar concluído antes dos dois portões passarem.
