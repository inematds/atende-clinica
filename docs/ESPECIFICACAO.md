# Especificação v1 — atende-clinica (contrato congelado)

> Este arquivo é **protegido** durante a execução longa: o agente implementa contra ele e não o altera.
> Os testes em `tests/` verificam exatamente o que está aqui. Mudança de contrato = humano edita, recongela o hash e reinicia o longrun.

## 0. O que é

Sistema de atendimento ao paciente para **uma clínica** (consultório, odonto, fisio, estética): agenda, confirmação automática, lista de espera, retorno programado, tirar dúvidas (FAQ), passagem para humano, emergência, campanhas com trava de conselho/LGPD e exportação de números para o **Painel de Recuperação do Raio-X de Margem**.

Canal v1 = **simulado** (mensagens de saída vão para uma caixa de saída consultável) + **chat web**. WhatsApp real é portão humano (seção 12).

## 1. Execução

- Ponto de entrada: arquivo executável `./atende` na raiz do repo.
- `./atende serve --porta N --dados DIR`
  - `--porta 0` = porta livre escolhida pelo sistema. A **primeira linha** do stdout é `PORTA=<n>` (com flush), impressa quando o servidor já aceita conexões.
  - Escuta só em `127.0.0.1`.
  - `DIR/clinica.json` = configuração (seção 2). Se não existir, copiar `exemplos/clinica.json`.
  - Todo o estado persiste em `DIR/` (ex.: SQLite). Reiniciar com o mesmo `DIR` mantém tudo.
- **Relógio:** variável de ambiente `ATENDE_AGORA` (`AAAA-MM-DDTHH:MM`, hora local da clínica, sem fuso) fixa o "agora" do processo. Sem ela, usa o relógio real. Datas/horas no contrato são sempre `AAAA-MM-DDTHH:MM` local.
- `./atende raiox --dados DIR --mes AAAA-MM --acompanhamento ARQ` (seção 10).
- Sem rede externa. Sem API paga. Sem chave de API.

## 2. `clinica.json`

```json
{
  "nome": "Clínica Sorriso",
  "conselho": "cfo",                 // cfm | cfo | coffito | estetica
  "token": "segredo",               // exigido no header X-Token das rotas da recepção
  "passo_min": 30,                   // grade de horários
  "antecedencia_min_horas": 2,       // não oferece/aceita horário antes de agora + isto
  "janela_dias": 14,                 // até quantos dias à frente o chat oferece horários
  "confirmacao_horas": 48,           // pede confirmação quando a consulta começa em até 48 h
  "retorno_aviso_dias": 7,           // avisa o retorno quando faltam até 7 dias
  "feriados": ["2026-10-12"],
  "horarios": { "seg": [["08:00","12:00"],["14:00","18:00"]], "ter": [...], "qua": [...], "qui": [...], "sex": [...], "sab": [["08:00","12:00"]], "dom": [] },
  "profissionais": [ { "id": "ana", "nome": "Dra. Ana", "servicos": ["avaliacao","limpeza"] } ],
  "servicos": [ { "id": "limpeza", "nome": "Limpeza", "duracao_min": 60, "retorno_dias": 180 } ],
  "faq": [ { "id": "convenios", "perguntas": ["vocês aceitam convênio"], "resposta": "Atendemos Unimed Odonto e particular." } ]
}
```

`retorno_dias` pode ser `null` (sem retorno). Dias da semana: `seg ter qua qui sex sab dom`.

## 3. Regras de agenda

- Horário candidato: começa no início de uma janela e anda de `passo_min` em `passo_min`; vale se `[inicio, inicio+duracao)` cabe inteiro na janela.
- **Inválido (422)** se: não é horário candidato (fora da grade ou não cabe na janela); dia em `feriados`; `inicio < agora + antecedencia_min_horas`; profissional não faz o serviço.
- **Ocupado (409)** se é válido mas sobrepõe outro agendamento **ativo** do mesmo profissional (ou, sem profissional indicado, de todos que fazem o serviço).
- `GET /api/horarios` lista só horários válidos e livres.
- Agendamento ativo = status `agendado`, `confirmado`, `realizado` ou `falta`. `cancelado` libera o horário.
- Dois pedidos simultâneos para o mesmo horário/profissional: exatamente um vence (201), o outro recebe 409.

## 4. Autenticação

Rotas marcadas **[R]** (recepção) exigem header `X-Token` igual a `clinica.json.token`; sem ele ou errado → **401**. Rotas públicas: `/`, `/recepcao` (página; os dados vêm de rotas [R]), `/api/saude`, `/api/servicos`, `/api/horarios`, `/api/mensagens`.

## 5. API HTTP (JSON, UTF-8)

| Método e rota | Corpo | Resposta |
|---|---|---|
| `GET /api/saude` | — | 200 `{"ok": true, "versao": "<conteúdo de VERSION>"}` |
| `GET /api/servicos` | — | 200 `{"servicos": [{id, nome, duracao_min}]}` |
| `GET /api/horarios?servico=S&data=AAAA-MM-DD[&profissional=P]` | — | 200 `{"horarios": [{"inicio", "profissional"}]}` ordenado por `inicio`, depois `profissional`; serviço inexistente → 404 |
| `POST /api/pacientes` [R] | `{nome, telefone, consentimento_marketing?: bool}` | 201 `{id}`; telefone já cadastrado → 200 com o mesmo `{id}`; telefone inválido → 400 |
| `POST /api/agendamentos` [R] | `{paciente_id, servico, inicio, profissional?}` | 201 `{id, status: "agendado", inicio, fim, profissional}`; sem `profissional` = o primeiro livre por ordem de `id`; horário ocupado → 409; horário inválido (regra 3) → 422; paciente/serviço inexistente → 404 |
| `GET /api/agendamentos?data=AAAA-MM-DD` [R] | — | 200 `{"agendamentos": [{id, paciente_id, telefone, servico, profissional, inicio, fim, status}]}` |
| `POST /api/agendamentos/{id}/cancelar` [R] | — | 200 `{status: "cancelado"}`; dispara a lista de espera (seção 7) |
| `POST /api/agendamentos/{id}/remarcar` [R] | `{inicio}` | 200 com o agendamento no novo horário (mesmo `id`, status `agendado`); mesmas regras de 409/422 |
| `POST /api/agendamentos/{id}/presenca` [R] | `{compareceu: bool}` | 200 `{status: "realizado" \| "falta"}`; `realizado` + `retorno_dias` cria retorno (seção 8); pode ser marcada a qualquer momento (não depende do relógio) |
| `POST /api/espera` [R] | `{paciente_id, servico, data}` | 201 `{id}` |
| `POST /api/tarefas/rodar` [R] | `{agora?}` (padrão = relógio do processo) | 200 `{"enviadas": n}`; idempotente: rodar de novo no mesmo instante → `enviadas: 0` |
| `GET /api/saida` [R] | — | 200 `{"mensagens": [{id, tipo, telefone, paciente_id, texto, agendamento_id}]}` em ordem de criação. `tipo` ∈ `confirmacao, espera, retorno, campanha` |
| `POST /api/mensagens` | `{telefone, texto}` | 200 `{"respostas": [texto, ...]}` (seção 6) |
| `GET /api/atendimento-humano` [R] | — | 200 `{"fila": [{telefone, motivo, prioridade}]}`; `prioridade` ∈ `normal, alta` |
| `POST /api/campanhas` [R] | `{texto}` | 200 `{"enviadas": n}` ou 422 `{"violacoes": [codigos]}` (seção 9) |
| `GET /api/pacientes/{id}/dados` [R] | — | 200 `{paciente, agendamentos, mensagens}` (LGPD art. 18, II) |
| `DELETE /api/pacientes/{id}` [R] | — | 204; anonimiza (seção 11) |
| `GET /api/raiox?mes=AAAA-MM` [R] | — | 200 (seção 10) |

Telefone: aceita com ou sem `+55`, espaços, parênteses e hífen; normaliza para `+55DDNNNNNNNNN` (DDD + 8 ou 9 dígitos). Fora disso → inválido. Todas as respostas usam o telefone normalizado.

## 6. Conversa (`POST /api/mensagens`)

O texto é normalizado (minúsculas, sem acento, sem pontuação) antes de decidir. Ordem de decisão:

1. **Emergência** — contém um destes: `dor no peito`, `falta de ar`, `desmaio`, `desmaiou`, `sangramento`, `sangrando`, `convulsao`, `suicidio`, `me matar`, `avc`, `infarto`. Resposta contém `192` e `pronto-socorro`; entra na fila humana com `prioridade: "alta"`. Não agenda nada.
2. **Parar** — texto igual a `parar`, `sair` ou `pare`: paciente fica `nao_contatar`; resposta contém `não vai mais receber`. Nenhuma mensagem de saída (confirmação, retorno, campanha, espera) vai mais para esse telefone.
3. **Humano** — contém `atendente`, `humano` ou `falar com alguem`: fila humana com `prioridade: "normal"`; resposta contém `atendente`.
4. **Fluxo em andamento** (agendamento pelo chat, abaixo) consome a mensagem.
5. **Resposta a pendência**: se a última mensagem de saída para o telefone foi `confirmacao` (sem resposta ainda): `1`/`sim`/`confirmo` → status `confirmado`, resposta contém `confirmad`; `2`/`cancelar`/`nao` → status `cancelado` (dispara espera), resposta contém `cancelad`. Se foi `espera` (sem resposta): `1`/`sim` → agenda o horário ofertado se ainda livre (resposta contém `agendad`), senão resposta contém `ocupado`.
6. **Agendar** — contém `agendar`, `marcar` ou `consulta`: inicia o fluxo.
7. **FAQ** — palavras significativas (≥ 3 letras, fora de artigos/preposições/pronomes comuns) de alguma pergunta do FAQ: se ≥ 60 % delas aparecem no texto, responde **exatamente** a `resposta` daquele item (só ela, uma mensagem). Mais de um item casa → o de maior %; empate → o primeiro do FAQ.
8. **Não entendi** — resposta contém `não entendi` e oferece `atendente`. Na **segunda** seguida sem entender, entra na fila humana (`normal`) automaticamente.

**Fluxo de agendamento pelo chat** (estado por telefone, persistido):
- telefone sem paciente → pergunta o nome (resposta contém `nome`); a próxima mensagem vira o nome e o paciente é criado (`consentimento_marketing: false`).
- lista os serviços numerados `1 - <nome>` na ordem do `clinica.json`;
- escolhido o número, oferece os **3 primeiros** horários livres a partir de `agora + antecedencia_min_horas`, dentro de `janela_dias`, em todos os profissionais, ordem da seção 5; cada linha `N) DD/MM HH:MM com <nome do profissional>`;
- escolhido o número, cria o agendamento; resposta contém `agendad`, `DD/MM` e `HH:MM`.
- número inválido em qualquer passo → repete as opções. `cancelar` dentro do fluxo → sai do fluxo.
- O bot **nunca** inventa preço, diagnóstico ou orientação de remédio: fora do FAQ cai na regra 8.

## 7. Lista de espera

Ao cancelar (pela API ou pela conversa), o primeiro pedido de espera ainda não atendido com o mesmo `servico` e a mesma `data` do horário liberado (ordem de criação), cujo paciente não esteja `nao_contatar`, recebe mensagem `tipo: "espera"` contendo `HH:MM` do horário e `1`. O pedido fica `ofertado` (não recebe outra oferta do mesmo horário).

## 8. Confirmação e retorno (`POST /api/tarefas/rodar`)

- **Confirmação:** todo agendamento `agendado` com `agora < inicio ≤ agora + confirmacao_horas` que ainda não recebeu confirmação → mensagem `tipo: "confirmacao"` com `agendamento_id`. Texto contém o nome do serviço, `DD/MM`, `HH:MM`, `1` (confirmar) e `2` (cancelar). **Não contém valor em R$.**
- **Retorno:** presença `realizado` de serviço com `retorno_dias` cria um retorno com `data = data do atendimento + retorno_dias`. Quando `agora ≥ data − retorno_aviso_dias` e ainda não avisado → mensagem `tipo: "retorno"` com o nome do serviço. Uma vez só.
- Paciente `nao_contatar` nunca recebe. Lembrete e retorno **não** dependem de `consentimento_marketing` (LGPD art. 11, II, f — tutela da saúde).

## 9. Campanhas e trava de conselho

`POST /api/campanhas {texto}` envia só para pacientes com `consentimento_marketing: true` e sem `nao_contatar` (LGPD art. 11, I — consentimento específico). Antes de enviar, valida o texto em minúsculas e sem acento (**pontuação mantida**, para `r$` e `100%`). O `422` lista **todos** os códigos violados. Qualquer violação → 422 e nada é enviado.

| Código | Detecta | cfm | cfo | coffito | estetica |
|---|---|---|---|---|---|
| `promessa_resultado` | `garantido`, `garantia de resultado`, `100%`, `resultado garantido` | ✔ | ✔ | ✔ | ✔ |
| `melhor_profissional` | `melhor medico`, `melhor dentista`, `melhor fisioterapeuta`, `melhor clinica` | ✔ | ✔ | ✔ | — |
| `sorteio_brinde` | `sorteio`, `brinde`, `premio`, `premiacao` | ✔ | ✔ | — | — |
| `antes_depois` | `antes e depois` | ✔ | ✔ | — | — |
| `consorcio` | `consorcio` | ✔ | — | — | — |
| `preco` | `r$`, `reais` | — | ✔ | ✔ | — |
| `parcelamento` | `parcela`, `parcelamento`, `sem juros`, `10x` (qualquer `<n>x`) | — | ✔ | — | — |
| `gratuito` | `gratis`, `gratuito`, `gratuita` | — | ✔ | ✔ | — |
| `promocao` | `promocao`, `desconto`, `oferta` | — | — | ✔ | — |

Bases: CFM 2.336/2023 arts. 9º e 11; CFO 118/2012 art. 44 + 196/2019 + 271/2025; COFFITO 424/2013 arts. 39–40. Fonte e leitura em `raio-x-margem/docs/setores/servicos-pesquisa-2026-10.md`.

## 10. Exportação para o Raio-X (Painel de Recuperação)

`GET /api/raiox?mes=AAAA-MM` → `{"pacote": "clinica", "mes": "AAAA-MM", "valores": {...}}`, com números arredondados a 1 casa:

- `atendimentos_mes` = agendamentos `realizado` no mês (inteiro);
- `falta_pct` = `falta ÷ (realizado + falta) × 100` (0 se não houver);
- `ocupacao_pct` = minutos de agendamentos ativos no mês ÷ minutos disponíveis no mês (todas as janelas de todos os profissionais, menos feriados) × 100;
- `clientes_novos_mes` = pacientes cujo **primeiro** `realizado` cai no mês;
- `retorno_atual_pct` = dos retornos com `data` no mês, % cujo paciente tem agendamento `realizado` do mesmo serviço entre `data − 30 dias` e `data + 30 dias` (0 se não houver retornos).

`./atende raiox --dados DIR --mes M --acompanhamento ARQ`: lê `ARQ` (formato do `raio-x-margem/app/painel-motor.js`: `{tipo: "acompanhamento", pacote, cliente, base: {data, valores}, meses: [{mes, valores, obs}]}`), insere ou substitui o mês `M` com `valores` = os da rota acima **mesclados** sobre os valores do mês anterior (ou da base) e `obs: "atende-clinica"`, e grava de volta. Campos que o sistema não mede (ex.: `ticket_medio`, `glosa_pct`) ficam como estavam. Sai com código 0.

## 11. LGPD

- `GET /api/pacientes/{id}/dados` devolve tudo o que há do paciente: `paciente` `{id, nome, telefone, consentimento_marketing, nao_contatar}`, `agendamentos` (mesmo formato da listagem) e `mensagens` = recebidas e enviadas, cada uma `{direcao: "entrada" | "saida", texto, quando}`.
- `DELETE /api/pacientes/{id}`: nome vira `removido`, telefone vira `null`, agendamentos `agendado`/`confirmado` viram `cancelado` (os `realizado`/`falta` ficam), textos de mensagens dele viram `""`. Depois disso, mensagens ao telefone antigo são tratadas como de telefone desconhecido. Números agregados do `/api/raiox` continuam contando os atendimentos passados.

## 12. Fora do v1 (não implementar; portão humano ou próxima versão)

WhatsApp real (Meta Cloud API — pago e exige conta; bibliotecas não oficiais violam os termos), SMS/e-mail, cobrança de sinal por Pix e planos/assinatura (PSP), prontuário, convênio/glosa/TISS, várias clínicas no mesmo servidor, login por usuário, LLM nas respostas (pode entrar depois atrás de uma opção desligada por padrão; os testes nunca a usam), interface EN/ES, deploy público.

## 13. Páginas

- `GET /` → HTML do chat do paciente, com elemento `id="chat"`, que usa `/api/mensagens`.
- `GET /recepcao` → HTML da recepção com elementos `id="agenda"`, `id="fila-humano"` e `id="saida"`; pede o token e usa as rotas [R].
