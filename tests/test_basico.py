"""Seções 1, 4, 5 (saúde/serviços), 13 e persistência."""
from conftest import RAIZ, Servidor


def test_saude_traz_versao_do_arquivo(api):
    st, r = api.get("/api/saude", token=None)
    assert st == 200
    assert r["ok"] is True
    assert r["versao"] == (RAIZ / "VERSION").read_text().strip()


def test_servicos_na_ordem_da_config(api):
    st, r = api.get("/api/servicos", token=None)
    assert st == 200
    assert [s["id"] for s in r["servicos"]] == ["avaliacao", "limpeza", "canal"]
    assert r["servicos"][1]["duracao_min"] == 60


def test_rotas_da_recepcao_exigem_token(api):
    for metodo, rota in [("GET", "/api/saida"), ("GET", "/api/agendamentos?data=2026-10-07"),
                         ("POST", "/api/pacientes"), ("GET", "/api/atendimento-humano"),
                         ("GET", "/api/raiox?mes=2026-10"), ("POST", "/api/campanhas")]:
        corpo = {} if metodo == "POST" else None
        assert api.req(metodo, rota, corpo, token=None)[0] == 401, rota
        assert api.req(metodo, rota, corpo, token="errado")[0] == 401, rota


def test_rotas_publicas_sem_token(api):
    assert api.get("/api/horarios?servico=avaliacao&data=2026-10-07", token=None)[0] == 200
    assert api.post("/api/mensagens", {"telefone": "41911112222", "texto": "oi"}, token=None)[0] == 200


def test_paginas(api):
    st, html = api.get("/", token=None)
    assert st == 200 and 'id="chat"' in html
    st, html = api.get("/recepcao", token=None)
    assert st == 200
    for el in ('id="agenda"', 'id="fila-humano"', 'id="saida"'):
        assert el in html


def test_estado_persiste_ao_reiniciar(dados):
    s = Servidor(dados)
    api = s.subir()
    pid = api.paciente()
    st, ag = api.agenda(pid, "2026-10-07T09:00", profissional="ana")
    assert st == 201
    s.parar()
    s2 = Servidor(dados)
    try:
        api2 = s2.subir()
        st, r = api2.get("/api/agendamentos?data=2026-10-07")
        assert st == 200
        assert [a["id"] for a in r["agendamentos"]] == [ag["id"]]
        assert api2.agenda(pid, "2026-10-07T09:00", profissional="ana")[0] == 409
    finally:
        s2.parar()


def test_cria_clinica_json_do_exemplo_se_faltar(tmp_path):
    d = tmp_path / "vazio"
    d.mkdir()
    s = Servidor(d)
    try:
        api = s.subir()
        assert api.get("/api/saude", token=None)[0] == 200
        assert (d / "clinica.json").exists()
    finally:
        s.parar()
