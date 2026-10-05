"""Seções 3 e 5: horários, agendamento, conflito, cancelamento, remarcação, pacientes. Agora = ter 06/10/2026 09:00."""
import threading


def horarios(api, servico, data, profissional=None):
    rota = f"/api/horarios?servico={servico}&data={data}"
    if profissional:
        rota += f"&profissional={profissional}"
    st, r = api.get(rota, token=None)
    assert st == 200, (st, r)
    return [(h["inicio"], h["profissional"]) for h in r["horarios"]]


def test_horarios_respeitam_antecedencia_e_ordem(api):
    h = horarios(api, "avaliacao", "2026-10-06")
    assert h[:3] == [("2026-10-06T11:00", "ana"), ("2026-10-06T11:00", "bruno"), ("2026-10-06T11:30", "ana")]
    assert len(h) == 20  # manhã 11:00 e 11:30 + tarde 14:00..17:30, dois profissionais


def test_horarios_cabem_na_janela(api):
    h = horarios(api, "limpeza", "2026-10-06")
    assert [i for i, _ in h] == ["2026-10-06T11:00"] + [f"2026-10-06T{x}" for x in
                                                         ("14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00")]
    assert {p for _, p in h} == {"ana"}


def test_horarios_dia_inteiro_por_profissional(api):
    h = horarios(api, "avaliacao", "2026-10-07", "ana")
    assert len(h) == 16
    assert h[0] == ("2026-10-07T08:00", "ana") and h[-1] == ("2026-10-07T17:30", "ana")
    assert ("2026-10-07T12:00", "ana") not in h


def test_sem_horario_em_feriado_domingo_e_sabado_reduzido(api):
    assert horarios(api, "avaliacao", "2026-10-12") == []
    assert horarios(api, "avaliacao", "2026-10-11") == []
    assert len(horarios(api, "avaliacao", "2026-10-10")) == 16


def test_servico_inexistente_404(api):
    assert api.get("/api/horarios?servico=xyz&data=2026-10-07", token=None)[0] == 404


def test_agendar_e_listar(api):
    pid = api.paciente()
    st, r = api.agenda(pid, "2026-10-07T09:00", servico="limpeza", profissional="ana")
    assert st == 201
    assert r["status"] == "agendado" and r["inicio"] == "2026-10-07T09:00" and r["fim"] == "2026-10-07T10:00"
    st, lista = api.get("/api/agendamentos?data=2026-10-07")
    a = lista["agendamentos"][0]
    assert (a["paciente_id"], a["telefone"], a["servico"], a["profissional"]) == (pid, "+5541999990001", "limpeza", "ana")
    assert ("2026-10-07T09:00", "ana") not in horarios(api, "avaliacao", "2026-10-07")
    assert ("2026-10-07T09:30", "ana") not in horarios(api, "avaliacao", "2026-10-07")


def test_invalidos_422(api):
    pid = api.paciente()
    for inicio, servico, prof in [
        ("2026-10-07T12:00", "avaliacao", "ana"),   # almoço
        ("2026-10-07T09:15", "avaliacao", "ana"),   # fora da grade
        ("2026-10-07T11:30", "limpeza", "ana"),     # não cabe na janela
        ("2026-10-06T10:00", "avaliacao", "ana"),   # antes da antecedência
        ("2026-10-12T09:00", "avaliacao", "ana"),   # feriado
        ("2026-10-07T09:00", "limpeza", "bruno"),   # profissional não faz
    ]:
        assert api.agenda(pid, inicio, servico, prof)[0] == 422, (inicio, servico, prof)


def test_inexistentes_404(api):
    pid = api.paciente()
    assert api.agenda(9999, "2026-10-07T09:00")[0] == 404
    assert api.agenda(pid, "2026-10-07T09:00", servico="xyz")[0] == 404


def test_sobreposicao_409(api):
    pid = api.paciente()
    assert api.agenda(pid, "2026-10-07T09:00", "avaliacao", "ana")[0] == 201
    assert api.agenda(pid, "2026-10-07T08:30", "limpeza", "ana")[0] == 409
    assert api.agenda(pid, "2026-10-07T09:00", "avaliacao", "bruno")[0] == 201


def test_sem_profissional_pega_o_primeiro_livre(api):
    pid = api.paciente()
    st1, a1 = api.agenda(pid, "2026-10-07T09:00")
    st2, a2 = api.agenda(pid, "2026-10-07T09:00")
    st3, _ = api.agenda(pid, "2026-10-07T09:00")
    assert (st1, st2, st3) == (201, 201, 409)
    assert (a1["profissional"], a2["profissional"]) == ("ana", "bruno")


def test_concorrencia_um_so_vence(api):
    pid = api.paciente()
    codigos = []

    def tenta():
        codigos.append(api.agenda(pid, "2026-10-08T10:00", "avaliacao", "ana")[0])

    ts = [threading.Thread(target=tenta) for _ in range(10)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert sorted(codigos) == [201] + [409] * 9


def test_cancelar_libera(api):
    pid = api.paciente()
    _, a = api.agenda(pid, "2026-10-07T09:00", "avaliacao", "ana")
    st, r = api.post(f"/api/agendamentos/{a['id']}/cancelar")
    assert st == 200 and r["status"] == "cancelado"
    assert ("2026-10-07T09:00", "ana") in horarios(api, "avaliacao", "2026-10-07")
    assert api.agenda(pid, "2026-10-07T09:00", "avaliacao", "ana")[0] == 201


def test_remarcar(api):
    pid = api.paciente()
    _, a = api.agenda(pid, "2026-10-07T09:00", "avaliacao", "ana")
    _, b = api.agenda(pid, "2026-10-07T10:00", "avaliacao", "ana")
    assert api.post(f"/api/agendamentos/{a['id']}/remarcar", {"inicio": "2026-10-07T10:00"})[0] == 409
    assert api.post(f"/api/agendamentos/{a['id']}/remarcar", {"inicio": "2026-10-07T12:00"})[0] == 422
    st, r = api.post(f"/api/agendamentos/{a['id']}/remarcar", {"inicio": "2026-10-08T15:00"})
    assert st == 200 and r["id"] == a["id"] and r["inicio"] == "2026-10-08T15:00" and r["status"] == "agendado"
    assert ("2026-10-07T09:00", "ana") in horarios(api, "avaliacao", "2026-10-07")


def test_presenca(api):
    pid = api.paciente()
    _, a = api.agenda(pid, "2026-10-07T09:00", profissional="ana")
    _, b = api.agenda(pid, "2026-10-07T10:00", profissional="ana")
    assert api.post(f"/api/agendamentos/{a['id']}/presenca", {"compareceu": True})[1]["status"] == "realizado"
    assert api.post(f"/api/agendamentos/{b['id']}/presenca", {"compareceu": False})[1]["status"] == "falta"
    # falta continua ocupando o horário (ativo)
    assert ("2026-10-07T10:00", "ana") not in horarios(api, "avaliacao", "2026-10-07")


def test_telefone_normalizado_e_duplicado(api):
    st, r = api.post("/api/pacientes", {"nome": "A", "telefone": "(41) 99999-0001"})
    assert st == 201
    st2, r2 = api.post("/api/pacientes", {"nome": "A", "telefone": "+55 41 99999 0001"})
    assert st2 == 200 and r2["id"] == r["id"]
    st3, r3 = api.post("/api/pacientes", {"nome": "B", "telefone": "41 3333-4444"})
    assert st3 == 201 and r3["id"] != r["id"]
    st, dados = api.get(f"/api/pacientes/{r3['id']}/dados")
    assert dados["paciente"]["telefone"] == "+554133334444"
    for ruim in ("123", "abc", "+55 41 9999"):
        assert api.post("/api/pacientes", {"nome": "C", "telefone": ruim})[0] == 400, ruim
