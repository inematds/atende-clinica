"""Testes de aceitação caixa-preta do atende-clinica (contrato: docs/ESPECIFICACAO.md).

Sobem `./atende serve --porta 0 --dados <tmp>` com relógio fixo e falam só HTTP/CLI,
então valem para qualquer linguagem de implementação.
"""
import json
import os
import pathlib
import shutil
import signal
import subprocess
import threading
import urllib.error
import urllib.request

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "clinica.json"
TOKEN = "segredo-teste"
AGORA = "2026-10-06T09:00"  # terça-feira


class Cliente:
    def __init__(self, base):
        self.base = base

    def req(self, metodo, rota, corpo=None, token=TOKEN):
        dados = None if corpo is None else json.dumps(corpo).encode()
        r = urllib.request.Request(self.base + rota, data=dados, method=metodo)
        if dados is not None:
            r.add_header("Content-Type", "application/json")
        if token:
            r.add_header("X-Token", token)
        try:
            with urllib.request.urlopen(r, timeout=10) as resp:
                texto = resp.read().decode()
                return resp.status, (json.loads(texto) if texto and "json" in resp.headers.get("Content-Type", "") else texto)
        except urllib.error.HTTPError as e:
            texto = e.read().decode()
            try:
                return e.code, json.loads(texto)
            except ValueError:
                return e.code, texto

    def get(self, rota, **kw):
        return self.req("GET", rota, **kw)

    def post(self, rota, corpo=None, **kw):
        return self.req("POST", rota, {} if corpo is None else corpo, **kw)

    def delete(self, rota, **kw):
        return self.req("DELETE", rota, **kw)

    # atalhos
    def paciente(self, nome="Maria Silva", telefone="(41) 99999-0001", marketing=False):
        st, r = self.post("/api/pacientes", {"nome": nome, "telefone": telefone, "consentimento_marketing": marketing})
        assert st in (200, 201), (st, r)
        return r["id"]

    def agenda(self, paciente_id, inicio, servico="avaliacao", profissional=None):
        corpo = {"paciente_id": paciente_id, "servico": servico, "inicio": inicio}
        if profissional:
            corpo["profissional"] = profissional
        return self.post("/api/agendamentos", corpo)

    def msg(self, telefone, texto):
        st, r = self.post("/api/mensagens", {"telefone": telefone, "texto": texto}, token=None)
        assert st == 200, (st, r)
        return "\n".join(r["respostas"])

    def saida(self, tipo=None):
        st, r = self.get("/api/saida")
        assert st == 200, (st, r)
        return [m for m in r["mensagens"] if tipo is None or m["tipo"] == tipo]


class Servidor:
    def __init__(self, dados, agora=AGORA):
        self.dados = dados
        self.agora = agora
        self.proc = None

    def subir(self):
        exe = RAIZ / "atende"
        if not exe.exists():
            pytest.fail("./atende não existe (ponto de entrada da seção 1 da especificação)")
        env = dict(os.environ, ATENDE_AGORA=self.agora)
        self.proc = subprocess.Popen(
            [str(exe), "serve", "--porta", "0", "--dados", str(self.dados)],
            cwd=RAIZ, env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        )
        linha = {}

        def ler():
            linha["v"] = self.proc.stdout.readline()

        t = threading.Thread(target=ler, daemon=True)
        t.start()
        t.join(15)
        primeira = (linha.get("v") or "").strip()
        if not primeira.startswith("PORTA="):
            self.parar()
            pytest.fail(f"servidor não imprimiu PORTA=<n> na 1ª linha (veio {primeira!r})")
        # drena o resto do stdout para o processo não travar com o pipe cheio
        threading.Thread(target=lambda: [None for _ in self.proc.stdout], daemon=True).start()
        return Cliente(f"http://127.0.0.1:{int(primeira.split('=', 1)[1])}")

    def parar(self):
        if self.proc and self.proc.poll() is None:
            self.proc.send_signal(signal.SIGTERM)
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(5)


@pytest.fixture
def dados(tmp_path):
    d = tmp_path / "dados"
    d.mkdir()
    shutil.copy(FIXTURE, d / "clinica.json")
    return d


@pytest.fixture
def servidor(dados):
    s = Servidor(dados)
    yield s
    s.parar()


@pytest.fixture
def api(servidor):
    return servidor.subir()


def com_conselho(dados, conselho):
    cfg = json.loads((dados / "clinica.json").read_text())
    cfg["conselho"] = conselho
    (dados / "clinica.json").write_text(json.dumps(cfg, ensure_ascii=False))
