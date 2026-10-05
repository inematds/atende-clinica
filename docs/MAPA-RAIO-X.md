# Como o Raio-X de Margem alimenta este projeto

Fonte: `~/projetos/raio-x-margem` (pacote `setores/clinica.js`, receita `docs/modulos/servicos-agenda.md`, pesquisa `docs/setores/servicos-pesquisa-2026-10.md`).

## Vazamentos da clínica × o que o atende-clinica ataca

| Vazamento (id no Raio-X) | Peça no v1 | Seção da spec |
|---|---|---|
| `faltas` — falta sem aviso (nº 1: bem gerida 5–12 %, média ~25 %) | confirmação automática 48 h + "1/2" + lista de espera | 7, 8 |
| retorno no prazo (`retorno_atual_pct`) | retorno programado (`retorno_dias` por serviço) | 8 |
| `whatsapp_manual` — recepção marcando à mão (`horas_agenda_manual_semana`) | agendamento pelo chat + FAQ + fila humana | 6 |
| `sem_agenda_online` | horários públicos + chat web | 5, 6, 13 |
| `fidelidade` / plano | **fora do v1** (precisa de PSP) | 12 |
| `glosa`, `orcamentos` | **fora** — não é atendimento, é faturamento | 12 |

## Regras que viraram trava testável

- **LGPD art. 11:** lembrete e retorno = tutela da saúde (sem consentimento de marketing); campanha = consentimento específico. "PARAR" bloqueia tudo. Exportar e anonimizar (art. 18).
- **Conselhos:** tabela da seção 9 (CFM 2.336/2023, CFO 118/2012 + 196/2019 + 271/2025, COFFITO 424/2013). Odonto: sem preço, parcelamento, grátis, sorteio, antes-e-depois em campanha.
- **Bot não inventa:** fora do FAQ → "não entendi" → humano. Emergência → 192.

## Volta para o Raio-X

`GET /api/raiox?mes=` e `./atende raiox --acompanhamento` produzem os campos do pacote clínica (`atendimentos_mes`, `falta_pct`, `ocupacao_pct`, `clientes_novos_mes`, `retorno_atual_pct`) no formato do `app/painel.html` (Painel de Recuperação). Ciclo comercial: Raio-X mede o "antes" → atende-clinica implanta a receita "Agenda cheia" → o painel mostra o "depois" todo mês, com número tirado da agenda real.
