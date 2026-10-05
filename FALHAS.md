# FALHAS

| data | o que quebrou | menor correção | prompt \| infra |
|---|---|---|---|
| 2026-10-05 | páginas retornavam 404 e formulário enviava nascimento vazio inválido | servir páginas locais e converter campo opcional vazio para null; 93 testes e cadastro em navegador aprovados | infra |
| 2026-10-05 | entrega Docker ausente e CLI rejeitava host exigido pelo container | adicionar arquivos de entrega e aceitar --host; 4 testes adicionais aprovados e healthcheck local passou | infra |
| 2026-10-05 | integrações ausentes impediam WhatsApp e atendimento pelo Telegram | implementar transportes opcionais, deduplicação persistente e vínculos de atendimento; 88 passed / 5 failed | infra |
| 2026-10-05 | cadastros, bloqueios e backup ausentes causavam 10 falhas de aceitação | adicionar rotas CRUD, filtro de bloqueios e snapshot SQLite; suíte passou de 63 para 73 testes aprovados | infra |
| 2026-10-05 | opt-out e histórico de desconhecido não migravam ao cadastrar pela API | associar histórico e ler preferência da sessão em criar_paciente; verificação local passou | infra |
| 2026-10-05 | leitura usou nomes de arquivos inexistentes e repetiu tail abreviado | conferir caminhos com rg --files e usar tail -n | prompt |
| 2026-10-05 | tail com opção antiga e múltiplos arquivos recusou leitura | usar `tail -n 20` | prompt |
| 2026-10-05 | `verificar-independente.py` acusou agendamento falho na clínica nova: o atalho `Cliente.agenda()` usa servico="avaliacao" por padrão e a clínica nova só tem "sessao" (bug do verificador, não do sistema) | passar `servico="sessao"` explícito | prompt |
| 2026-10-05 | `atende serve` órfão por 14 h: no test_backup_e_restaurar o 1º Servidor subia fora de try/finally e asserção falhando antes do parar() deixava o processo vivo | registro SERVIDORES + fixture autouse que para todos no teardown | prompt |
