"""Seções 17 e 18: WhatsApp pela Evolution API e atendimento interno pelo Telegram (contra servidor falso local)."""
import json
import time
import unicodedata
import urllib.error
import urllib.request

from conftest import CHAT_EQUIPE, SEGREDO_TG, SEGREDO_WH, esperar

TEL = "41988887777"
NUM = "5541988887777"
ESTAC = "Temos convênio com o estacionamento ao lado (1 hora grátis)."


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


_ids = iter(range(1, 10 ** 6))


def evo(api, texto=None, numero=NUM, msg_id=None, from_me=False, sufixo="@s.whatsapp.net",
        evento="messages.upsert", message=None):
    if message is None:
        message = {"conversation": texto}
    corpo = {"event": evento, "instance": "clinica",
             "data": {"key": {"remoteJid": numero + sufixo, "fromMe": from_me, "id": msg_id or f"M{next(_ids)}"},
                      "pushName": "Paciente", "message": message, "messageType": "conversation"}}
    st, _ = api.post(f"/webhook/evolution/{SEGREDO_WH}", corpo, token=None)
    assert st == 200
    return corpo


def tg(api, texto, reply_to=None, chat=CHAT_EQUIPE, segredo=SEGREDO_TG):
    """Entrega um update do Telegram no webhook; devolve o status HTTP."""
    msg = {"message_id": next(_ids), "chat": {"id": chat}, "from": {"id": 7, "first_name": "Rita"}, "text": texto}
    if reply_to:
        msg["reply_to_message"] = {"message_id": reply_to}
    q = urllib.request.Request(api.base + "/webhook/telegram", method="POST",
                               data=json.dumps({"update_id": next(_ids), "message": msg}).encode(),
                               headers={"Content-Type": "application/json", "X-Telegram-Bot-Api-Secret-Token": segredo})
    try:
        with urllib.request.urlopen(q, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code


def textos_whats(externo):
    return [p["json"]["text"] for p in externo.whats()]


def abre_atendimento(api, externo):
    api.msg(TEL, "quero falar com um atendente")
    assert esperar(lambda: len(externo.telegram()) >= 1)
    [at] = api.get("/api/atendimento-humano")[1]["fila"]
    abertura = next(p for p in externo.telegram() if f"#{at['id']}" in p["json"]["text"])
    return at, abertura


# --- WhatsApp (Evolution) ---------------------------------------------------------------

def test_webhook_evolution_segredo_errado(api_int):
    assert api_int.post("/webhook/evolution/errado", {"event": "messages.upsert"}, token=None)[0] == 404


def test_whatsapp_responde_pela_evolution(api_int, externo):
    evo(api_int, "tem estacionamento?")
    assert esperar(lambda: len(externo.whats()) == 1)
    [p] = externo.whats()
    assert p["json"]["number"] == NUM and p["json"]["text"] == ESTAC
    assert p["headers"].get("apikey") == "chave-evo"


def test_whatsapp_ignora_o_que_nao_e_do_paciente(api_int, externo):
    evo(api_int, "tem estacionamento?", msg_id="DUP1")
    evo(api_int, "tem estacionamento?", msg_id="DUP1")            # reenvio da Evolution
    evo(api_int, "tem estacionamento?", from_me=True)              # mensagem da própria clínica
    evo(api_int, "tem estacionamento?", numero="1203630", sufixo="@g.us")  # grupo
    evo(api_int, "tem estacionamento?", evento="connection.update")
    time.sleep(0.8)
    assert textos_whats(externo) == [ESTAC]


def test_whatsapp_sem_texto(api_int, externo):
    evo(api_int, message={"audioMessage": {"seconds": 5}})
    assert esperar(lambda: textos_whats(externo) == ["Por enquanto só consigo ler mensagens de texto."])


def test_whatsapp_agenda_e_avisa_equipe(api_int, externo):
    def tem(trecho):
        return esperar(lambda: any(trecho in norm(t) for t in textos_whats(externo)))

    evo(api_int, "quero marcar uma consulta")
    assert tem("nome")
    evo(api_int, "João Souza")
    assert tem("1 - avaliacao")
    evo(api_int, "1")
    assert tem("2) 06/10 11:00 com dr. bruno")
    evo(api_int, "2")
    assert tem("agendad")
    st, lista = api_int.get("/api/agendamentos?data=2026-10-06")
    [a] = lista["agendamentos"]
    assert (a["telefone"], a["profissional"], a["inicio"]) == ("+" + NUM, "bruno", "2026-10-06T11:00")
    assert esperar(lambda: any("Novo agendamento: 06/10 11:00 João Souza — Avaliação com Dr. Bruno" in p["json"]["text"]
                               for p in externo.telegram()))
    assert all(p["json"]["chat_id"] in (CHAT_EQUIPE, str(CHAT_EQUIPE)) for p in externo.telegram())


def test_saida_pela_evolution_com_reenvio(api_int, externo):
    pid = api_int.paciente("Maria", TEL)
    api_int.agenda(pid, "2026-10-07T09:00", profissional="ana")
    externo.falhas = 1
    st, r = api_int.post("/api/tarefas/rodar", {})
    assert r["enviadas"] == 1
    [m] = api_int.saida("confirmacao")
    assert m["status"] == "pendente"
    st, r = api_int.post("/api/tarefas/rodar", {})
    assert r["enviadas"] == 0 and r["reenviadas"] == 1
    assert api_int.saida("confirmacao")[0]["status"] == "enviado"
    [p] = externo.whats()
    assert p["json"]["number"] == NUM and "07/10" in p["json"]["text"]


def test_sem_evolution_status_simulado(api):
    pid = api.paciente("Maria", TEL)
    api.agenda(pid, "2026-10-07T09:00", profissional="ana")
    api.post("/api/tarefas/rodar", {})
    assert api.saida("confirmacao")[0]["status"] == "simulado"


# --- Telegram (equipe) ------------------------------------------------------------------

def test_abertura_vai_ao_grupo(api_int, externo):
    at, abertura = abre_atendimento(api_int, externo)
    t = abertura["json"]["text"]
    assert TEL in t.replace(" ", "").replace("-", "") and f"#{at['id']}" in t
    assert str(abertura["json"]["chat_id"]) == str(CHAT_EQUIPE)
    assert at["status"] == "aberto"


def test_emergencia_marca_alta(api_int, externo):
    api_int.msg(TEL, "meu pai desmaiou aqui")
    assert esperar(lambda: any("ALTA" in p["json"]["text"] for p in externo.telegram()))


def test_atendimento_aberto_silencia_bot_e_repassa(api_int, externo):
    at, abertura = abre_atendimento(api_int, externo)
    st, r = api_int.post("/api/mensagens", {"telefone": TEL, "texto": "tem estacionamento?"}, token=None)
    assert r["respostas"] == []
    assert esperar(lambda: any(p["json"].get("reply_to_message_id") == abertura["message_id"]
                               and "tem estacionamento" in p["json"]["text"] for p in externo.telegram()))
    # emergência continua respondendo
    assert "192" in api_int.msg(TEL, "agora estou com falta de ar")


def test_equipe_responde_em_cima_da_mensagem(api_int, externo):
    at, abertura = abre_atendimento(api_int, externo)
    assert tg(api_int, "Olá, aqui é a Rita. Como posso ajudar?", reply_to=abertura["message_id"]) == 200
    assert esperar(lambda: any(m["texto"] == "Olá, aqui é a Rita. Como posso ajudar?" for m in api_int.saida("humano")))
    assert api_int.saida("humano")[0]["telefone"] == "+" + NUM
    assert esperar(lambda: "Olá, aqui é a Rita. Como posso ajudar?" in textos_whats(externo))


def test_webhook_telegram_protegido(api_int, externo):
    at, abertura = abre_atendimento(api_int, externo)
    assert tg(api_int, "invasor", reply_to=abertura["message_id"], segredo="errado") == 401
    assert tg(api_int, "outro grupo", reply_to=abertura["message_id"], chat=-1009999) == 200
    time.sleep(0.5)
    assert api_int.saida("humano") == []


def test_comandos_responder_encerrar_fila(api_int, externo):
    at, _ = abre_atendimento(api_int, externo)
    tg(api_int, f"/responder {at['id']} Já te ligo")
    assert esperar(lambda: [m["texto"] for m in api_int.saida("humano")] == ["Já te ligo"])
    n = len(externo.telegram())
    tg(api_int, "/fila")
    assert esperar(lambda: any(f"#{at['id']}" in p["json"]["text"] for p in externo.telegram()[n:]))
    tg(api_int, f"/encerrar {at['id']}")
    assert esperar(lambda: api_int.get("/api/atendimento-humano")[1]["fila"] == [])
    assert api_int.msg(TEL, "tem estacionamento?") == ESTAC


def test_comando_agenda(api_int, externo):
    pid = api_int.paciente("Maria Lima", "41999990001")
    api_int.agenda(pid, "2026-10-07T09:00", "avaliacao", "ana")
    api_int.agenda(pid, "2026-10-07T14:00", "limpeza", "ana")
    _, c = api_int.agenda(pid, "2026-10-07T15:00", "avaliacao", "bruno")
    api_int.post(f"/api/agendamentos/{c['id']}/cancelar")
    tg(api_int, "/agenda 2026-10-07")
    def achou():
        ts = [p["json"]["text"] for p in externo.telegram()]
        return any("09:00 Maria Lima — Avaliação (Dra. Ana)" in t and "14:00 Maria Lima — Limpeza (Dra. Ana)" in t
                   and "15:00" not in t for t in ts)
    assert esperar(achou)


def test_recepcao_responde_e_encerra(api_int, externo):
    at, _ = abre_atendimento(api_int, externo)
    assert api_int.post(f"/api/atendimento-humano/{at['id']}/responder", {"texto": "Pode vir às 10h"})[0] == 200
    assert [m["texto"] for m in api_int.saida("humano")] == ["Pode vir às 10h"]
    assert api_int.post(f"/api/atendimento-humano/{at['id']}/encerrar")[0] == 200
    assert api_int.get("/api/atendimento-humano")[1]["fila"] == []


def test_cancelamento_pelo_chat_avisa_equipe(api_int, externo):
    pid = api_int.paciente("Maria", TEL)
    api_int.agenda(pid, "2026-10-07T09:00", profissional="ana")
    api_int.post("/api/tarefas/rodar", {})
    assert "cancelad" in norm(api_int.msg(TEL, "2"))
    assert esperar(lambda: any(p["json"]["text"].startswith("Cancelado:") and "07/10 09:00" in p["json"]["text"]
                               for p in externo.telegram()))
