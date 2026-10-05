"""Conversa e notificações persistidas, compartilhadas por todos os canais."""
import json
import re
import unicodedata
from datetime import datetime, timedelta

from .core import Erro, agora, telefone
from . import integracoes


def normalizar(texto):
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')
    return ' '.join(re.sub(r'[^\w\s]', ' ', texto).split())


def iniciar(c):
    integracoes.iniciar(c)
    c.db.executescript('''
        CREATE TABLE IF NOT EXISTS sessoes (telefone TEXT PRIMARY KEY, dados TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS historico (id INTEGER PRIMARY KEY, paciente_id INTEGER,
            telefone TEXT, direcao TEXT, texto TEXT, quando TEXT);
        CREATE TABLE IF NOT EXISTS humanos (id INTEGER PRIMARY KEY, telefone TEXT, motivo TEXT,
            prioridade TEXT, status TEXT NOT NULL DEFAULT 'aberto');
        CREATE TABLE IF NOT EXISTS saida (id INTEGER PRIMARY KEY, tipo TEXT, telefone TEXT,
            paciente_id INTEGER, texto TEXT, agendamento_id INTEGER, quando TEXT,
            status TEXT NOT NULL DEFAULT 'simulado', respondida INTEGER NOT NULL DEFAULT 0, oferta TEXT);
        CREATE TABLE IF NOT EXISTS espera (id INTEGER PRIMARY KEY, paciente_id INTEGER,
            servico TEXT, data TEXT, status TEXT NOT NULL DEFAULT 'aguardando');
        CREATE TABLE IF NOT EXISTS retornos (id INTEGER PRIMARY KEY, agendamento_id INTEGER UNIQUE,
            paciente_id INTEGER, servico TEXT, data TEXT, avisado INTEGER NOT NULL DEFAULT 0);
    ''')


def paciente_tel(c, tel):
    r = c.db.execute('SELECT id FROM pacientes WHERE telefone=?', (tel,)).fetchone()
    return c.paciente(r[0]) if r else None


def registrar(c, tel, direcao, texto):
    p = paciente_tel(c, tel)
    c.db.execute('INSERT INTO historico(paciente_id,telefone,direcao,texto,quando) VALUES (?,?,?,?,?)',
                 (p['id'] if p else None, tel, direcao, texto, agora().isoformat(timespec='minutes')))


def enviar(c, pid, tipo, texto, agendamento_id=None, oferta=None):
    p = c.paciente(pid)
    if p['nao_contatar'] or not p['telefone']:
        return 0
    ident = c.db.execute('''INSERT INTO saida(tipo,telefone,paciente_id,texto,agendamento_id,quando,oferta)
        VALUES (?,?,?,?,?,?,?)''', (tipo, p['telefone'], pid, texto, agendamento_id,
        agora().isoformat(timespec='minutes'), json.dumps(oferta) if oferta else None)).lastrowid
    integracoes.entregar(c, ident)
    registrar(c, p['telefone'], 'saida', texto)
    return 1


def cancelar(c, ident):
    a = c.agendamento(ident)
    if a['status'] == 'cancelado':
        return
    c.db.execute("UPDATE agendamentos SET status='cancelado' WHERE id=?", (ident,))
    e = c.db.execute('''SELECT e.* FROM espera e JOIN pacientes p ON p.id=e.paciente_id
        WHERE e.servico=? AND e.data=? AND e.status='aguardando' AND p.nao_contatar=0
        AND p.telefone IS NOT NULL ORDER BY e.id LIMIT 1''', (a['servico'], a['inicio'][:10])).fetchone()
    if e:
        oferta = {k: a[k] for k in ('servico', 'inicio', 'profissional')}
        oferta['paciente_id'] = e['paciente_id']
        oferta['espera_id'] = e['id']
        enviar(c, e['paciente_id'], 'espera', f"Vaga às {a['inicio'][11:]}. Responda 1 para agendar.", ident, oferta)
        c.db.execute("UPDATE espera SET status='ofertado' WHERE id=?", (e['id'],))


def presenca(c, ident, compareceu):
    a = c.agendamento(ident)
    status = 'realizado' if compareceu else 'falta'
    c.db.execute('UPDATE agendamentos SET status=? WHERE id=?', (status, ident))
    dias = c.servico(a['servico']).get('retorno_dias')
    if compareceu and dias is not None:
        data = (datetime.fromisoformat(a['inicio']) + timedelta(days=dias)).date().isoformat()
        c.db.execute('INSERT OR IGNORE INTO retornos(agendamento_id,paciente_id,servico,data) VALUES (?,?,?,?)',
                     (ident, a['paciente_id'], a['servico'], data))
    return status


def rodar(c, instante=None):
    t = datetime.fromisoformat(instante) if instante else agora()
    reenviadas = integracoes.reenviar(c)
    enviadas = 0
    for a in c.db.execute("SELECT * FROM agendamentos WHERE status='agendado' ORDER BY id").fetchall():
        if t < datetime.fromisoformat(a['inicio']) <= t + timedelta(hours=c.cfg['confirmacao_horas']):
            if not c.db.execute("SELECT 1 FROM saida WHERE tipo='confirmacao' AND agendamento_id=?", (a['id'],)).fetchone():
                data = datetime.fromisoformat(a['inicio']).strftime('%d/%m %H:%M')
                enviadas += enviar(c, a['paciente_id'], 'confirmacao',
                    f"Confirme {c.servico(a['servico'])['nome']} em {data}: 1 confirmar, 2 cancelar.", a['id'])
    for r in c.db.execute('SELECT * FROM retornos WHERE avisado=0 ORDER BY id').fetchall():
        if t >= datetime.fromisoformat(r['data']) - timedelta(days=c.cfg['retorno_aviso_dias']):
            n = enviar(c, r['paciente_id'], 'retorno', f"Está chegando seu retorno de {c.servico(r['servico'])['nome']}.", r['agendamento_id'])
            if n:
                c.db.execute('UPDATE retornos SET avisado=1 WHERE id=?', (r['id'],))
            enviadas += n
    return {'enviadas': enviadas, 'reenviadas': reenviadas}


def abrir_humano(c, tel, motivo, prioridade):
    r = c.db.execute("SELECT id FROM humanos WHERE telefone=? AND status='aberto'", (tel,)).fetchone()
    if r:
        if prioridade == 'alta':
            c.db.execute('UPDATE humanos SET prioridade=?,motivo=? WHERE id=?', (prioridade, motivo, r[0]))
        integracoes.notificar_humano(c, r[0], motivo)
        return r[0]
    ident = c.db.execute('INSERT INTO humanos(telefone,motivo,prioridade) VALUES (?,?,?)', (tel, motivo, prioridade)).lastrowid
    integracoes.notificar_humano(c, ident, motivo, abertura=True)
    return ident


def fila(c):
    return [dict(r) for r in c.db.execute("SELECT h.*,p.nome FROM humanos h LEFT JOIN pacientes p ON p.telefone=h.telefone WHERE h.status='aberto' ORDER BY h.id")]


def opcoes_servicos(c):
    ss = [s for s in c.catalogo('servicos') if s['ativo']]
    return {'etapa': 'servico', 'opcoes': [s['id'] for s in ss],
            'texto': '\n'.join(f"{i} - {s['nome']}" for i, s in enumerate(ss, 1))}


def conversar(c, numero, texto):
    tel = telefone(numero)
    if not isinstance(texto, str):
        raise Erro(400, 'Texto obrigatório')
    registrar(c, tel, 'entrada', texto)
    r = c.db.execute('SELECT dados FROM sessoes WHERE telefone=?', (tel,)).fetchone()
    estado = json.loads(r[0]) if r else {}
    respostas = decidir(c, tel, texto, estado)
    c.db.execute('INSERT INTO sessoes VALUES (?,?) ON CONFLICT(telefone) DO UPDATE SET dados=excluded.dados', (tel, json.dumps(estado)))
    for resposta in respostas:
        registrar(c, tel, 'saida', resposta)
    return respostas


def decidir(c, tel, texto, estado):
    t = normalizar(texto)
    p = paciente_tel(c, tel)
    emergencias = ('dor no peito', 'falta de ar', 'desmaio', 'desmaiou', 'sangramento', 'sangrando', 'convulsao', 'suicidio', 'me matar', 'avc', 'infarto')
    if any(x in t for x in emergencias):
        estado.clear()
        abrir_humano(c, tel, texto, 'alta')
        return ['Ligue 192 ou procure um pronto-socorro imediatamente. Nossa equipe foi avisada.']
    if t in ('parar', 'sair', 'pare'):
        # Guarda a preferência mesmo antes de saber o nome.
        estado.clear()
        estado['nao_contatar'] = True
        if p:
            c.db.execute('UPDATE pacientes SET nao_contatar=1 WHERE id=?', (p['id'],))
        resposta = ['Você não vai mais receber mensagens.']
    else:
        resposta = None
    humano = c.db.execute("SELECT id FROM humanos WHERE telefone=? AND status='aberto'", (tel,)).fetchone()
    if humano:
        integracoes.notificar_humano(c, humano[0], texto)
        return []
    if resposta is not None:
        return resposta
    if any(x in t for x in ('atendente', 'humano', 'falar com alguem')):
        estado.pop('etapa', None)
        estado['falhas'] = 0
        abrir_humano(c, tel, texto, 'normal')
        return ['Vou chamar um atendente.']
    if estado.get('etapa'):
        estado['falhas'] = 0
        if t == 'cancelar':
            estado.pop('etapa', None)
            return ['Agendamento interrompido.']
        if estado['etapa'] == 'nome':
            if not texto.strip():
                return ['Qual é seu nome?']
            _, novo = c.criar_paciente({'nome': texto, 'telefone': tel})
            c.db.execute('UPDATE historico SET paciente_id=? WHERE telefone=? AND paciente_id IS NULL', (novo['id'], tel))
            if estado.get('nao_contatar'):
                c.db.execute('UPDATE pacientes SET nao_contatar=1 WHERE id=?', (novo['id'],))
            estado.update(opcoes_servicos(c))
            return [estado['texto']]
        indice = int(t) - 1 if t.isascii() and t.isdigit() else -1
        if not 0 <= indice < len(estado['opcoes']):
            return [estado['texto']]
        if estado['etapa'] == 'servico':
            servico = estado['opcoes'][indice]
            hs = []
            for d in range(c.cfg['janela_dias'] + 1):
                hs.extend(c.horarios(servico, (agora() + timedelta(days=d)).date().isoformat()))
                if len(hs) >= 3:
                    break
            hs = hs[:3]
            nomes = {p['id']: p['nome'] for p in c.catalogo('profissionais')}
            msg = '\n'.join(f"{i}) {datetime.fromisoformat(h['inicio']).strftime('%d/%m %H:%M')} com {nomes[h['profissional']]}" for i, h in enumerate(hs, 1))
            estado.update(etapa='horario', servico=servico, opcoes=hs, texto=msg or 'Sem horários livres. Digite cancelar para sair.')
            return [estado['texto']]
        h = estado['opcoes'][indice]
        try:
            a = c.agendar({'paciente_id': p['id'], 'servico': estado['servico'], **h})
        except Erro as e:
            if e.status not in (409, 422):
                raise
            return ['Horário ocupado ou indisponível. Digite cancelar para recomeçar.']
        estado.pop('etapa', None)
        integracoes.avisar_agenda(c, a)
        return [f"Agendado para {datetime.fromisoformat(a['inicio']).strftime('%d/%m %H:%M')}."]
    pendente = c.db.execute('SELECT * FROM saida WHERE telefone=? ORDER BY id DESC LIMIT 1', (tel,)).fetchone()
    if pendente and not pendente['respondida']:
        acao = None
        if pendente['tipo'] == 'confirmacao':
            if t in ('1', 'sim', 'confirmo'):
                c.db.execute("UPDATE agendamentos SET status='confirmado' WHERE id=? AND status='agendado'", (pendente['agendamento_id'],))
                acao = 'Agendamento confirmado.'
            elif t in ('2', 'cancelar', 'nao'):
                cancelar(c, pendente['agendamento_id'])
                integracoes.avisar_agenda(c, c.agendamento(pendente['agendamento_id']), cancelado=True)
                acao = 'Agendamento cancelado.'
        elif pendente['tipo'] == 'espera' and t in ('1', 'sim'):
            oferta = json.loads(pendente['oferta'])
            try:
                a = c.agendar(oferta)
                integracoes.avisar_agenda(c, a)
                c.db.execute("UPDATE espera SET status='atendido' WHERE id=?", (oferta['espera_id'],))
                acao = 'Horário agendado.'
            except Erro as e:
                if e.status not in (409, 422):
                    raise
                acao = 'Horário ocupado ou indisponível.'
        if acao:
            estado['falhas'] = 0
            c.db.execute('UPDATE saida SET respondida=1 WHERE id=?', (pendente['id'],))
            return [acao]
    if any(x in t for x in ('agendar', 'marcar', 'consulta')):
        estado['falhas'] = 0
        if not p:
            estado['etapa'] = 'nome'
            return ['Qual é seu nome?']
        estado.update(opcoes_servicos(c))
        return [estado['texto']]
    comuns = set('que qual quais como onde para por com sem uma uns umas dos das seu sua seus suas voce voces vcs nos eles elas tem'.split())
    palavras = set(t.split())
    melhor, resposta = 0, None
    for item in c.catalogo('faq'):
        for pergunta in item['perguntas']:
            pp = {w for w in normalizar(pergunta).split() if len(w) >= 3 and w not in comuns}
            nota = len(pp & palavras) / len(pp) if pp else 0
            if nota >= .6 and nota > melhor:
                melhor, resposta = nota, item['resposta']
    if resposta is not None:
        estado['falhas'] = 0
        return [resposta]
    estado['falhas'] = estado.get('falhas', 0) + 1
    if estado['falhas'] >= 2:
        abrir_humano(c, tel, texto, 'normal')
    return ['Não entendi. Você pode pedir um atendente.']


def dados_paciente(c, ident):
    p = c.paciente(ident)
    return {'paciente': p, 'agendamentos': [a for a in c.listar_agenda({}) if a['paciente_id'] == ident],
            'mensagens': [dict(r) for r in c.db.execute('SELECT direcao,texto,quando FROM historico WHERE paciente_id=? ORDER BY id', (ident,))]}
