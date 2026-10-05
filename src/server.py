"""CLI e transporte HTTP; cada requisição de domínio é uma transação."""
import argparse
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
import sys
from urllib.parse import parse_qs, urlsplit

from .core import Clinica, Erro, ROOT
from . import conversa, gestao, cadastros, backup, integracoes


def rotear(c, metodo, rota, q, b):
    if metodo == 'POST' and rota.startswith('/webhook/evolution/'):
        integracoes.evolution(c, b)
        return 200, {'ok': True}
    if metodo == 'POST' and rota == '/webhook/telegram':
        integracoes.receber_telegram(c, b)
        return 200, {'ok': True}
    m = re.fullmatch(r'/api/atendimento-humano/(\d+)/(responder|encerrar)', rota)
    if metodo == 'POST' and m:
        return 200, integracoes.humano(c, int(m[1]), m[2], b.get('texto'))
    if metodo == 'GET' and rota == '/api/pacientes':
        return 200, {'pacientes': cadastros.pacientes(c, q.get('busca', ''))}
    m = re.fullmatch(r'/api/pacientes/(\d+)', rota)
    if metodo == 'PUT' and m:
        return 200, cadastros.editar_paciente(c, int(m[1]), b)
    m = re.fullmatch(r'/api/(profissionais|servicos|faq)(?:/([^/]+))?', rota)
    if m:
        tipo, ident = m.groups()
        if metodo == 'GET' and ident is None and tipo != 'servicos':
            return 200, {tipo: c.catalogo(tipo)}
        if metodo == 'POST' and ident is None:
            item = cadastros.salvar_catalogo(c, tipo, b)
            return 201, {'id': item['id']} if tipo == 'faq' else item
        if metodo == 'PUT' and ident is not None and tipo != 'faq':
            return 200, cadastros.salvar_catalogo(c, tipo, b, ident)
        if metodo == 'DELETE' and ident is not None:
            if tipo == 'faq':
                c.db.execute('DELETE FROM catalogo WHERE tipo=? AND id=?', (tipo, ident))
                return 204, None
            cadastros.salvar_catalogo(c, tipo, {'ativo': False}, ident)
            return 200, {'ativo': False}
    if rota == '/api/bloqueios':
        if metodo == 'POST':
            return 201, cadastros.bloquear(c, b)
        if metodo == 'GET':
            return 200, {'bloqueios': [dict(r) for r in c.db.execute(
                'SELECT * FROM bloqueios WHERE (? IS NULL OR profissional=?) ORDER BY inicio,id',
                (q.get('profissional'), q.get('profissional')))]}
    m = re.fullmatch(r'/api/bloqueios/(\d+)', rota)
    if metodo == 'DELETE' and m:
        c.db.execute('DELETE FROM bloqueios WHERE id=?', (int(m[1]),))
        return 204, None
    if metodo == 'GET' and rota == '/api/saude':
        return 200, {'ok': True, 'versao': (ROOT / 'VERSION').read_text().strip()}
    if metodo == 'GET' and rota == '/api/servicos':
        return 200, {'servicos': [s for s in c.catalogo('servicos') if s['ativo']]}
    if metodo == 'GET' and rota == '/api/horarios':
        return 200, {'horarios': c.horarios(q['servico'], q['data'], q.get('profissional'))}
    if metodo == 'POST' and rota == '/api/mensagens':
        return 200, {'respostas': conversa.conversar(c, b['telefone'], b['texto'])}
    if metodo == 'GET' and rota == '/api/atendimento-humano':
        return 200, {'fila': conversa.fila(c)}
    if metodo == 'GET' and rota == '/api/saida':
        return 200, {'mensagens': [dict(r) for r in c.db.execute('SELECT * FROM saida ORDER BY id')]}
    if metodo == 'POST' and rota == '/api/tarefas/rodar':
        return 200, conversa.rodar(c, b.get('agora'))
    if metodo == 'POST' and rota == '/api/espera':
        c.paciente(b['paciente_id'])
        c.servico(b['servico'])
        from datetime import datetime
        datetime.strptime(b['data'], '%Y-%m-%d')
        ident = c.db.execute('INSERT INTO espera(paciente_id,servico,data) VALUES (?,?,?)',
                             (b['paciente_id'], b['servico'], b['data'])).lastrowid
        return 201, {'id': ident}
    m = re.fullmatch(r'/api/pacientes/(\d+)/dados', rota)
    if metodo == 'GET' and m:
        return 200, conversa.dados_paciente(c, int(m[1]))
    if metodo == 'POST' and rota == '/api/campanhas':
        return gestao.campanhas(c, b['texto'])
    if metodo == 'GET' and rota == '/api/raiox':
        return 200, gestao.raiox(c, q['mes'])
    m = re.fullmatch(r'/api/pacientes/(\d+)', rota)
    if metodo == 'DELETE' and m:
        gestao.remover_paciente(c, int(m[1]))
        return 204, None
    if metodo == 'POST' and rota == '/api/pacientes':
        return c.criar_paciente(b)
    if metodo == 'POST' and rota == '/api/agendamentos':
        return 201, c.agendar(b)
    if metodo == 'GET' and rota == '/api/agendamentos':
        return 200, {'agendamentos': c.listar_agenda(q)}
    m = re.fullmatch(r'/api/agendamentos/(\d+)/(cancelar|remarcar|presenca)', rota)
    if metodo == 'POST' and m:
        ident, acao = int(m[1]), m[2]
        a = c.agendamento(ident)
        if acao == 'remarcar':
            return 200, c.agendar({**a, 'inicio': b['inicio']}, ident)
        if acao == 'presenca' and not isinstance(b.get('compareceu'), bool):
            raise Erro(400, 'compareceu deve ser booleano')
        status = 'cancelado' if acao == 'cancelar' else ('realizado' if b['compareceu'] else 'falta')
        if acao == 'cancelar':
            conversa.cancelar(c, ident)
        else:
            conversa.presenca(c, ident, b['compareceu'])
        return 200, {'status': status}
    raise Erro(404, 'Rota inexistente')


def main():
    parser = argparse.ArgumentParser(description='Atendimento da clínica')
    sub = parser.add_subparsers(dest='comando', required=True)
    serve = sub.add_parser('serve')
    serve.add_argument('--porta', type=int, default=8080)
    serve.add_argument('--host', default='127.0.0.1')
    serve.add_argument('--dados', required=True)
    raiox = sub.add_parser('raiox')
    raiox.add_argument('--dados', required=True)
    raiox.add_argument('--mes', required=True)
    raiox.add_argument('--acompanhamento', required=True)
    for comando, arquivo in (('backup', '--saida'), ('restaurar', '--entrada')):
        p = sub.add_parser(comando)
        p.add_argument('--dados', required=True)
        p.add_argument(arquivo, required=True)
    args = parser.parse_args()
    if args.comando in ('backup', 'restaurar'):
        try:
            if args.comando == 'backup':
                backup.copiar(args.dados, args.saida)
            else:
                backup.restaurar(args.dados, args.entrada)
        except Exception as e:
            parser.exit(1, f'Falha no {args.comando}: {e}\n')
        return
    if args.comando == 'raiox':
        clinica = Clinica(args.dados)
        try:
            conversa.iniciar(clinica)
            gestao.exportar(clinica, args.mes, args.acompanhamento)
        finally:
            clinica.db.close()
        return
    clinica = Clinica(args.dados)
    conversa.iniciar(clinica)

    class Handler(BaseHTTPRequestHandler):
        def processar(self):
            url = urlsplit(self.path)
            arquivos = {'/': ('index.html', 'text/html'), '/recepcao': ('recepcao.html', 'text/html'),
                        '/web/style.css': ('style.css', 'text/css'), '/web/chat.js': ('chat.js', 'text/javascript'),
                        '/web/recepcao.js': ('recepcao.js', 'text/javascript')}
            if self.command == 'GET' and url.path in arquivos:
                nome, tipo = arquivos[url.path]
                conteudo = (ROOT / 'web' / nome).read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', tipo + '; charset=utf-8')
                self.send_header('Content-Length', str(len(conteudo)))
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
                self.end_headers()
                self.wfile.write(conteudo)
                return
            publico = (self.command == 'GET' and url.path in ('/', '/recepcao', '/api/saude', '/api/servicos', '/api/horarios')) or (self.command == 'POST' and url.path == '/api/mensagens')
            try:
                if self.command == 'POST' and integracoes.autorizar(url.path, self.headers):
                    publico = True
                if not publico and not hmac.compare_digest(self.headers.get('X-Token', '').encode(), str(clinica.cfg['token']).encode()):
                    raise Erro(401, 'Token inválido')
                tamanho = int(self.headers.get('Content-Length', '0'))
                if tamanho < 0 or tamanho > 1048576:
                    raise Erro(413, 'Corpo muito grande')
                b = json.loads(self.rfile.read(tamanho)) if tamanho else {}
                if not isinstance(b, dict):
                    raise Erro(400, 'Objeto JSON esperado')
                q = {k: v[-1] for k, v in parse_qs(url.query).items()}
                with clinica.lock, clinica.db:
                    status, resposta = rotear(clinica, self.command, url.path, q, b)
            except Erro as e:
                status, resposta = e.status, {'erro': e.mensagem}
            except (ValueError, KeyError, TypeError):
                status, resposta = 400, {'erro': 'Pedido inválido'}
            except Exception as e:
                print(f'Erro interno: {type(e).__name__}: {e}', file=sys.stderr)
                status, resposta = 500, {'erro': 'Erro interno'}
            conteudo = b'' if status == 204 else json.dumps(resposta, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(conteudo)))
            self.end_headers()
            self.wfile.write(conteudo)

        do_GET = do_POST = do_PUT = do_DELETE = processar

        def log_message(self, *args):
            pass

    servidor = ThreadingHTTPServer((args.host, args.porta), Handler)
    print(f'PORTA={servidor.server_port}', flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()
        clinica.db.close()
