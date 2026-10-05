"""Seções 10 e 11: direitos do titular (LGPD) e exportação para o Painel de Recuperação do Raio-X."""
import json
import subprocess
import unicodedata

from conftest import RAIZ, Servidor

DISPONIVEL_OUT = 22560  # minutos de out/2026: 21 dias úteis (sem 12/10) × 480 + 5 sábados × 240, × 2 profissionais


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def test_dados_e_exclusao(api):
    tel = "41999990001"
    pid = api.paciente("Maria Silva", tel, marketing=True)
    _, a = api.agenda(pid, "2026-10-07T09:00", profissional="ana")
    _, b = api.agenda(pid, "2026-10-08T09:00", profissional="ana")
    api.post(f"/api/agendamentos/{b['id']}/presenca", {"compareceu": True})
    api.msg(tel, "tem estacionamento")
    st, d = api.get(f"/api/pacientes/{pid}/dados")
    assert st == 200
    assert d["paciente"]["nome"] == "Maria Silva" and d["paciente"]["telefone"] == "+5541999990001"
    assert {x["id"] for x in d["agendamentos"]} == {a["id"], b["id"]}
    assert {"entrada", "saida"} <= {m["direcao"] for m in d["mensagens"]}
    assert any("estacionamento" in m["texto"] for m in d["mensagens"])

    assert api.delete(f"/api/pacientes/{pid}")[0] == 204
    st, d = api.get(f"/api/pacientes/{pid}/dados")
    assert d["paciente"]["nome"] == "removido" and d["paciente"]["telefone"] is None
    status = {x["id"]: x["status"] for x in d["agendamentos"]}
    assert status == {a["id"]: "cancelado", b["id"]: "realizado"}
    assert d["mensagens"] and all(m["texto"] == "" for m in d["mensagens"])
    st, r = api.get("/api/raiox?mes=2026-10")
    assert r["valores"]["atendimentos_mes"] == 1
    assert "nome" in norm(api.msg(tel, "quero agendar"))  # telefone virou desconhecido


def montar_mes(dados):
    """Abril: dois atendimentos de limpeza que geram retorno em 05/10 e 06/10. Outubro: o cenário medido."""
    s = Servidor(dados, agora="2026-04-01T09:00")
    api = s.subir()
    p6 = api.paciente("Seis", "41900000006")
    p7 = api.paciente("Sete", "41900000007")
    for pid, dia in ((p6, "2026-04-08"), (p7, "2026-04-09")):
        st, a = api.agenda(pid, f"{dia}T09:00", "limpeza", "ana")
        assert st == 201, a
        api.post(f"/api/agendamentos/{a['id']}/presenca", {"compareceu": True})
    s.parar()

    s = Servidor(dados)  # agora = 06/10/2026 09:00
    api = s.subir()
    p1, p2, p3, p4, p5 = (api.paciente(n, f"4190000000{i}") for i, n in enumerate(["Um", "Dois", "Tres", "Quatro", "Cinco"], 1))

    def marca(pid, inicio, servico, prof, compareceu=None):
        st, a = api.agenda(pid, inicio, servico, prof)
        assert st == 201, (inicio, a)
        if compareceu is not None:
            api.post(f"/api/agendamentos/{a['id']}/presenca", {"compareceu": compareceu})
        return a

    marca(p1, "2026-10-07T08:00", "avaliacao", "ana", True)     # 30 min, novo
    marca(p1, "2026-10-07T08:30", "limpeza", "ana", True)       # 60 min
    marca(p2, "2026-10-07T08:00", "avaliacao", "bruno", False)  # 30 min, falta
    marca(p3, "2026-10-08T08:00", "avaliacao", "bruno", True)   # 30 min, novo
    marca(p4, "2026-10-08T08:00", "avaliacao", "ana")           # 30 min, agendado (ativo)
    c = marca(p5, "2026-10-08T09:00", "avaliacao", "ana")       # cancelado: não conta
    api.post(f"/api/agendamentos/{c['id']}/cancelar")
    marca(p6, "2026-10-07T10:00", "limpeza", "ana", True)       # 60 min, cumpre o retorno de 05/10
    return s, api


def test_raiox_numeros_do_mes(dados):
    s, api = montar_mes(dados)
    try:
        st, r = api.get("/api/raiox?mes=2026-10")
        assert st == 200 and r["pacote"] == "clinica" and r["mes"] == "2026-10"
        v = r["valores"]
        assert v["atendimentos_mes"] == 4
        assert v["falta_pct"] == 20.0
        assert v["clientes_novos_mes"] == 2
        assert v["retorno_atual_pct"] == 50.0
        assert abs(v["ocupacao_pct"] - 240 / DISPONIVEL_OUT * 100) <= 0.06
        st, abr = api.get("/api/raiox?mes=2026-04")
        assert abr["valores"]["atendimentos_mes"] == 2 and abr["valores"]["clientes_novos_mes"] == 2
        assert abr["valores"]["falta_pct"] == 0
    finally:
        s.parar()


def test_cli_grava_mes_no_acompanhamento_do_painel(dados, tmp_path):
    s, _ = montar_mes(dados)
    s.parar()
    arq = tmp_path / "acompanhamento.json"
    arq.write_text(json.dumps({
        "tipo": "acompanhamento", "pacote": "clinica", "cliente": "Clínica Sorriso",
        "base": {"data": "2026-09-01", "valores": {"falta_pct": 18, "ticket_medio": 250, "atendimentos_mes": 400}},
        "meses": [],
    }))
    cmd = [str(RAIZ / "atende"), "raiox", "--dados", str(dados), "--mes", "2026-10", "--acompanhamento", str(arq)]
    for _ in range(2):  # rodar duas vezes substitui o mês, não duplica
        assert subprocess.run(cmd, cwd=RAIZ, capture_output=True, timeout=30).returncode == 0
    acomp = json.loads(arq.read_text())
    assert acomp["tipo"] == "acompanhamento" and acomp["base"]["valores"]["falta_pct"] == 18
    [m] = acomp["meses"]
    assert m["mes"] == "2026-10" and m["obs"] == "atende-clinica"
    assert m["valores"]["ticket_medio"] == 250          # mesclado da base
    assert m["valores"]["falta_pct"] == 20.0            # medido
    assert m["valores"]["atendimentos_mes"] == 4
