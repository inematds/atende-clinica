"""Cadastros e bloqueios, executados na transação da requisição."""
from datetime import datetime
import json
import re
import unicodedata
import uuid

from .core import Erro, telefone


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if not unicodedata.combining(c))


def validar_paciente(b):
    if 'nome' in b and (not isinstance(b['nome'], str) or not b['nome'].strip()):
        raise Erro(400, 'Nome obrigatório')
    if b.get('nascimento') is not None:
        datetime.strptime(b['nascimento'], '%Y-%m-%d')
    for campo in ('consentimento_marketing', 'nao_contatar'):
        if campo in b and not isinstance(b[campo], bool):
            raise Erro(400, 'Preferência deve ser booleana')


def pacientes(c, busca):
    termo = normalizar(busca.strip())
    digitos = re.sub(r'\D', '', busca)
    return [c.paciente(r['id']) for r in c.db.execute('SELECT id,nome,telefone FROM pacientes ORDER BY id')
            if not termo or termo in normalizar(r['nome']) or (digitos and digitos in (r['telefone'] or ''))]


def editar_paciente(c, ident, b):
    p = c.paciente(ident)
    validar_paciente(b)
    campos = ('nome', 'telefone', 'email', 'nascimento', 'consentimento_marketing', 'nao_contatar')
    valores = {k: b[k] for k in campos if k in b}
    if 'telefone' in valores:
        valores['telefone'] = telefone(valores['telefone'])
        if c.db.execute('SELECT 1 FROM pacientes WHERE telefone=? AND id!=?', (valores['telefone'], ident)).fetchone():
            raise Erro(409, 'Telefone já cadastrado')
    for campo, valor in valores.items():
        c.db.execute(f'UPDATE pacientes SET {campo}=? WHERE id=?', (valor, ident))
    return c.paciente(ident)


def validar_horarios(grade):
    if grade is None:
        return
    if not isinstance(grade, dict) or set(grade) - set(('seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom')):
        raise Erro(422, 'Horários inválidos')
    for janelas in grade.values():
        if not isinstance(janelas, list):
            raise Erro(422, 'Horários inválidos')
        for janela in janelas:
            if not isinstance(janela, list) or len(janela) != 2:
                raise Erro(422, 'Janela inválida')
            inicio, fim = [datetime.strptime(h, '%H:%M') for h in janela]
            if fim <= inicio:
                raise Erro(422, 'Janela inválida')


def salvar_catalogo(c, tipo, b, ident=None):
    if ident is not None:
        atual = next((x for x in c.catalogo(tipo) if x['id'] == ident), None)
        if atual is None:
            raise Erro(404, 'Registro inexistente')
        item = {**atual, **b, 'id': ident}
    else:
        item = dict(b)
        if tipo == 'faq':
            item['id'] = uuid.uuid4().hex
        if not isinstance(item.get('id'), str) or not item['id'].strip():
            raise Erro(400, 'ID obrigatório')
        if any(x['id'] == item['id'] for x in c.catalogo(tipo)):
            raise Erro(409, 'ID já cadastrado')
        if tipo != 'faq':
            item.setdefault('ativo', True)
    if tipo == 'faq':
        if not isinstance(item.get('perguntas'), list) or not item['perguntas'] or not all(isinstance(p, str) and p.strip() for p in item['perguntas']) or not isinstance(item.get('resposta'), str) or not item['resposta'].strip():
            raise Erro(400, 'Perguntas e resposta obrigatórias')
    else:
        if not isinstance(item.get('nome'), str) or not item['nome'].strip():
            raise Erro(400, 'Nome obrigatório')
        if not isinstance(item['ativo'], bool):
            raise Erro(400, 'Ativo deve ser booleano')
        if tipo == 'servicos':
            if type(item.get('duracao_min')) is not int or item['duracao_min'] <= 0:
                raise Erro(422, 'Duração deve ser positiva')
            item.setdefault('retorno_dias', None)
            if item['retorno_dias'] is not None and (type(item['retorno_dias']) is not int or item['retorno_dias'] < 0):
                raise Erro(422, 'Retorno inválido')
        else:
            servicos = {s['id'] for s in c.catalogo('servicos')}
            if not isinstance(item.get('servicos'), list) or any(s not in servicos for s in item['servicos']):
                raise Erro(422, 'Serviço inexistente')
            item.setdefault('registro', None)
            item.setdefault('horarios', None)
            validar_horarios(item['horarios'])
    if ident is None:
        c.db.execute('INSERT INTO catalogo VALUES (?,?,?)', (tipo, item['id'], json.dumps(item)))
    else:
        c.db.execute('UPDATE catalogo SET dados=? WHERE tipo=? AND id=?', (json.dumps(item), tipo, ident))
    return item


def bloquear(c, b):
    if not any(p['id'] == b['profissional'] for p in c.catalogo('profissionais')):
        raise Erro(404, 'Profissional inexistente')
    inicio, fim = [datetime.strptime(b[k], '%Y-%m-%dT%H:%M') for k in ('inicio', 'fim')]
    if inicio >= fim:
        raise Erro(422, 'Intervalo inválido')
    ident = c.db.execute('INSERT INTO bloqueios(profissional,inicio,fim,motivo) VALUES (?,?,?,?)',
                         (b['profissional'], b['inicio'], b['fim'], b.get('motivo', ''))).lastrowid
    conflitos = [r[0] for r in c.db.execute("""SELECT id FROM agendamentos WHERE profissional=?
        AND inicio < ? AND fim > ? AND status IN ('agendado','confirmado','realizado','falta') ORDER BY id""",
        (b['profissional'], b['fim'], b['inicio']))]
    return {'id': ident, 'conflitos': conflitos}
