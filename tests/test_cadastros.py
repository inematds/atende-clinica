"""Seções 14, 15 e 16: cadastros, gestão de agenda e banco de dados."""
import subprocess

from conftest import RAIZ, Servidor


def horarios(api, servico, data, profissional=None):
    rota = f"/api/horarios?servico={servico}&data={data}" + (f"&profissional={profissional}" if profissional else "")
    st, r = api.get(rota, token=None)
    assert st == 200, (st, r)
    return [(h["inicio"], h["profissional"]) for h in r["horarios"]]


def test_profissional_novo_com_horario_proprio(api):
    st, r = api.post("/api/profissionais", {
        "id": "carlos", "nome": "Dr. Carlos", "servicos": ["avaliacao"], "registro": "CRO-PR 12345",
        "horarios": {"seg": [], "ter": [], "qua": [["13:00", "15:00"]], "qui": [], "sex": [], "sab": [], "dom": []}})
    assert st == 201, r
    h = [i for i, p in horarios(api, "avaliacao", "2026-10-07") if p == "carlos"]
    assert h == ["2026-10-07T13:00", "2026-10-07T13:30", "2026-10-07T14:00", "2026-10-07T14:30"]
    assert [i for i, p in horarios(api, "avaliacao", "2026-10-08") if p == "carlos"] == []
    st, lista = api.get("/api/profissionais")
    c = next(p for p in lista["profissionais"] if p["id"] == "carlos")
    assert c["registro"] == "CRO-PR 12345" and c["ativo"] is True
    assert next(p for p in lista["profissionais"] if p["id"] == "ana")["horarios"] is None


def test_profissional_validacoes(api):
    assert api.post("/api/profissionais", {"id": "ana", "nome": "X", "servicos": ["avaliacao"]})[0] == 409
    assert api.post("/api/profissionais", {"id": "z", "nome": "Z", "servicos": ["xyz"]})[0] == 422
    assert api.req("PUT", "/api/profissionais/naoexiste", {"nome": "Q"})[0] == 404


def test_editar_e_desativar_profissional(api):
    st, r = api.req("PUT", "/api/profissionais/bruno", {"servicos": ["avaliacao", "canal", "limpeza"]})
    assert st == 200 and "limpeza" in r["servicos"]
    assert {p for _, p in horarios(api, "limpeza", "2026-10-07")} == {"ana", "bruno"}
    pid = api.paciente()
    _, a = api.agenda(pid, "2026-10-08T09:00", "avaliacao", "bruno")
    st, r = api.delete("/api/profissionais/bruno")
    assert st == 200 and r["ativo"] is False
    assert {p for _, p in horarios(api, "avaliacao", "2026-10-09")} == {"ana"}
    assert api.agenda(pid, "2026-10-09T09:00", "avaliacao", "bruno")[0] == 422
    st, lista = api.get("/api/agendamentos?data=2026-10-08")
    assert [x["id"] for x in lista["agendamentos"]] == [a["id"]]


def test_servicos_crud(api):
    assert api.post("/api/servicos", {"id": "clareamento", "nome": "Clareamento", "duracao_min": 90, "retorno_dias": None})[0] == 201
    assert api.post("/api/servicos", {"id": "limpeza", "nome": "X", "duracao_min": 30})[0] == 409
    api.req("PUT", "/api/profissionais/ana", {"servicos": ["avaliacao", "limpeza", "clareamento"]})
    assert ("2026-10-07T08:00", "ana") in horarios(api, "clareamento", "2026-10-07")
    assert api.req("PUT", "/api/servicos/clareamento", {"duracao_min": 120})[0] == 200
    assert ("2026-10-07T10:30", "ana") not in horarios(api, "clareamento", "2026-10-07")  # 10:30+120 > 12:00
    assert ("2026-10-07T10:00", "ana") in horarios(api, "clareamento", "2026-10-07")
    assert api.delete("/api/servicos/canal")[0] == 200
    st, r = api.get("/api/servicos", token=None)
    assert [s["id"] for s in r["servicos"]] == ["avaliacao", "limpeza", "clareamento"]


def test_chat_usa_servicos_ativos(api):
    api.delete("/api/servicos/canal")
    api.paciente("Maria", "41988887777")
    r = api.msg("41988887777", "quero agendar")
    assert "1 - Avaliação" in r and "Tratamento de canal" not in r


def test_pacientes_busca_e_edicao(api):
    p1 = api.paciente("José Antônio Souza", "41999990001")
    p2 = api.paciente("Maria Lima", "41999990002")
    st, r = api.get("/api/pacientes?busca=antonio")
    assert st == 200 and [p["id"] for p in r["pacientes"]] == [p1]
    st, r = api.get("/api/pacientes?busca=990002")
    assert [p["id"] for p in r["pacientes"]] == [p2]
    assert len(api.get("/api/pacientes")[1]["pacientes"]) == 2
    st, r = api.req("PUT", f"/api/pacientes/{p2}", {"email": "maria@exemplo.com", "nascimento": "1980-05-02",
                                                   "consentimento_marketing": True})
    assert st == 200 and r["email"] == "maria@exemplo.com" and r["consentimento_marketing"] is True
    assert api.req("PUT", f"/api/pacientes/{p2}", {"telefone": "41999990001"})[0] == 409
    assert api.req("PUT", f"/api/pacientes/{p2}", {"telefone": "12"})[0] == 400


def test_faq_crud_vale_na_hora(api):
    st, r = api.post("/api/faq", {"perguntas": ["atendem criança"], "resposta": "Sim, a partir de 3 anos."})
    assert st == 201
    assert api.msg("41988887777", "vocês atendem criança?") == "Sim, a partir de 3 anos."
    assert api.delete(f"/api/faq/{r['id']}")[0] == 204
    assert api.msg("41988887777", "vocês atendem criança?") != "Sim, a partir de 3 anos."
    ids = [f["id"] for f in api.get("/api/faq")[1]["faq"]]
    assert "convenios" in ids and r["id"] not in ids


def test_bloqueio_tira_horarios_e_avisa_conflito(api):
    pid = api.paciente()
    _, a = api.agenda(pid, "2026-10-08T09:00", "avaliacao", "ana")
    st, r = api.post("/api/bloqueios", {"profissional": "ana", "inicio": "2026-10-08T08:00",
                                         "fim": "2026-10-09T00:00", "motivo": "congresso"})
    assert st == 201 and r["conflitos"] == [a["id"]]
    assert [p for _, p in horarios(api, "avaliacao", "2026-10-08")] and \
        {p for _, p in horarios(api, "avaliacao", "2026-10-08")} == {"bruno"}
    assert api.agenda(pid, "2026-10-08T15:00", "avaliacao", "ana")[0] == 422
    st, lista = api.get("/api/bloqueios?profissional=ana")
    assert [b["motivo"] for b in lista["bloqueios"]] == ["congresso"]
    assert api.delete(f"/api/bloqueios/{r['id']}")[0] == 204
    assert ("2026-10-08T15:00", "ana") in horarios(api, "avaliacao", "2026-10-08")


def test_agenda_por_periodo_e_profissional(api):
    pid = api.paciente()
    api.agenda(pid, "2026-10-09T09:00", "avaliacao", "ana")
    api.agenda(pid, "2026-10-07T09:00", "avaliacao", "bruno")
    api.agenda(pid, "2026-10-08T09:00", "avaliacao", "ana")
    api.agenda(pid, "2026-10-13T09:00", "avaliacao", "ana")
    st, r = api.get("/api/agendamentos?de=2026-10-07&ate=2026-10-09")
    assert [a["inicio"] for a in r["agendamentos"]] == ["2026-10-07T09:00", "2026-10-08T09:00", "2026-10-09T09:00"]
    st, r = api.get("/api/agendamentos?de=2026-10-07&ate=2026-10-13&profissional=ana")
    assert [a["inicio"][:10] for a in r["agendamentos"]] == ["2026-10-08", "2026-10-09", "2026-10-13"]


def test_semente_so_na_primeira_vez(dados):
    s = Servidor(dados)
    api = s.subir()
    api.post("/api/servicos", {"id": "raiox", "nome": "Raio-X", "duracao_min": 30})
    s.parar()
    s2 = Servidor(dados)
    try:
        api2 = s2.subir()
        ids = [x["id"] for x in api2.get("/api/servicos", token=None)[1]["servicos"]]
        assert ids == ["avaliacao", "limpeza", "canal", "raiox"]
    finally:
        s2.parar()


def test_backup_e_restaurar(dados, tmp_path):
    s = Servidor(dados)
    api = s.subir()
    pid = api.paciente("Guardada", "41999990009")
    api.agenda(pid, "2026-10-07T09:00", "avaliacao", "ana")
    arq = tmp_path / "copia.bak"
    r = subprocess.run([str(RAIZ / "atende"), "backup", "--dados", str(dados), "--saida", str(arq)],
                       cwd=RAIZ, capture_output=True, timeout=30)
    assert r.returncode == 0 and arq.exists() and arq.stat().st_size > 0
    api.delete(f"/api/pacientes/{pid}")
    api.paciente("Depois do backup", "41999990010")
    s.parar()
    r = subprocess.run([str(RAIZ / "atende"), "restaurar", "--dados", str(dados), "--entrada", str(arq)],
                       cwd=RAIZ, capture_output=True, timeout=30)
    assert r.returncode == 0
    s2 = Servidor(dados)
    try:
        api2 = s2.subir()
        nomes = [p["nome"] for p in api2.get("/api/pacientes")[1]["pacientes"]]
        assert nomes == ["Guardada"]
        assert len(api2.get("/api/agendamentos?data=2026-10-07")[1]["agendamentos"]) == 1
    finally:
        s2.parar()
