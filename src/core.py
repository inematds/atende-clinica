"""Estado transacional e regras de agenda da clínica."""
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import threading
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent.parent


class Erro(Exception):
    def __init__(self, status, mensagem):
        self.status, self.mensagem = status, mensagem


def agora():
    return datetime.fromisoformat(os.environ['ATENDE_AGORA']) if os.environ.get('ATENDE_AGORA') else datetime.now()


def telefone(valor):
    if not isinstance(valor, str) or re.search(r'[^\d+()\s-]', valor):
        raise Erro(400, 'Telefone inválido')
    digitos = re.sub(r'\D', '', valor)
    if len(digitos) in (12, 13) and digitos.startswith('55'):
        digitos = digitos[2:]
    if len(digitos) not in (10, 11):
        raise Erro(400, 'Telefone inválido')
    return '+55' + digitos


class Clinica:
    def __init__(self, pasta):
        self.pasta = Path(pasta)
        self.pasta.mkdir(parents=True, exist_ok=True)
        config = self.pasta / 'clinica.json'
        if not config.exists():
            shutil.copyfile(ROOT / 'exemplos/clinica.json', config)
        self.cfg = json.loads(config.read_text(encoding='utf-8'))
        self.lock = threading.RLock()
        self.db = sqlite3.connect(self.pasta / 'estado.sqlite3', check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS catalogo (tipo TEXT, id TEXT, dados TEXT, PRIMARY KEY(tipo,id));
            CREATE TABLE IF NOT EXISTS meta (chave TEXT PRIMARY KEY, valor TEXT);
            CREATE TABLE IF NOT EXISTS pacientes (
                id INTEGER PRIMARY KEY, nome TEXT NOT NULL, telefone TEXT UNIQUE,
                email TEXT, nascimento TEXT, consentimento_marketing INTEGER NOT NULL DEFAULT 0,
                nao_contatar INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS agendamentos (
                id INTEGER PRIMARY KEY, paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
                servico TEXT NOT NULL, profissional TEXT NOT NULL, inicio TEXT NOT NULL,
                fim TEXT NOT NULL, status TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS agenda_profissional ON agendamentos(profissional,inicio,fim);
            CREATE TABLE IF NOT EXISTS bloqueios (
                id INTEGER PRIMARY KEY, profissional TEXT NOT NULL,
                inicio TEXT NOT NULL, fim TEXT NOT NULL, motivo TEXT NOT NULL);
        ''')
        with self.db:
            if not self.db.execute("SELECT 1 FROM meta WHERE chave='semeado'").fetchone():
                for tipo in ('servicos', 'profissionais', 'faq'):
                    for item in self.cfg.get(tipo, []):
                        item = dict(item)
                        if tipo != 'faq':
                            item.setdefault('ativo', True)
                        if tipo == 'profissionais':
                            item.setdefault('registro', None)
                            item.setdefault('horarios', None)
                        self.db.execute('INSERT INTO catalogo VALUES (?,?,?)', (tipo, item['id'], json.dumps(item)))
                self.db.execute("INSERT INTO meta VALUES ('semeado','1')")

    def catalogo(self, tipo):
        return [json.loads(r[0]) for r in self.db.execute('SELECT dados FROM catalogo WHERE tipo=? ORDER BY rowid', (tipo,))]

    def servico(self, ident):
        for s in self.catalogo('servicos'):
            if s['id'] == ident:
                return s
        raise Erro(404, 'Serviço inexistente')

    def paciente(self, ident):
        r = self.db.execute('SELECT * FROM pacientes WHERE id=?', (ident,)).fetchone()
        if not r:
            raise Erro(404, 'Paciente inexistente')
        p = dict(r)
        for k in ('consentimento_marketing', 'nao_contatar'):
            p[k] = bool(p[k])
        return p

    def criar_paciente(self, b):
        from .cadastros import validar_paciente
        validar_paciente(b)
        tel = telefone(b.get('telefone'))
        r = self.db.execute('SELECT id FROM pacientes WHERE telefone=?', (tel,)).fetchone()
        if r:
            return 200, {'id': r[0]}
        if not isinstance(b.get('nome'), str) or not b['nome'].strip():
            raise Erro(400, 'Nome obrigatório')
        c = self.db.execute('INSERT INTO pacientes(nome,telefone,email,nascimento,consentimento_marketing) VALUES (?,?,?,?,?)',
                            (b['nome'], tel, b.get('email'), b.get('nascimento'), bool(b.get('consentimento_marketing', False))))
        ident = c.lastrowid
        # A preferência de contato pode anteceder o cadastro pela recepção.
        if self.db.execute("SELECT 1 FROM sqlite_master WHERE name='sessoes'").fetchone():
            sessao = self.db.execute('SELECT dados FROM sessoes WHERE telefone=?', (tel,)).fetchone()
            if sessao and json.loads(sessao[0]).get('nao_contatar'):
                self.db.execute('UPDATE pacientes SET nao_contatar=1 WHERE id=?', (ident,))
            self.db.execute('UPDATE historico SET paciente_id=? WHERE telefone=? AND paciente_id IS NULL', (ident, tel))
        return 201, {'id': ident}

    def candidatos(self, servico, data, profissional=None):
        s = self.servico(servico)
        dia = datetime.strptime(data, '%Y-%m-%d')
        if not s['ativo'] or data in self.cfg.get('feriados', []):
            return []
        resultado = []
        duracao = timedelta(minutes=s['duracao_min'])
        passo = timedelta(minutes=self.cfg['passo_min'])
        if passo.total_seconds() <= 0 or duracao.total_seconds() <= 0:
            raise Erro(422, 'Duração e passo devem ser positivos')
        limite = agora() + timedelta(hours=self.cfg['antecedencia_min_horas'])
        for p in self.catalogo('profissionais'):
            if not p['ativo'] or servico not in p['servicos'] or (profissional and profissional != p['id']):
                continue
            grade = p.get('horarios') if p.get('horarios') is not None else self.cfg['horarios']
            for ini, fim in grade.get(('seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom')[dia.weekday()], []):
                t = datetime.fromisoformat(data + 'T' + ini)
                final = datetime.fromisoformat(data + 'T' + fim)
                while t + duracao <= final:
                    bloqueado = self.db.execute('SELECT 1 FROM bloqueios WHERE profissional=? AND inicio < ? AND fim > ?',
                        (p['id'], (t + duracao).isoformat(timespec='minutes'), t.isoformat(timespec='minutes'))).fetchone()
                    if t >= limite and not bloqueado:
                        resultado.append({'inicio': t.isoformat(timespec='minutes'), 'profissional': p['id']})
                    t += passo
        return sorted(resultado, key=lambda h: (h['inicio'], h['profissional']))

    def livre(self, profissional, inicio, fim, ignorar=None):
        return not self.db.execute('''SELECT 1 FROM agendamentos WHERE profissional=?
            AND status IN ('agendado','confirmado','realizado','falta') AND inicio < ? AND fim > ?
            AND (? IS NULL OR id != ?) LIMIT 1''', (profissional, fim, inicio, ignorar, ignorar)).fetchone()

    def horarios(self, servico, data, profissional=None):
        duracao = self.servico(servico)['duracao_min']
        return [h for h in self.candidatos(servico, data, profissional) if self.livre(h['profissional'], h['inicio'],
                (datetime.fromisoformat(h['inicio']) + timedelta(minutes=duracao)).isoformat(timespec='minutes'))]

    def agendar(self, b, ident=None):
        self.paciente(b['paciente_id'])
        s = self.servico(b['servico'])
        inicio = b['inicio']
        try:
            datetime.strptime(inicio, '%Y-%m-%dT%H:%M')
        except (ValueError, TypeError):
            raise Erro(422, 'Horário inválido')
        candidatos = [h for h in self.candidatos(s['id'], inicio[:10], b.get('profissional')) if h['inicio'] == inicio]
        if not candidatos:
            raise Erro(422, 'Horário inválido')
        fim = (datetime.fromisoformat(inicio) + timedelta(minutes=s['duracao_min'])).isoformat(timespec='minutes')
        for h in candidatos:
            if self.livre(h['profissional'], inicio, fim, ident):
                valores = (b['paciente_id'], s['id'], h['profissional'], inicio, fim, 'agendado')
                if ident is None:
                    ident = self.db.execute('INSERT INTO agendamentos(paciente_id,servico,profissional,inicio,fim,status) VALUES (?,?,?,?,?,?)', valores).lastrowid
                else:
                    self.db.execute('UPDATE agendamentos SET paciente_id=?,servico=?,profissional=?,inicio=?,fim=?,status=? WHERE id=?', (*valores, ident))
                return self.agendamento(ident)
        raise Erro(409, 'Horário ocupado')

    def agendamento(self, ident):
        r = self.db.execute('SELECT a.*,p.telefone FROM agendamentos a JOIN pacientes p ON p.id=a.paciente_id WHERE a.id=?', (ident,)).fetchone()
        if not r:
            raise Erro(404, 'Agendamento inexistente')
        return dict(r)

    def listar_agenda(self, q):
        de = q.get('data', q.get('de', '0001-01-01'))
        ate = q.get('data', q.get('ate', '9999-12-31'))
        return [dict(r) for r in self.db.execute('''SELECT a.*,p.telefone FROM agendamentos a JOIN pacientes p ON p.id=a.paciente_id
            WHERE substr(inicio,1,10) BETWEEN ? AND ? AND (? IS NULL OR profissional=?) ORDER BY inicio,a.id''',
            (de, ate, q.get('profissional'), q.get('profissional')))]
