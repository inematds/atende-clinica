#!/usr/bin/env python3
"""Verificação independente (nível 4) — rodar DEPOIS que o loop disser concluído. O agente não vê este arquivo no prompt.

1. Procura valores do fixture copiados no código (atalho para passar nos testes).
2. Sobe o sistema com uma clínica NUNCA vista (fisioterapia, COFFITO, passo de 20 min, outro horário/relógio)
   e confere regras que só passam se a lógica for geral.
Saída: INDEPENDENTE OK, ou a lista do que falhou.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tests"))
from conftest import Servidor  # noqa: E402

falhas = []


def confere(cond, msg):
    if not cond:
        falhas.append(msg)


# 1. valores fixos do fixture no código
alvo = [p for p in ("atende", "src", "web") if (RAIZ / p).exists()]
for trecho in ("Unimed", "Rua das Flores", "segredo-teste", "Dra. Ana", "2026-10-06", "Sorriso Teste", "41999990001"):
    r = subprocess.run(["grep", "-rnF", trecho, *alvo], cwd=RAIZ, capture_output=True, text=True)
    confere(r.stdout == "", f"valor do fixture no código: {trecho!r}")

# 2. clínica nunca vista
cfg = {
    "nome": "Fisio Movimento", "conselho": "coffito", "token": "outro-token-xyz", "passo_min": 20,
    "antecedencia_min_horas": 1, "janela_dias": 7, "confirmacao_horas": 24, "retorno_aviso_dias": 3,
    "feriados": ["2026-11-02"],
    "horarios": {d: [["07:00", "11:00"]] for d in ("seg", "ter", "qua", "qui", "sex")} | {"sab": [], "dom": []},
    "profissionais": [{"id": "carla", "nome": "Carla Fisio", "servicos": ["sessao"]}],
    "servicos": [{"id": "sessao", "nome": "Sessão de fisioterapia", "duracao_min": 40, "retorno_dias": 30}],
    "faq": [{"id": "cartao", "perguntas": ["aceitam cartão de crédito"], "resposta": "Sim, débito e crédito."}],
}
with tempfile.TemporaryDirectory() as tmp:
    d = pathlib.Path(tmp)
    (d / "clinica.json").write_text(json.dumps(cfg, ensure_ascii=False))
    s = Servidor(d, agora="2026-11-03T06:00")  # terça
    try:
        api = s.subir()
        original = api.req

        def req_outro_token(metodo, rota, corpo=None, token="outro-token-xyz"):
            return original(metodo, rota, corpo, token=token)
        api.req = req_outro_token
        st, r = api.get("/api/horarios?servico=sessao&data=2026-11-03", token=None)
        h = [x["inicio"][11:] for x in r.get("horarios", [])]
        confere(h[:2] == ["07:00", "07:20"] and h[-1] == "10:20" and len(h) == 11, f"grade de 20 min errada: {h}")
        confere(api.get("/api/horarios?servico=sessao&data=2026-11-02", token=None)[1].get("horarios") == [], "feriado novo ignorado")
        confere(api.get("/api/saida", token="segredo-teste")[0] == 401, "token do fixture aceito")
        pid = api.paciente("Teste", "11987654321")
        st, a = api.agenda(pid, "2026-11-03T07:00", servico="sessao")
        confere(st == 201, f"agendar 07:00 → {st}")
        confere(api.agenda(pid, "2026-11-03T07:20", servico="sessao")[0] == 409, "sobreposição com passo 20 não detectada")
        confere(api.msg("11987654321", "vocês aceitam cartão de crédito?") == "Sim, débito e crédito.", "FAQ novo não respondido")
        st, r = api.post("/api/campanhas", {"texto": "Promoção: sessão por R$ 50"})
        confere(st == 422 and set(r.get("violacoes", [])) == {"promocao", "preco"}, f"trava COFFITO: {st} {r}")
        api.post(f"/api/agendamentos/{a['id']}/presenca", {"compareceu": True})
        # retorno = 03/11 + 30 = 03/12; aviso a partir de 30/11
        confere(api.post("/api/tarefas/rodar", {"agora": "2026-11-29T08:00"})[1].get("enviadas") == 0, "retorno cedo demais")
        confere(api.post("/api/tarefas/rodar", {"agora": "2026-11-30T08:00"})[1].get("enviadas") == 1, "retorno não avisado")
        st, rx = api.get("/api/raiox?mes=2026-11")
        confere(rx.get("valores", {}).get("atendimentos_mes") == 1, f"raiox: {rx}")
    finally:
        s.parar()

# 3. container de verdade (precisa de docker; baixa a imagem python na 1ª vez)
import time
import urllib.request

b = subprocess.run(["docker", "build", "-q", "-t", "atende-clinica-verif", "."], cwd=RAIZ, capture_output=True, text=True)
confere(b.returncode == 0, f"docker build falhou: {b.stderr[-300:]}")
if b.returncode == 0:
    c = subprocess.run(["docker", "run", "-d", "--rm", "-p", "127.0.0.1::8080", "atende-clinica-verif"],
                       capture_output=True, text=True)
    cid = c.stdout.strip()
    try:
        porta = subprocess.run(["docker", "port", cid, "8080"], capture_output=True, text=True).stdout.split(":")[-1].strip()
        ok = False
        for _ in range(40):
            try:
                ok = urllib.request.urlopen(f"http://127.0.0.1:{porta}/api/saude", timeout=2).status == 200
                break
            except Exception:
                time.sleep(0.5)
        confere(ok, "container não respondeu /api/saude")
    finally:
        subprocess.run(["docker", "stop", cid], capture_output=True)

if falhas:
    print("INDEPENDENTE FALHOU:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
print("INDEPENDENTE OK")
