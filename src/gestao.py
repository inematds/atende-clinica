"""Campanhas, anonimização e indicadores, sem dependências de transporte."""
import calendar
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata

from .core import Erro
from . import conversa


def campanhas(c, texto):
    if not isinstance(texto, str) or not texto.strip():
        raise Erro(400, 'Texto obrigatório')
    normal = ''.join(x for x in unicodedata.normalize('NFD', texto.lower())
                     if unicodedata.category(x) != 'Mn')
    regras = (
        ('promessa_resultado', ('cfm', 'cfo', 'coffito', 'estetica'),
         r'garantido|garantia de resultado|100%'),
        ('melhor_profissional', ('cfm', 'cfo', 'coffito'),
         r'melhor medico|melhor dentista|melhor fisioterapeuta|melhor clinica'),
        ('sorteio_brinde', ('cfm', 'cfo'), r'sorteio|brinde|premio|premiacao'),
        ('antes_depois', ('cfm', 'cfo'), r'antes e depois'),
        ('consorcio', ('cfm',), r'consorcio'),
        ('preco', ('cfo', 'coffito'), r'r\$|reais'),
        ('parcelamento', ('cfo',), r'parcela|sem juros|\d+x\b'),
        ('gratuito', ('cfo', 'coffito'), r'gratis|gratuito|gratuita'),
        ('promocao', ('coffito',), r'promocao|desconto|oferta'),
    )
    violacoes = [codigo for codigo, conselhos, padrao in regras
                if c.cfg['conselho'] in conselhos and re.search(padrao, normal)]
    if violacoes:
        return 422, {'violacoes': violacoes}
    pacientes = c.db.execute('SELECT id FROM pacientes WHERE consentimento_marketing=1 AND nao_contatar=0').fetchall()
    return 200, {'enviadas': sum(conversa.enviar(c, p['id'], 'campanha', texto) for p in pacientes)}


def remover_paciente(c, ident):
    p = c.paciente(ident)
    # Desvincula o telefone antes de liberar vagas: ele não pode receber oferta.
    c.db.execute('''UPDATE pacientes SET nome='removido', telefone=NULL, email=NULL,
        nascimento=NULL, consentimento_marketing=0, nao_contatar=1 WHERE id=?''', (ident,))
    c.db.execute("UPDATE espera SET status='cancelado' WHERE paciente_id=?", (ident,))
    c.db.execute('UPDATE retornos SET avisado=1 WHERE paciente_id=?', (ident,))
    for a in c.db.execute("SELECT id FROM agendamentos WHERE paciente_id=? AND status IN ('agendado','confirmado')", (ident,)).fetchall():
        conversa.cancelar(c, a['id'])
    c.db.execute("UPDATE historico SET texto='',telefone=NULL WHERE paciente_id=? OR telefone=?", (ident, p['telefone']))
    c.db.execute("UPDATE saida SET texto='',telefone=NULL,oferta=NULL,respondida=1,status='simulado' WHERE paciente_id=? OR telefone=?", (ident, p['telefone']))
    if p['telefone']:
        c.db.execute('DELETE FROM sessoes WHERE telefone=?', (p['telefone'],))
        c.db.execute("UPDATE humanos SET telefone=NULL,motivo='',status='encerrado' WHERE telefone=?", (p['telefone'],))


def raiox(c, mes):
    if not isinstance(mes, str) or not re.fullmatch(r'\d{4}-\d{2}', mes):
        raise Erro(400, 'Mês inválido')
    inicio = datetime.strptime(mes, '%Y-%m')
    dias = calendar.monthrange(inicio.year, inicio.month)[1]
    registros = [dict(r) for r in c.db.execute('SELECT * FROM agendamentos WHERE substr(inicio,1,7)=?', (mes,))]
    realizados = sum(a['status'] == 'realizado' for a in registros)
    faltas = sum(a['status'] == 'falta' for a in registros)
    ocupados = sum((datetime.fromisoformat(a['fim']) - datetime.fromisoformat(a['inicio'])).total_seconds() / 60
                   for a in registros if a['status'] in ('agendado', 'confirmado', 'realizado', 'falta'))
    disponiveis = 0
    for dia in range(dias):
        data = inicio + timedelta(days=dia)
        if data.date().isoformat() in c.cfg.get('feriados', []):
            continue
        semana = ('seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom')[data.weekday()]
        for p in c.catalogo('profissionais'):
            grade = p.get('horarios') if p.get('horarios') is not None else c.cfg['horarios']
            for ini, fim in grade.get(semana, []):
                disponiveis += (datetime.strptime(fim, '%H:%M') - datetime.strptime(ini, '%H:%M')).total_seconds() / 60
    novos = c.db.execute('''SELECT COUNT(*) FROM (SELECT paciente_id, MIN(inicio) AS primeiro
        FROM agendamentos WHERE status='realizado' GROUP BY paciente_id) WHERE substr(primeiro,1,7)=?''', (mes,)).fetchone()[0]
    retornos = c.db.execute('SELECT * FROM retornos WHERE substr(data,1,7)=?', (mes,)).fetchall()
    cumpridos = 0
    for r in retornos:
        data = datetime.fromisoformat(r['data'])
        de, ate = ((data + timedelta(days=n)).date().isoformat() for n in (-30, 30))
        cumpridos += bool(c.db.execute('''SELECT 1 FROM agendamentos WHERE paciente_id=? AND servico=?
            AND status='realizado' AND substr(inicio,1,10) BETWEEN ? AND ? LIMIT 1''',
            (r['paciente_id'], r['servico'], de, ate)).fetchone())
    def percentual(n, total):
        return round(n / total * 100, 1) if total else 0.0
    return {'pacote': 'clinica', 'mes': mes, 'valores': {
        'atendimentos_mes': realizados, 'falta_pct': percentual(faltas, realizados + faltas),
        'ocupacao_pct': percentual(ocupados, disponiveis), 'clientes_novos_mes': novos,
        'retorno_atual_pct': percentual(cumpridos, len(retornos)),
    }}


def exportar(c, mes, arquivo):
    valores = raiox(c, mes)['valores']
    caminho = Path(arquivo)
    acompanhamento = json.loads(caminho.read_text(encoding='utf-8'))
    meses = acompanhamento.get('meses', [])
    anteriores = sorted((m for m in meses if m['mes'] < mes), key=lambda m: m['mes'])
    anterior = anteriores[-1]['valores'] if anteriores else acompanhamento['base']['valores']
    novo = {'mes': mes, 'valores': {**anterior, **valores}, 'obs': 'atende-clinica'}
    acompanhamento['meses'] = sorted([m for m in meses if m['mes'] != mes] + [novo], key=lambda m: m['mes'])
    # Substituição atômica evita JSON parcial em caso de interrupção.
    nome = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=caminho.parent, delete=False) as f:
            nome = f.name
            json.dump(acompanhamento, f, ensure_ascii=False, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(nome, caminho)
    finally:
        if nome and os.path.exists(nome):
            os.unlink(nome)
