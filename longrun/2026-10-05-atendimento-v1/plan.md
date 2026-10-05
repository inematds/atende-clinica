# Plano (reescrever, não acumular)

## Estratégia atual
Python 3 só stdlib: `atende` (CLI) → `src/` (servidor ThreadingHTTPServer, SQLite com lock para a concorrência, motor de agenda, motor de conversa, tarefas, trava de conselho, raiox) → `web/` (chat e recepção, HTML+JS sem CDN). Implementar na ordem dos arquivos de teste, rodando a suíte a cada passo.

## Próximos passos
1. `./atende serve --porta 0 --dados DIR` com PORTA=, clinica.json padrão, /api/saude, /api/servicos, auth X-Token, páginas mínimas → test_basico.
2. Grade de horários, pacientes (telefone), agendar/cancelar/remarcar/presença com 409/422 e lock → test_agenda.
3. Conversa (emergência, parar, humano, fluxo, pendências, FAQ, não entendi) → test_conversa; depois lembretes, campanhas, LGPD/raiox.
