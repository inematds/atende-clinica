# Estado — atualizado 2026-10-05 00:52

## Funciona
- CLI serve com PORTA, bind 127.0.0.1, auth X-Token, SQLite persistente, configuração e catálogo semeado uma vez; agenda transacional e normalização de telefones.
- Conversa persistente: emergência, opt-out, FAQ, fallback, fila humana, agendamento, confirmação, espera FIFO e retorno. Atendimento aberto silencia o bot, exceto emergência.
- Campanhas com regras dos quatro conselhos, lista completa de violações, consentimento e opt-out. LGPD exporta histórico e anonimiza contato, histórico/saída/sessão/fila, preservando agregados.
- Raio-X HTTP/CLI calcula indicadores do banco/calendário, mescla mês anterior/base, preserva campos não medidos e grava JSON atomicamente.
- Cadastros completos em src/cadastros.py: profissionais (registro/horários próprios), serviços e desativação; pacientes com busca sem acento/caixa e edição validada; FAQ com efeito imediato. Edições persistem sem ressemear o catálogo.
- Bloqueios persistentes: retiram horários sobrepostos, novas reservas recebem 422, informam conflitos ativos sem cancelar consultas existentes; exclusão libera a grade. Listagem por período/profissional passa.
- CLI backup/restaurar em src/backup.py: snapshot SQLite consistente com servidor ligado, ZIP com banco e clinica.json; restauração validada com servidor parado. Verificação local adicional passou para configuração, paciente, FAQ, bloqueio e rejeição de arquivo inválido sem alteração do banco.
- Versão 0.4.0. Suíte completa: **73 passed / 20 failed**, sem errors, em 65.80s; pytest-ciclo-4.log. Ganho de 10 testes, sem regressão observada; todos os testes de cadastros passam.
- Verificador: **LIMITES OK**, 93 testes e contrato intacto. Nenhuma rede externa, API real ou commit neste ciclo.

## Falta
- Evolution e Telegram: webhooks, envio/reenvio, responder/encerrar pela recepção, notificações à equipe. Ainda nenhuma chamada de integração implementada.
- Docker, compose, .env.exemplo, README e páginas web.
- Revisar bordas da conversa: preferências de desconhecido ao limpar sessão por emergência; respostas a confirmações depois de alteração do agendamento; opções antigas de catálogo durante um fluxo.
- Nenhum conflito teste/spec identificado neste ciclo. Restrição de bind local prevalece durante o loop; conciliar Docker ao implementar entrega.

## Como retomar
1. Ler goal → state → plan → canal e fins de progress/failures. Especificação inteira e conftest foram lidos neste ciclo.
2. Ler src/server.py, src/conversa.py e tests/test_integracoes.py. HTTP envolve operações em lock/transação; conversa.iniciar cria tabelas adicionais e é chamado em serve e raiox.
3. Implementar Evolution e Telegram exclusivamente com variáveis da spec e servidores falsos locais dos testes; sem URLs externas no código nem credenciais reais.
4. Rodar suíte inteira para arquivo e ler só tail -n 30, executar verificar-limites.sh, atualizar registros. Não fazer commit. Só marcar concluído quando os dois portões passarem.
