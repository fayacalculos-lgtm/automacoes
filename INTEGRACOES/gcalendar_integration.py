"""
Integracao com o Google Agenda do escritorio.

Cria, lista e remove eventos (prazos, audiencias, reunioes de fechamento). Nao convida ninguem:
os eventos nascem sem participantes e sem envio de e-mail (sendUpdates='none'), para a Regra de ouro
(nada sai ao cliente sem revisao humana) continuar valendo.

Credenciais (nunca versionar):
  config/credentials_gcalendar.json   cliente OAuth "App para computador" do Google Cloud do escritorio
  config/token_gcalendar.json         criado sozinho na 1a autorizacao
Caminhos alternativos: GCAL_CREDENCIAIS e GCAL_TOKEN no config/.env.
Agenda usada: GCAL_AGENDA no config/.env (padrao 'primary').

Primeira vez (abre o navegador para o login na conta do escritorio):
  python INTEGRACOES/gcalendar_integration.py autorizar
Depois:
  python INTEGRACOES/gcalendar_integration.py proximos [dias]
"""
import os
import sys
from datetime import datetime, timedelta, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
FUSO = 'America/Bahia'
COR_ATRASADO = '11'   # vermelho (Tomato) do Google Agenda


def _caminho(var, padrao):
    return os.getenv(var) or os.path.join(RAIZ, 'config', padrao)


def arquivo_credenciais():
    return _caminho('GCAL_CREDENCIAIS', 'credentials_gcalendar.json')


def arquivo_token():
    return _caminho('GCAL_TOKEN', 'token_gcalendar.json')


def agenda_id():
    return os.getenv('GCAL_AGENDA') or 'primary'


def configurado():
    """True se ha como autenticar (token ja salvo ou cliente OAuth para o 1o login)."""
    return os.path.exists(arquivo_token()) or os.path.exists(arquivo_credenciais())


def _credenciais(permitir_login=True):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    creds = None
    if os.path.exists(arquivo_token()):
        creds = Credentials.from_authorized_user_file(arquivo_token(), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        if not permitir_login:
            raise RuntimeError('Google Agenda sem token valido. Rode: python INTEGRACOES/gcalendar_integration.py autorizar')
        if not os.path.exists(arquivo_credenciais()):
            raise RuntimeError(f'Falta {arquivo_credenciais()} (cliente OAuth do Google Cloud do escritorio).')
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(arquivo_credenciais(), SCOPES)
        creds = flow.run_local_server(port=0)
    with open(arquivo_token(), 'w', encoding='utf-8') as f:
        f.write(creds.to_json())
    return creds


def _servico(permitir_login=True):
    from googleapiclient.discovery import build
    return build('calendar', 'v3', credentials=_credenciais(permitir_login), cache_discovery=False)


def conta():
    """Fuso da agenda autorizada (o escopo calendar.events nao le o nome da agenda)."""
    return _servico().events().list(calendarId=agenda_id(), maxResults=1).execute().get('timeZone')


def criar_evento(titulo, inicio, fim=None, descricao='', local='', dia_inteiro=False, lembretes_min=(1440, 60), chave=None, atrasado=False):
    """Cria o evento na agenda do escritorio. `inicio`/`fim` sao datetime (ou date se dia_inteiro).
    Sem `fim`: 1 hora depois (ou o mesmo dia). Nao convida ninguem. Retorna {'id', 'link'}.
    `chave` (ex.: URL do Notion) evita duplicar: se ja existe evento com ela, devolve o existente
    com 'ja_existia': True."""
    if chave:
        achados = _servico().events().list(calendarId=agenda_id(), privateExtendedProperty=f'chave={chave}',
                                           maxResults=1).execute().get('items', [])
        if achados:
            return {'id': achados[0]['id'], 'link': achados[0].get('htmlLink'), 'ja_existia': True}
    if dia_inteiro:
        fim = fim or inicio
        corpo_tempo = {'start': {'date': inicio.strftime('%Y-%m-%d')},
                       'end': {'date': (fim + timedelta(days=1)).strftime('%Y-%m-%d')}}
    else:
        fim = fim or inicio + timedelta(hours=1)
        corpo_tempo = {'start': {'dateTime': inicio.isoformat(), 'timeZone': FUSO},
                       'end': {'dateTime': fim.isoformat(), 'timeZone': FUSO}}
    corpo = {'summary': titulo, 'description': descricao, 'location': local, **corpo_tempo,
             'reminders': {'useDefault': False,
                           'overrides': [{'method': 'popup', 'minutes': m} for m in lembretes_min]}}
    if atrasado:
        corpo['colorId'] = COR_ATRASADO
        corpo['summary'] = 'ATRASADO | ' + titulo
    if chave:
        corpo['extendedProperties'] = {'private': {'chave': chave}}
    ev = _servico().events().insert(calendarId=agenda_id(), body=corpo, sendUpdates='none').execute()
    return {'id': ev.get('id'), 'link': ev.get('htmlLink')}


def listar_proximos(dias=7):
    """Eventos dos proximos `dias` dias, em ordem."""
    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    res = _servico().events().list(
        calendarId=agenda_id(), timeMin=agora.isoformat() + 'Z',
        timeMax=(agora + timedelta(days=dias)).isoformat() + 'Z',
        singleEvents=True, orderBy='startTime', maxResults=100).execute()
    return res.get('items', [])


def remover_evento(evento_id):
    _servico().events().delete(calendarId=agenda_id(), eventId=evento_id, sendUpdates='none').execute()


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'autorizar':
        print('Abrindo o navegador para autorizar o Google Agenda do escritorio...')
        print('Agenda autorizada (fuso):', conta())
        print('Token salvo em', arquivo_token())
    elif cmd == 'proximos':
        for ev in listar_proximos(int(sys.argv[2]) if len(sys.argv) > 2 else 7):
            ini = ev['start'].get('dateTime') or ev['start'].get('date')
            print(ini, '-', ev.get('summary', '(sem titulo)'))
    else:
        print('Uso: python INTEGRACOES/gcalendar_integration.py autorizar | proximos [dias]')
        print('Configurado:', configurado(), '| credenciais:', arquivo_credenciais())
