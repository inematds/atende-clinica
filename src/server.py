"""CLI e transporte HTTP; cada requisição de domínio é uma transação."""
import argparse
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
import sys
from urllib.parse import parse_qs, urlsplit

from .core import Clinica, Erro, ROOT


def rotear(c, metodo, rota, q, b):
    if metodo == 'GET' and rota == '/api/saude':
        return 200, {'ok': True, 'versao': (ROOT / 'VERSION').read_text().strip()}
    if metodo == 'GET' and rota == '/api/servicos':
        return 200, {'servicos': [s for s in c.catalogo('servicos') if s['ativo']]}
    if metodo == 'GET' and rota == '/api/horarios':
        return 200, {'horarios': c.horarios(q['servico'], q['data'], q.get('profissional'))}
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
        c.db.execute('UPDATE agendamentos SET status=? WHERE id=?', (status, ident))
        return 200, {'status': status}
    raise Erro(404, 'Rota inexistente')


def main():
    parser = argparse.ArgumentParser(description='Atendimento da clínica')
    sub = parser.add_subparsers(dest='comando', required=True)
    serve = sub.add_parser('serve')
    serve.add_argument('--porta', type=int, default=8080)
    serve.add_argument('--host', default='127.0.0.1')
    serve.add_argument('--dados', required=True)
    args = parser.parse_args()
    if args.host != '127.0.0.1':
        parser.error('Neste ambiente o servidor só pode escutar em 127.0.0.1')
    clinica = Clinica(args.dados)

    class Handler(BaseHTTPRequestHandler):
        def processar(self):
            url = urlsplit(self.path)
            publico = (self.command == 'GET' and url.path in ('/', '/recepcao', '/api/saude', '/api/servicos', '/api/horarios')) or (self.command == 'POST' and url.path == '/api/mensagens')
            try:
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
            conteudo = json.dumps(resposta, ensure_ascii=False).encode('utf-8')
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
