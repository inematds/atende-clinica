# Plano

## Estratégia atual
Python 3 stdlib, HTTP e SQLite com lock/transação por requisição. Domínio e integrações implementados. Docker/documentação entregues; falta interface web.

## Próximos 3 passos
1. Criar web/ com chat paciente e recepção: token em memória, cadastros, agenda, fila humana responder/encerrar e saída; servir HTML nas rotas públicas sem expor arquivos arbitrários.
2. Integrar web/ ao Dockerfile, atualizar README e verificar páginas/fluxos com servidor exclusivamente local; revisar bordas pendentes da conversa se houver espaço no ciclo.
3. Rodar suíte inteira e verificar-limites.sh, registrar evidências e atualizar estado; marcar concluído somente com ambos aprovados. Build/container e inspeção humana posterior conforme goal; nenhuma rede externa ou commit.
