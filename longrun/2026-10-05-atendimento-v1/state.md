# Estado — atualizado 2026-10-05 01:13

## Funciona
concluído

- `./atende` implementa base HTTP/SQLite, autenticação, agenda, conversa, confirmações, espera, retornos, campanhas, LGPD, Raio-X, cadastros, bloqueios, backup/restauração e integrações opcionais pelo ambiente.
- Chat em `/` e recepção em `/recepcao`, com arquivos em web/. Recepção permite cadastros/edição, agenda por período, reserva/espera, presença/cancelamento/remarcação, fila humana responder/encerrar, bloqueios, FAQ, campanhas, saída, tarefas, LGPD e indicadores.
- Token somente na memória da aba; saída da sessão limpa dados renderizados. Assets servidos por lista fixa, CSP local e conteúdo dinâmico via textContent. Nenhuma dependência de CDN.
- Dockerfile copia web/, README atualizado e VERSION 0.7.0.
- Suíte final: **93 passed / 0 failed**, 25.46s, `pytest-ciclo-7.log`. **LIMITES OK** (hash ab5cccd19cc8242a, 93 testes, escopo intacto). Sintaxe de ambos os scripts JS e diff --check dos arquivos editados passaram. Detector de UI não apontou ocorrências.
- Chromium local: login, cadastro com nascimento opcional vazio, logout apagando lista de pacientes e chat iniciando agendamento passaram. Screenshots recepcao-desktop.png (1280×900) e recepcao-mobile.png (390×844) inspecionados; sem overflow horizontal. Processos iniciados foram encerrados pelos respectivos PIDs.

## Falta
- Critérios automáticos deste longrun satisfeitos. Conforme goal, verificador independente (inclui Docker build/container) e aceite humano das páginas são etapa posterior; build Docker não executado neste ciclo.
- Bordas anotadas em ciclos anteriores não foram ampliadas neste: preferência de desconhecido ao limpar sessão por emergência, confirmação antiga após remarcação e catálogo desativado durante fluxo.
- Limitação conhecida: envios síncronos com timeout sob transação; queda após envio remoto e antes do commit pode duplicar entrega. Sem garantia exactly-once.
- A recepção usa atualização manual. Retorno humano ao paciente segue telefone/Evolution; sem integração fica na saída simulada, conforme README.

## Como retomar
1. Critérios de encerramento atingidos; loop externo pode registrar o checkpoint. Não foi feito commit nesta execução.
2. Para auditoria, ler goal → state → plan → canal; resultados em pytest-ciclo-7.log e screenshots neste diretório.
3. Validação independente e Docker ficam para a etapa humana prevista no goal, respeitando autorização de rede. Não chamar integrações reais automaticamente.
