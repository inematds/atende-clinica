"""Seções 7 e 8: confirmação automática, resposta à confirmação, lista de espera, retorno programado."""
import unicodedata

from conftest import Servidor


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def rodar(api, agora=None):
    st, r = api.post("/api/tarefas/rodar", {"agora": agora} if agora else {})
    assert st == 200, (st, r)
    return r["enviadas"]


def ag_por_id(api, data, ag_id):
    st, r = api.get(f"/api/agendamentos?data={data}")
    return next(a for a in r["agendamentos"] if a["id"] == ag_id)


def test_confirmacao_dentro_de_48h_uma_vez(api):
    p1 = api.paciente("Maria", "41999990001")
    p2 = api.paciente("José", "41999990002")
    _, a = api.agenda(p1, "2026-10-07T09:00", profissional="ana")   # 24 h
    _, b = api.agenda(p2, "2026-10-09T09:00", profissional="ana")   # 72 h
    assert rodar(api) == 1
    [m] = api.saida("confirmacao")
    assert m["agendamento_id"] == a["id"] and m["telefone"] == "+5541999990001" and m["paciente_id"] == p1
    t = norm(m["texto"])
    for trecho in ("avaliacao", "07/10", "09:00", "1", "2"):
        assert trecho in t, trecho
    assert "r$" not in t
    assert rodar(api) == 0
    assert rodar(api, "2026-10-07T10:00") == 1
    assert [x["agendamento_id"] for x in api.saida("confirmacao")] == [a["id"], b["id"]]


def test_responder_1_confirma(api):
    p = api.paciente("Maria", "41999990001")
    _, a = api.agenda(p, "2026-10-07T09:00", profissional="ana")
    rodar(api)
    assert "confirmad" in norm(api.msg("41999990001", "1"))
    assert ag_por_id(api, "2026-10-07", a["id"])["status"] == "confirmado"


def test_responder_2_cancela(api):
    p = api.paciente("Maria", "41999990001")
    _, a = api.agenda(p, "2026-10-07T09:00", profissional="ana")
    rodar(api)
    assert "cancelad" in norm(api.msg("41999990001", "2"))
    assert ag_por_id(api, "2026-10-07", a["id"])["status"] == "cancelado"


def test_lista_de_espera_oferece_e_agenda(api):
    p1 = api.paciente("Maria", "41999990001")
    p2 = api.paciente("José", "41999990002")
    p3 = api.paciente("Rita", "41999990003")
    _, a = api.agenda(p1, "2026-10-07T09:00", profissional="ana")
    assert api.post("/api/espera", {"paciente_id": p2, "servico": "avaliacao", "data": "2026-10-07"})[0] == 201
    assert api.post("/api/espera", {"paciente_id": p3, "servico": "avaliacao", "data": "2026-10-07"})[0] == 201
    api.post(f"/api/agendamentos/{a['id']}/cancelar")
    ofertas = api.saida("espera")
    assert [m["telefone"] for m in ofertas] == ["+5541999990002"]
    assert "09:00" in ofertas[0]["texto"] and "1" in ofertas[0]["texto"]
    assert "agendad" in norm(api.msg("41999990002", "1"))
    st, r = api.get("/api/agendamentos?data=2026-10-07")
    ativos = [x for x in r["agendamentos"] if x["status"] != "cancelado"]
    assert [(x["paciente_id"], x["inicio"], x["profissional"]) for x in ativos] == [(p2, "2026-10-07T09:00", "ana")]


def test_espera_horario_ja_ocupado(api):
    p1 = api.paciente("Maria", "41999990001")
    p2 = api.paciente("José", "41999990002")
    p4 = api.paciente("Ana", "41999990004")
    _, a = api.agenda(p1, "2026-10-07T09:00", profissional="ana")
    api.post("/api/espera", {"paciente_id": p2, "servico": "avaliacao", "data": "2026-10-07"})
    api.post(f"/api/agendamentos/{a['id']}/cancelar")
    assert api.agenda(p4, "2026-10-07T09:00", profissional="ana")[0] == 201
    assert "ocupado" in norm(api.msg("41999990002", "1"))


def test_espera_de_outro_dia_nao_recebe(api):
    p1 = api.paciente("Maria", "41999990001")
    p2 = api.paciente("José", "41999990002")
    _, a = api.agenda(p1, "2026-10-07T09:00", profissional="ana")
    api.post("/api/espera", {"paciente_id": p2, "servico": "avaliacao", "data": "2026-10-08"})
    api.post(f"/api/agendamentos/{a['id']}/cancelar")
    assert api.saida("espera") == []


def test_cancelar_pela_conversa_dispara_espera(api):
    p1 = api.paciente("Maria", "41999990001")
    p2 = api.paciente("José", "41999990002")
    api.agenda(p1, "2026-10-07T09:00", profissional="ana")
    api.post("/api/espera", {"paciente_id": p2, "servico": "avaliacao", "data": "2026-10-07"})
    rodar(api)
    api.msg("41999990001", "2")
    assert [m["telefone"] for m in api.saida("espera")] == ["+5541999990002"]


def test_retorno_programado(api):
    p = api.paciente("Maria", "41999990001")
    _, a = api.agenda(p, "2026-10-07T09:00", servico="limpeza", profissional="ana")
    api.post(f"/api/agendamentos/{a['id']}/presenca", {"compareceu": True})
    # retorno = 07/10/2026 + 180 dias = 05/04/2027; aviso a partir de 29/03/2027
    assert rodar(api, "2027-03-28T09:00") == 0
    assert rodar(api, "2027-03-29T09:00") == 1
    [m] = api.saida("retorno")
    assert m["telefone"] == "+5541999990001" and "limpeza" in norm(m["texto"])
    assert rodar(api, "2027-03-30T09:00") == 0


def test_servico_sem_retorno_nao_gera_aviso(api):
    p = api.paciente("Maria", "41999990001")
    _, a = api.agenda(p, "2026-10-07T09:00", servico="avaliacao", profissional="ana")
    api.post(f"/api/agendamentos/{a['id']}/presenca", {"compareceu": True})
    assert rodar(api, "2027-12-01T09:00") == 0


def test_confirmacao_sobrevive_a_reinicio(dados):
    s = Servidor(dados)
    api = s.subir()
    p = api.paciente("Maria", "41999990001")
    _, a = api.agenda(p, "2026-10-07T09:00", profissional="ana")
    assert rodar(api) == 1
    s.parar()
    s2 = Servidor(dados)
    try:
        api2 = s2.subir()
        assert rodar(api2) == 0
        assert "confirmad" in norm(api2.msg("41999990001", "sim"))
    finally:
        s2.parar()
