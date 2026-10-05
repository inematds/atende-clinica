"""Transportes opcionais, configurados exclusivamente pelo ambiente."""
import hmac
import json
import os
import re
from datetime import datetime
from urllib.request import Request, urlopen

from .core import Erro, agora, telefone


def iniciar(c):
    c.db.executescript('''
        CREATE TABLE IF NOT EXISTS evolution_recebidas (id TEXT PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS telegram_mensagens (message_id INTEGER PRIMARY KEY, atendimento_id INTEGER);
    ''')


def postar(url, corpo, headers=None):
    req = Request(url, data=json.dumps(corpo).encode(),
                  headers={'Content-Type': 'application/json', **(headers or {})}, method='POST')
    try:
        with urlopen(req, timeout=5) as resp:
            raw = resp.read()
            try:
                return True, json.loads(raw) if raw else {}
            except ValueError:
                return True, {}
    except (OSError, ValueError):
        return False, {}


def whatsapp(numero, texto):
    base = os.environ.get('EVOLUTION_URL')
    if not base:
        return 'simulado'
    ok, _ = postar(base.rstrip('/') + '/message/sendText/' + os.environ.get('EVOLUTION_INSTANCIA', ''),
                   {'number': numero.lstrip('+'), 'text': texto},
                   {'apikey': os.environ.get('EVOLUTION_API_KEY', '')})
    return 'enviado' if ok else 'pendente'


def entregar(c, ident):
    m = c.db.execute('SELECT * FROM saida WHERE id=?', (ident,)).fetchone()
    status = whatsapp(m['telefone'], m['texto'])
    c.db.execute('UPDATE saida SET status=? WHERE id=?', (status, ident))
    return status


def reenviar(c):
    linhas = c.db.execute("""SELECT s.id FROM saida s LEFT JOIN pacientes p ON p.id=s.paciente_id
        WHERE s.status='pendente' AND s.telefone IS NOT NULL
        AND (p.id IS NULL OR p.nao_contatar=0) ORDER BY s.id""").fetchall()
    return sum(entregar(c, r['id']) == 'enviado' for r in linhas)


def telegram(c, texto, atendimento=None, reply=None):
    nomes = ('TELEGRAM_API_URL', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID', 'TELEGRAM_SEGREDO')
    if not all(os.environ.get(n) for n in nomes):
        return
    corpo = {'chat_id': os.environ['TELEGRAM_CHAT_ID'], 'text': texto}
    if reply is not None:
        corpo['reply_to_message_id'] = reply
    ok, resultado = postar(os.environ['TELEGRAM_API_URL'].rstrip('/') + '/bot' + os.environ['TELEGRAM_TOKEN'] + '/sendMessage', corpo)
    mid = resultado.get('result', {}).get('message_id') if ok else None
    if atendimento is not None and mid is not None:
        c.db.execute('INSERT OR REPLACE INTO telegram_mensagens VALUES (?,?)', (mid, atendimento))


def notificar_humano(c, ident, texto, abertura=False):
    from .conversa import paciente_tel
    h = c.db.execute('SELECT * FROM humanos WHERE id=?', (ident,)).fetchone()
    p = paciente_tel(c, h['telefone'])
    nome = p['nome'] if p else h['telefone']
    original = c.db.execute('SELECT message_id FROM telegram_mensagens WHERE atendimento_id=? ORDER BY rowid LIMIT 1', (ident,)).fetchone()
    if abertura or not original:
        mensagem = f"#{ident} {h['telefone']} {nome} — {h['motivo']}\n{'ALTA' if h['prioridade'] == 'alta' else 'normal'}\n{texto}"
    else:
        mensagem = f"#{ident} {nome}: {texto}"
        if h['prioridade'] == 'alta':
            mensagem += '\nALTA'
    telegram(c, mensagem, ident, original[0] if original else None)


def avisar_agenda(c, a, cancelado=False):
    p = c.paciente(a['paciente_id'])
    servico = c.servico(a['servico'])['nome']
    profissional = next(p['nome'] for p in c.catalogo('profissionais') if p['id'] == a['profissional'])
    data = datetime.fromisoformat(a['inicio']).strftime('%d/%m %H:%M')
    telegram(c, f"{'Cancelado' if cancelado else 'Novo agendamento'}: {data} {p['nome']} — {servico} com {profissional}")


def humano(c, ident, acao, texto=None):
    from .conversa import paciente_tel, registrar
    h = c.db.execute("SELECT * FROM humanos WHERE id=? AND status='aberto'", (ident,)).fetchone()
    if not h:
        raise Erro(404, 'Atendimento aberto inexistente')
    if acao == 'encerrar':
        c.db.execute("UPDATE humanos SET status='encerrado' WHERE id=?", (ident,))
        return {'status': 'encerrado'}
    if not isinstance(texto, str) or not texto.strip():
        raise Erro(400, 'Texto obrigatório')
    p = paciente_tel(c, h['telefone'])
    ident = c.db.execute('''INSERT INTO saida(tipo,telefone,paciente_id,texto,quando)
        VALUES ('humano',?,?,?,?)''', (h['telefone'], p['id'] if p else None, texto, agora().isoformat(timespec='minutes'))).lastrowid
    registrar(c, h['telefone'], 'saida', texto)
    return {'status': entregar(c, ident)}


def evolution(c, b):
    from .conversa import conversar, registrar
    data = b.get('data') or {}
    key = data.get('key') or {}
    jid = key.get('remoteJid', '')
    ident = key.get('id')
    if b.get('event') != 'messages.upsert' or key.get('fromMe') or jid.endswith('@g.us') or not ident:
        return
    if c.db.execute('SELECT 1 FROM evolution_recebidas WHERE id=?', (ident,)).fetchone():
        return
    try:
        numero = telefone(jid.split('@')[0])
    except (Erro, ValueError, TypeError):
        return
    c.db.execute('INSERT INTO evolution_recebidas VALUES (?)', (ident,))
    msg = data.get('message') or {}
    texto = msg.get('conversation') or (msg.get('extendedTextMessage') or {}).get('text')
    if isinstance(texto, str) and texto:
        respostas = conversar(c, numero, texto)
    else:
        respostas = ['Por enquanto só consigo ler mensagens de texto.']
        registrar(c, numero, 'saida', respostas[0])
    for resposta in respostas:
        whatsapp(numero, resposta)


def receber_telegram(c, b):
    from .conversa import fila
    msg = b.get('message') or {}
    if str((msg.get('chat') or {}).get('id')) != os.environ.get('TELEGRAM_CHAT_ID'):
        return
    texto = msg.get('text')
    if not isinstance(texto, str):
        return
    m = re.fullmatch(r'/responder\s+(\d+)\s+(.+)', texto, re.S)
    enc = re.fullmatch(r'/encerrar\s+(\d+)', texto)
    try:
        if m:
            humano(c, int(m[1]), 'responder', m[2])
        elif enc:
            humano(c, int(enc[1]), 'encerrar')
        elif texto == '/fila':
            telegram(c, '\n'.join(f"#{h['id']} {h['nome'] or h['telefone']} — {h['motivo']}" for h in fila(c)) or 'Fila vazia.')
        elif texto == '/agenda' or texto.startswith('/agenda '):
            data = texto.split(maxsplit=1)[1] if ' ' in texto else agora().date().isoformat()
            linhas = []
            for a in c.listar_agenda({'data': data}):
                if a['status'] == 'cancelado':
                    continue
                nome = c.paciente(a['paciente_id'])['nome']
                serv = c.servico(a['servico'])['nome']
                prof = next(p['nome'] for p in c.catalogo('profissionais') if p['id'] == a['profissional'])
                linhas.append(f"{a['inicio'][11:]} {nome} — {serv} ({prof})")
            telegram(c, '\n'.join(linhas) or 'Sem agendamentos.')
        else:
            reply = (msg.get('reply_to_message') or {}).get('message_id')
            r = c.db.execute('SELECT atendimento_id FROM telegram_mensagens WHERE message_id=?', (reply,)).fetchone()
            if r:
                humano(c, r[0], 'responder', texto)
    except (Erro, ValueError):
        telegram(c, 'Comando inválido ou atendimento encerrado.')


def autorizar(rota, headers):
    if rota.startswith('/webhook/evolution/'):
        segredo = os.environ.get('WEBHOOK_SEGREDO', '')
        if not segredo or not hmac.compare_digest(rota.rsplit('/', 1)[-1].encode(), segredo.encode()):
            raise Erro(404, 'Webhook inexistente')
    elif rota == '/webhook/telegram':
        segredo = os.environ.get('TELEGRAM_SEGREDO', '')
        if not segredo or not hmac.compare_digest(headers.get('X-Telegram-Bot-Api-Secret-Token', '').encode(), segredo.encode()):
            raise Erro(401, 'Segredo inválido')
    else:
        return False
    return True
