"""Seção 6: conversa — FAQ, não entendi, humano, emergência, parar, agendamento pelo chat."""
import unicodedata

TEL = "41988887777"
TEL_N = "+5541988887777"


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def fila(api):
    st, r = api.get("/api/atendimento-humano")
    assert st == 200
    return r["fila"]


def test_faq_responde_exatamente(api):
    assert api.msg(TEL, "Oi, vcs aceitam convenio?") == "Atendemos Unimed Odonto, Amil Dental e particular."
    assert api.msg(TEL, "Onde fica a clínica de vocês?") == "Rua das Flores, 100, sala 5, Batel, Curitiba."
    assert api.msg(TEL, "tem estacionamento aí?") == "Temos convênio com o estacionamento ao lado (1 hora grátis)."


def test_nao_entendi_e_depois_passa_para_humano(api):
    r = norm(api.msg(TEL, "posso tomar ibuprofeno depois da extração?"))
    assert "nao entendi" in r and "atendente" in r
    assert fila(api) == []
    api.msg(TEL, "e dipirona serve?")
    f = fila(api)
    assert len(f) == 1 and f[0]["telefone"] == TEL_N and f[0]["prioridade"] == "normal"


def test_pedido_de_atendente(api):
    assert "atendente" in norm(api.msg(TEL, "quero falar com um atendente"))
    f = fila(api)
    assert len(f) == 1 and f[0]["prioridade"] == "normal"


def test_emergencia(api):
    r = norm(api.msg(TEL, "Estou com DOR NO PEITO e falta de ar"))
    assert "192" in r and "pronto-socorro" in r
    f = fila(api)
    assert len(f) == 1 and f[0]["prioridade"] == "alta" and f[0]["telefone"] == TEL_N


def test_emergencia_vence_agendamento(api):
    r = norm(api.msg(TEL, "quero marcar consulta, estou sangrando muito"))
    assert "192" in r
    st, lista = api.get("/api/agendamentos?data=2026-10-06")
    assert lista["agendamentos"] == []


def test_agendamento_pelo_chat_paciente_novo(api):
    assert "nome" in norm(api.msg(TEL, "quero marcar uma consulta"))
    r = api.msg(TEL, "João Souza")
    assert "1 - Avaliação" in r and "2 - Limpeza" in r and "3 - Tratamento de canal" in r
    r = api.msg(TEL, "1")
    assert "1) 06/10 11:00 com Dra. Ana" in r
    assert "2) 06/10 11:00 com Dr. Bruno" in r
    assert "3) 06/10 11:30 com Dra. Ana" in r
    r = norm(api.msg(TEL, "2"))
    assert "agendad" in r and "06/10" in r and "11:00" in r
    st, lista = api.get("/api/agendamentos?data=2026-10-06")
    [a] = lista["agendamentos"]
    assert (a["telefone"], a["servico"], a["profissional"], a["inicio"], a["status"]) == \
        (TEL_N, "avaliacao", "bruno", "2026-10-06T11:00", "agendado")
    st, d = api.get(f"/api/pacientes/{a['paciente_id']}/dados")
    assert d["paciente"]["nome"] == "João Souza"
    assert d["paciente"]["consentimento_marketing"] is False


def test_agendamento_pelo_chat_paciente_conhecido_e_opcao_invalida(api):
    api.paciente("Maria", TEL)
    r = api.msg(TEL, "quero agendar")
    assert "1 - Avaliação" in r and "nome" not in norm(r)
    r = api.msg(TEL, "2")
    assert "1) 06/10 11:00 com Dra. Ana" in r
    r = api.msg(TEL, "9")
    assert "1) 06/10 11:00 com Dra. Ana" in r  # repete as opções
    assert "agendad" in norm(api.msg(TEL, "1"))
    st, lista = api.get("/api/agendamentos?data=2026-10-06")
    [a] = lista["agendamentos"]
    assert (a["servico"], a["profissional"], a["inicio"]) == ("limpeza", "ana", "2026-10-06T11:00")


def test_chat_oferece_proximos_dias_quando_hoje_lota(api):
    pid = api.paciente("Ocupa", "41900000001")
    for prof in ("ana", "bruno"):
        for h in ("11:00", "11:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30"):
            assert api.agenda(pid, f"2026-10-06T{h}", "avaliacao", prof)[0] == 201
    api.msg(TEL, "quero agendar")
    api.msg(TEL, "Pedro")
    r = api.msg(TEL, "1")
    assert "1) 07/10 08:00 com Dra. Ana" in r and "3) 07/10 08:30 com Dra. Ana" in r


def test_cancelar_sai_do_fluxo(api):
    api.paciente("Maria", TEL)
    api.msg(TEL, "quero agendar")
    api.msg(TEL, "cancelar")
    assert api.msg(TEL, "tem estacionamento") == "Temos convênio com o estacionamento ao lado (1 hora grátis)."


def test_parar_bloqueia_contato(api):
    pid = api.paciente("Maria", TEL)
    api.agenda(pid, "2026-10-07T09:00", profissional="ana")
    assert "nao vai mais receber" in norm(api.msg(TEL, "PARAR"))
    st, r = api.post("/api/tarefas/rodar", {})
    assert st == 200 and r["enviadas"] == 0
    assert api.saida() == []
    st, d = api.get(f"/api/pacientes/{pid}/dados")
    assert d["paciente"]["nao_contatar"] is True
