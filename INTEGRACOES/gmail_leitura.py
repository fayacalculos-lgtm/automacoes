"""
Leitura do Gmail do escritorio via IMAP - SOMENTE LEITURA, para acompanhar prazos administrativos
(INSS, orgaos e calculos). Nao envia, nao apaga, nao move e nao marca como lido (usa BODY.PEEK).

Configuracao (config/.env, nunca no chat nem no git). Uma ou mais contas, numeradas:
  EMAIL_1_USER=fayabarreiros@gmail.com
  EMAIL_1_SENHA=<senha de aplicativo de 16 letras>
  EMAIL_1_HOST=imap.gmail.com        (opcional; padrao Gmail. Outlook: outlook.office365.com)
  EMAIL_2_USER=<email das notificacoes>  ... e assim por diante
Gmail: conta Google -> Seguranca -> Verificacao em duas etapas -> Senhas de app.

Gmail por OAUTH (Google Cloud, sem senha; escopo gmail.readonly): coloque o cliente "App para computador"
em config/credentials_gmail.json e rode, uma vez por caixa:
  python INTEGRACOES/gmail_leitura.py autorizar 1      (abre o navegador; entre na conta da caixa 1)
Se EMAIL_n_SENHA estiver vazio e houver token OAuth da caixa n, o OAuth e usado; senao, IMAP.

Uso:  python INTEGRACOES/gmail_leitura.py [dias=30]
"""
import base64
import email
import imaplib
import os
import re
import sys
from datetime import date, datetime, timedelta
from email.header import decode_header, make_header

HOST = 'imap.gmail.com'
# Remetentes/termos de interesse (ajuste a vontade)
REMETENTES = ['inss.gov.br', 'meu.inss', 'gov.br', 'previdencia.gov.br', 'jus.br', 'dataprev', 'receita.fazenda']
TERMOS = ['exigência', 'exigencia', 'prazo', 'perícia', 'pericia', 'notificação', 'notificacao', 'intimação',
          'recurso administrativo', 'cálculo', 'calculo', 'conta', 'cumprimento de exigência', 'agendamento']
_DATA = re.compile(r'\b(\d{2})/(\d{2})/(\d{4})\b')


SCOPE_LEITURA = ['https://www.googleapis.com/auth/gmail.readonly']
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _token_oauth(n):
    return os.path.join(RAIZ, 'config', f'token_gmail_leitura_{n}.json')


def _cliente_oauth():
    return os.getenv('GMAIL_CREDENCIAIS') or os.path.join(RAIZ, 'config', 'credentials_gmail.json')


def _contas():
    """Contas EMAIL_n_*: (n, usuario, senha|None, host). Sem senha + token OAuth => OAuth."""
    contas = []
    for n in range(1, 10):
        u, s = os.getenv(f'EMAIL_{n}_USER'), os.getenv(f'EMAIL_{n}_SENHA')
        if u and s:
            contas.append((n, u, s.replace(' ', ''), os.getenv(f'EMAIL_{n}_HOST') or HOST))
        elif u and os.path.exists(_token_oauth(n)):
            contas.append((n, u, None, ''))
    if not contas:
        print('ERRO: nenhuma conta configurada (senha de app em EMAIL_n_SENHA ou OAuth: gmail_leitura.py autorizar n)')
        sys.exit(1)
    return contas


def autorizar(n):
    """1o login OAuth da caixa n (abre o navegador). Escopo somente leitura."""
    from google_auth_oauthlib.flow import InstalledAppFlow
    if not os.path.exists(_cliente_oauth()):
        print(f'Falta {_cliente_oauth()} (cliente OAuth "App para computador" do Google Cloud).')
        sys.exit(1)
    creds = InstalledAppFlow.from_client_secrets_file(_cliente_oauth(), SCOPE_LEITURA).run_local_server(port=0)
    open(_token_oauth(n), 'w', encoding='utf-8').write(creds.to_json())
    from googleapiclient.discovery import build
    mail = build('gmail', 'v1', credentials=creds, cache_discovery=False).users().getProfile(userId='me').execute()
    print('Autorizado:', mail.get('emailAddress'), '-> confira se e o mesmo de EMAIL_%s_USER' % n)


def _buscar_oauth(n, u, dias, max_msgs):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_file(_token_oauth(n), SCOPE_LEITURA)
    if not creds.valid:
        creds.refresh(Request())
        open(_token_oauth(n), 'w', encoding='utf-8').write(creds.to_json())
    svc = build('gmail', 'v1', credentials=creds, cache_discovery=False)
    desde = (date.today() - timedelta(days=dias)).strftime('%Y/%m/%d')
    q = f'after:{desde} (' + ' OR '.join([f'from:{r}' for r in REMETENTES] + [f'subject:"{t}"' for t in TERMOS]) + ')'
    ids, tok = [], None
    while len(ids) < max_msgs:
        r = svc.users().messages().list(userId='me', q=q, pageToken=tok, maxResults=100).execute()
        ids += [m['id'] for m in r.get('messages', [])]
        tok = r.get('nextPageToken')
        if not tok:
            break
    out = []
    for i in ids[:max_msgs]:
        raw = svc.users().messages().get(userId='me', id=i, format='raw').execute()['raw']
        msg = email.message_from_bytes(base64.urlsafe_b64decode(raw + '=' * (-len(raw) % 4)))
        out.append(_montar(u, msg))
    return out


def _txt(v):
    return str(make_header(decode_header(v or '')))


def _corpo(msg):
    for p in msg.walk() if msg.is_multipart() else [msg]:
        if p.get_content_type() in ('text/plain', 'text/html') and not p.get_filename():
            try:
                t = p.get_payload(decode=True).decode(p.get_content_charset() or 'utf-8', 'replace')
            except Exception:
                continue
            return re.sub(r'<[^>]+>|\s+', ' ', t)
    return ''


def _montar(u, msg):
    corpo = _corpo(msg)[:20000]
    datas = []
    for dd, mm, aa in _DATA.findall(corpo):
        try:
            dt = datetime(int(aa), int(mm), int(dd)).date()
            if dt >= date.today() - timedelta(days=1):
                datas.append(dt)
        except ValueError:
            pass
    return {'conta': u, 'data': msg.get('Date'), 'de': _txt(msg.get('From')), 'assunto': _txt(msg.get('Subject')),
            'datas_futuras': sorted(set(datas)), 'trecho': corpo[:300], 'corpo': corpo[:6000]}


def _buscar_conta(u, s, host, dias, max_msgs):
    desde = (date.today() - timedelta(days=dias)).strftime('%d-%b-%Y')
    out, vistos = [], set()
    m = imaplib.IMAP4_SSL(host)
    m.login(u, s)
    # Gmail: "Todos os e-mails" (pega arquivados); demais provedores: caixa de entrada
    if m.select('"[Gmail]/All Mail"', readonly=True)[0] != 'OK':
        m.select('INBOX', readonly=True)
    try:
        crit = [f'(SINCE {desde} FROM "{r}")' for r in REMETENTES] + [f'(SINCE {desde} SUBJECT "{t}")' for t in TERMOS]
        for c in crit:
            typ, d = m.search('UTF-8', c.encode('utf-8'))
            for num in (d[0].split() if d and d[0] else []):
                if num in vistos or len(vistos) >= max_msgs:
                    continue
                vistos.add(num)
                typ, raw = m.fetch(num, '(BODY.PEEK[])')
                msg = email.message_from_bytes(raw[0][1])
                out.append(_montar(u, msg))
    finally:
        m.logout()
    return out


def buscar(dias=30, max_msgs=200):
    """Mensagens dos ultimos `dias` de remetentes/termos de interesse em TODAS as contas configuradas."""
    out = []
    for n, u, s, host in _contas():
        try:
            out += _buscar_oauth(n, u, dias, max_msgs) if s is None else _buscar_conta(u, s, host, dias, max_msgs)
        except Exception as e:
            print(f'  Falha na conta {u}: {e}')
    return out


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))
    if len(sys.argv) > 2 and sys.argv[1] == 'autorizar':
        autorizar(int(sys.argv[2]))
        sys.exit(0)
    r = buscar(int(sys.argv[1]) if len(sys.argv) > 1 else 30)
    r.sort(key=lambda x: (x['datas_futuras'] or [date.max])[0])
    for x in r:
        print(x['conta'][:22], '|', (x['datas_futuras'][0].isoformat() if x['datas_futuras'] else 'sem data'), '|', x['de'][:40], '|', x['assunto'][:80])
    print(len(r), 'mensagens')
