"""
Painel do escritorio (so leitura) - abre no navegador deste computador.

    python PAINEL/servidor.py            http://127.0.0.1:8765  (usuario/senha: PAINEL_USUARIO / PAINEL_SENHA do .env)
    deploy\\iniciar_painel.bat           o mesmo, e abre o navegador

Mostra num lugar so:
- pedidos de calculo do e-mail (CALCULOS/: preparado = aguardando o OK da Dra. Faya, enviado, ignorado);
- prazos abertos (Notion, Prazos/Tarefas) e a fila de calculos (Notion, Fluxo RT);
- atalho para o FINANCEIRO (artefato no claude.ai).

So le. A unica acao e abrir no computador a pasta de um pedido ja conhecido (nunca um caminho vindo do navegador).
Escuta so em 127.0.0.1. Sem PAINEL_SENHA no .env, gera uma e grava no .env (mostra uma vez no terminal).
"""
import base64
import hmac
import json
import os
import re
import secrets
import sys
import threading
import time
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [RAIZ, os.path.join(RAIZ, 'NUCLEO'), os.path.join(RAIZ, 'INTEGRACOES')]
import ambiente  # noqa: E402,F401

try:
    sys.stdout.reconfigure(encoding='utf-8')
except (AttributeError, ValueError):
    pass

AQUI = os.path.dirname(os.path.abspath(__file__))
PORTA = int(os.getenv('PAINEL_PORTA') or 8765)
FINANCEIRO_URL = 'https://claude.ai/artifact/TLTNLuxv8MAJrQUy86fa4M'
CACHE_SEG = 90
_cache = {'em': 0, 'dados': None}
_trava = threading.Lock()
_PRAZO = re.compile(r'prazo[^0-9]{0,12}(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{2,4}))?', re.I)


# ------------------------------------------------------------------ senha

def credenciais():
    usuario = os.getenv('PAINEL_USUARIO') or 'faya'
    senha = os.getenv('PAINEL_SENHA')
    if not senha:
        senha = secrets.token_urlsafe(12)
        env = os.path.join(RAIZ, 'config', '.env')
        with open(env, 'a', encoding='utf-8') as f:
            f.write(f'\n# Painel local (PAINEL/servidor.py)\nPAINEL_USUARIO={usuario}\nPAINEL_SENHA={senha}\n')
        os.environ['PAINEL_USUARIO'], os.environ['PAINEL_SENHA'] = usuario, senha
        print(f'Senha do painel criada e gravada no config/.env -> usuário: {usuario}  senha: {senha}')
    return usuario, senha


# ------------------------------------------------------------------ dados

def prazo_do_assunto(texto, hoje=None):
    """'PRAZO DIA 11/11' -> date (ano corrente; se ja passou ha mais de 60 dias, ano seguinte). None se nao houver."""
    m = _PRAZO.search(texto or '')
    if not m:
        return None
    hoje = hoje or date.today()
    d, mth, a = int(m.group(1)), int(m.group(2)), m.group(3)
    ano = (int(a) + 2000 if len(a) == 2 else int(a)) if a else hoje.year
    try:
        dt = date(ano, mth, d)
    except ValueError:
        return None
    if not a and (hoje - dt).days > 60:
        dt = date(ano + 1, mth, d)
    return dt


def pedidos_calculo():
    try:
        with open(os.path.join(RAIZ, 'SAIDA', 'calculos', 'estado.json'), encoding='utf-8') as f:
            est = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        est = {}
    lista = []
    for mid, v in est.items():
        p = prazo_do_assunto(v.get('assunto'))
        lista.append({'id': mid, 'status': v.get('status'), 'de': v.get('de', ''), 'assunto': v.get('assunto', ''),
                      'recebido': v.get('data', ''), 'prazo': p.isoformat() if p else '',
                      'pendencias': len(v.get('pendencias') or []), 'motivo': v.get('motivo', ''),
                      'enviado_em': (v.get('enviado_em') or '')[:10], 'financeiro': v.get('financeiro', ''),
                      'tem_pasta': bool(v.get('pasta') and os.path.isdir(v['pasta']))})
    ordem = {'preparado': 0, 'novo': 1, 'enviado': 2, 'cancelado': 3, 'ignorado': 4}
    lista.sort(key=lambda x: (ordem.get(x['status'], 5), x['prazo'] or '9999', x['recebido']))
    return lista, est


def notion():
    if not os.getenv('NOTION_TOKEN'):
        return {'erro': 'Sem NOTION_TOKEN no config/.env.'}
    try:
        import notion_escritorio as ne
        prazos = ne.tarefas_abertas(n=200)
        col = ne.CAMPOS['calculos']['status']
        fila = ne.listar('calculos', n=200, filtro={'property': col, 'status': {'does_not_equal': 'Concluído'}})
        for x in prazos + fila:
            x.pop('_id', None)
        return {'prazos': prazos, 'fluxo_rt': fila}
    except Exception as e:  # noqa: BLE001
        return {'erro': f'Não consegui ler o Notion: {str(e)[:160]}'}


def coletar(forcar=False):
    with _trava:
        if not forcar and _cache['dados'] and time.time() - _cache['em'] < CACHE_SEG:
            return _cache['dados']
        pedidos, _ = pedidos_calculo()
        dados = {'gerado_em': datetime.now().strftime('%d/%m/%Y %H:%M'), 'hoje': date.today().isoformat(),
                 'pedidos': pedidos, 'notion': notion(), 'financeiro_url': FINANCEIRO_URL,
                 'gmail_ok': os.path.exists(os.path.join(RAIZ, 'config', 'token_gmail_calculos.json'))}
        _cache.update(em=time.time(), dados=dados)
        return dados


# ------------------------------------------------------------------ HTTP

class Painel(BaseHTTPRequestHandler):
    server_version = 'PainelFaya/1'

    def log_message(self, *_):
        pass

    def _autorizado(self):
        usuario, senha = credenciais()
        h = self.headers.get('Authorization', '')
        if h.startswith('Basic '):
            try:
                u, _, s = base64.b64decode(h[6:]).decode('utf-8').partition(':')
                if hmac.compare_digest(u, usuario) and hmac.compare_digest(s, senha):
                    return True
            except Exception:  # noqa: BLE001
                pass
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Painel Faya Barreiros", charset="UTF-8"')
        self.end_headers()
        return False

    def _enviar(self, codigo, corpo, tipo='application/json; charset=utf-8'):
        b = corpo if isinstance(corpo, bytes) else corpo.encode('utf-8')
        self.send_response(codigo)
        self.send_header('Content-Type', tipo)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if not self._autorizado():
            return
        u = urlparse(self.path)
        if u.path in ('/', '/index.html'):
            with open(os.path.join(AQUI, 'index.html'), 'rb') as f:
                return self._enviar(200, f.read(), 'text/html; charset=utf-8')
        if u.path == '/api/dados':
            forcar = parse_qs(u.query).get('atualizar') == ['1']
            return self._enviar(200, json.dumps(coletar(forcar), ensure_ascii=False))
        self._enviar(404, json.dumps({'erro': 'não encontrado'}))

    def do_POST(self):
        if not self._autorizado():
            return
        u = urlparse(self.path)
        if u.path == '/api/abrir-pasta':
            mid = (parse_qs(u.query).get('id') or [''])[0]
            _, est = pedidos_calculo()
            pasta = (est.get(mid) or {}).get('pasta')   # so pasta registrada pela rotina, nunca caminho do navegador
            if pasta and os.path.isdir(pasta) and hasattr(os, 'startfile'):
                os.startfile(pasta)  # noqa: S606 - pasta conhecida, abre no Explorer deste computador
                return self._enviar(200, json.dumps({'ok': True}))
            return self._enviar(404, json.dumps({'erro': 'Pasta não encontrada.'}))
        self._enviar(404, json.dumps({'erro': 'não encontrado'}))


def main():
    usuario, _ = credenciais()
    srv = ThreadingHTTPServer(('127.0.0.1', PORTA), Painel)
    print(f'Painel no ar: http://127.0.0.1:{PORTA}  (usuário: {usuario}; senha no config/.env, PAINEL_SENHA)')
    print('Ctrl+C para parar.')
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
