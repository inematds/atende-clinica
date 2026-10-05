# Plano

## Estratégia atual
Python 3 stdlib, HTTP local e SQLite com lock/transação por requisição. core.py: agenda; cadastros.py: CRUD/bloqueios; backup.py: snapshot; conversa.py: fluxo/notificações; gestao.py: campanhas/LGPD/Raio-X; integracoes.py: Evolution/Telegram e atendimento humano. Contrato e testes intactos.

## Próximos 3 passos
1. Entrega Docker/compose/.env.exemplo/README: ler testes, conciliar bind do container com limites da execução, documentar configuração, webhooks e backup diário sem realizar chamadas reais.
2. Páginas em web/: chat paciente e recepção com token, cadastros, agenda, fila humana responder/encerrar, saída e operações disponíveis; servir HTML corretamente em server.py.
3. Revisar bordas de conversa anotadas no state; rodar suíte completa e limites, registrar evidências e só marcar concluído se ambos passarem. Não alterar testes/spec/verificadores nem fazer commit.
