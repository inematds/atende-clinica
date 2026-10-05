# Plano

## Estratégia atual
Python 3 stdlib, ThreadingHTTPServer, SQLite; lock reentrante e transação por requisição serializam validação e gravação. Separar novos motores em módulos de src/ conforme cresçam. Não editar arquivos protegidos nem fazer chamadas externas.

## Próximos 3 passos
1. Conversa: normalização, emergência, opt-out, fila humana, fluxo de agendamento, FAQ e fallback; persistir sessões/histórico. Preservar prioridade da emergência e silêncio durante atendimento humano aberto.
2. Mensagens de saída/pendências, confirmação, espera e retorno, com idempotência e efeitos em cancelar/presença. Validar a suíte inteira e registrar falhas restantes.
3. Campanhas e LGPD, depois Raio-X. Seguir com cadastros/bloqueios/backup → Evolution/Telegram (só falsos locais) → Docker/README → páginas.
