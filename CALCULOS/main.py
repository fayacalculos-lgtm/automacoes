"""
CALCULOS - pedidos de calculo que chegam por e-mail (Dra. Faya). Roda todo dia pela rotina /rotina-calculos.

    python CALCULOS/main.py autorizar                 1a vez: login no Google da caixa que recebe os pedidos
    python CALCULOS/main.py novos [--dias 3]          baixa os pedidos novos com anexo -> pasta CALCULOS 2026
    python CALCULOS/main.py preparar <ID>             rascunho da resposta ao parceiro + e-mail-resumo para a Dra. Faya
    python CALCULOS/main.py ignorar <ID> --motivo "..."   nao e pedido de calculo
    python CALCULOS/main.py aprovacoes                le os "OK" da Dra. Faya e ENVIA o rascunho aprovado
    python CALCULOS/main.py status                    situacao de todos os pedidos

Ciclo de um pedido: novo -> preparado (rascunho + resumo enviado a ela) -> aprovado/enviado | ignorado.

Travas:
- Nada vai ao parceiro sem o "OK" dela: ela responde o e-mail-resumo comecando com "OK". Se ela editar o rascunho
  antes, sai a versao editada (o Gmail envia o rascunho como esta).
- O unico e-mail enviado sem OK e o resumo para ela mesma (CALCULOS_AVISO_PARA, padrao: a propria caixa).
- O numero oficial do calculo e do software da Dra. Faya: a rotina marca [CONFERIR] onde ele entra, e `preparar`
  lista no resumo toda pendencia ({{campo}}, [CONFERIR]...) que ainda estiver no texto, para ela resolver antes do OK.
- Um login proprio na caixa dos pedidos (faya.calculos@gmail.com; CALCULOS_CONTA no .env), token
  config/token_gmail_calculos.json, escopos gmail.readonly + gmail.compose. O modulo INTEGRACOES/gmail_integration.py
  continua sem envio, como manda a regra dele.

Pasta de cada pedido: <PASTA_CLIENTES_RAIZ>/CALCULOS 2026/<AAAA-MM-DD - remetente - assunto>/
    01_RECEBIDO/   anexos do e-mail + pedido.json
    02_PREPARADO/  o que a rotina produz: resposta_parceiro.md (corpo), resumo.md (para a Dra. Faya),
                   anexos a enviar (relatorio .docx/.pdf, planilha...). So o que estiver aqui vai no e-mail.
"""
import argparse
import base64
import email
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import parseaddr

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [RAIZ, os.path.join(RAIZ, 'NUCLEO'), os.path.join(RAIZ, 'INTEGRACOES')]
import ambiente  # noqa: E402,F401

try:
    sys.stdout.reconfigure(encoding='utf-8')
except (AttributeError, ValueError):
    pass

# Um so login, na caixa que recebe os pedidos (faya.calculos@gmail.com): ler + rascunho/envio.
SCOPE_ENVIO = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.compose']
TOKEN_ENVIO = os.path.join(RAIZ, 'config', 'token_gmail_calculos.json')
MARCA = '[CALCULO #{id}]'
TERMOS = ['cálculo', 'calculo', 'cálculos', 'calculos', 'liquidação', 'liquidacao', 'RMI', 'planejamento',
          'revisão', 'revisao', 'parecer', 'atualização', 'atualizacao', '"valor da causa"', '"cumprimento de sentença"',
          'atrasados', 'impugnação', 'impugnacao', 'contadoria', 'CNIS', 'calcular', 'análise', 'analise', 'analisar',
          'prazo', 'sucumbência', 'sucumbencia', 'honorários', 'honorarios', 'LOAS', 'emenda']
LIMITE_MB = 20


# ------------------------------------------------------------------ estado e pastas

def pasta_saida():
    p = os.path.join(RAIZ, 'SAIDA', 'calculos')
    os.makedirs(p, exist_ok=True)
    return p


def arq_estado():
    return os.path.join(pasta_saida(), 'estado.json')


def ler_estado():
    try:
        with open(arq_estado(), encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def salvar_estado(est):
    tmp = arq_estado() + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(est, f, ensure_ascii=False, indent=1)
    os.replace(tmp, arq_estado())


def raiz_calculos():
    raiz = os.getenv('PASTA_CLIENTES_RAIZ') or os.path.join(RAIZ, 'CLIENTES')
    return os.path.join(raiz, os.getenv('CALCULOS_PASTA') or 'CALCULOS 2026')


def limpo(s, n=60):
    s = re.sub(r'[<>:"/\\|?*\r\n\t]', ' ', s or '')
    return re.sub(r'\s+', ' ', s).strip()[:n].strip() or 'sem assunto'


def nome_pasta(data_iso, remetente, assunto):
    return f"{data_iso} - {limpo(remetente, 40)} - {limpo(assunto, 60)}"


# ------------------------------------------------------------------ regras puras (testadas)

def consulta(dias):
    """Busca do Gmail: anexos recentes com termo de calculo, fora o que a propria caixa mandou."""
    return f'newer_than:{int(dias)}d has:attachment -from:me (' + ' OR '.join(TERMOS) + ')'


def primeira_linha_util(texto):
    """Primeira linha do que a pessoa escreveu (antes da citacao "Em ... escreveu:" / ">")."""
    for linha in (texto or '').replace('\r', '').split('\n'):
        l = linha.strip()
        if not l:
            continue
        if l.startswith('>') or re.match(r'^(em|on)\s.+(escreveu|wrote)', l, re.I) or l.startswith('-----'):
            return ''
        return l
    return ''


def eh_ok(texto):
    """A resposta dela aprova se a primeira linha util comeca com OK (ok, Ok., OK pode enviar...)."""
    return bool(re.match(r'^ok\b', primeira_linha_util(texto), re.I))


def texto_arquivo(caminho):
    """Texto de .md/.txt/.docx (para achar pendencia antes de anexar). Outros tipos: vazio."""
    ext = os.path.splitext(caminho)[1].lower()
    try:
        if ext in ('.md', '.txt'):
            with open(caminho, encoding='utf-8', errors='replace') as f:
                return f.read()
        if ext == '.docx':
            import docx
            d = docx.Document(caminho)
            return '\n'.join(p.text for p in d.paragraphs)
    except Exception:  # noqa: BLE001
        return ''
    return ''


def pendencias(texto):
    return sorted(set(re.findall(r'\{\{\s*[A-Za-z0-9_]+\s*\}\}|\[\s*(?:CONFERIR|A CONFIRMAR|NARRAR|INSERIR IMAGEM)[^\]]*\]',
                                 texto or '', re.I)))


# ------------------------------------------------------------------ Gmail

def _svc_leitura():
    """Mesmo login do envio (config/token_gmail_calculos.json), na caixa que recebe os pedidos."""
    return _svc_envio()


def _svc_envio(permitir_login=False):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_file(TOKEN_ENVIO, SCOPE_ENVIO) if os.path.exists(TOKEN_ENVIO) else None
    if creds and not creds.valid and creds.refresh_token:
        creds.refresh(Request())
        open(TOKEN_ENVIO, 'w', encoding='utf-8').write(creds.to_json())
    if not (creds and creds.valid):
        if not permitir_login:
            raise SystemExit('Envio não autorizado. Rode uma vez: python CALCULOS/main.py autorizar')
        import gmail_leitura as gl
        from google_auth_oauthlib.flow import InstalledAppFlow
        creds = InstalledAppFlow.from_client_secrets_file(gl._cliente_oauth(), SCOPE_ENVIO).run_local_server(port=0)
        open(TOKEN_ENVIO, 'w', encoding='utf-8').write(creds.to_json())
    return build('gmail', 'v1', credentials=creds, cache_discovery=False)


def _txt(v):
    return str(make_header(decode_header(v or '')))


def _corpo(msg):
    texto, html = '', ''
    for p in msg.walk() if msg.is_multipart() else [msg]:
        if p.get_filename():
            continue
        try:
            t = p.get_payload(decode=True).decode(p.get_content_charset() or 'utf-8', 'replace')
        except Exception:  # noqa: BLE001
            continue
        if p.get_content_type() == 'text/plain' and not texto:
            texto = t
        elif p.get_content_type() == 'text/html' and not html:
            html = re.sub(r'<br\s*/?>|</p>|</div>', '\n', t, flags=re.I)
            html = re.sub(r'<[^>]+>', ' ', html)
    return (texto or html).strip()


def _mensagem(svc, mid):
    raw = svc.users().messages().get(userId='me', id=mid, format='raw').execute()
    msg = email.message_from_bytes(base64.urlsafe_b64decode(raw['raw'] + '=' * (-len(raw['raw']) % 4)))
    return raw, msg


def _anexos(msg):
    for p in msg.walk():
        nome = p.get_filename()
        if nome:
            yield _txt(nome), p.get_payload(decode=True) or b''


# ------------------------------------------------------------------ comandos

def cmd_autorizar(_a):
    svc = _svc_envio(permitir_login=True)
    conta = svc.users().getProfile(userId='me').execute().get('emailAddress')
    print('Autorizado (leitura + rascunho/envio) na conta:', conta)
    esperada = os.getenv('CALCULOS_CONTA') or 'faya.calculos@gmail.com'
    if conta.lower() != esperada.lower():
        print(f'ATENÇÃO: os pedidos de cálculo chegam em {esperada}. Rode de novo e entre com essa conta.')


def cmd_novos(a):
    svc = _svc_leitura()
    est = ler_estado()
    ids, tok = [], None
    while True:
        r = svc.users().messages().list(userId='me', q=consulta(a.dias), pageToken=tok, maxResults=100).execute()
        ids += [m['id'] for m in r.get('messages', [])]
        tok = r.get('nextPageToken')
        if not tok or len(ids) >= 200:
            break
    novos = []
    for mid in ids:
        if mid in est:
            continue
        raw, msg = _mensagem(svc, mid)
        de_nome, de_email = parseaddr(_txt(msg.get('From')))
        assunto = _txt(msg.get('Subject'))
        quando = datetime.fromtimestamp(int(raw.get('internalDate', '0')) / 1000).date().isoformat()
        pasta = os.path.join(raiz_calculos(), nome_pasta(quando, de_nome or de_email, assunto))
        if a.simular:
            novos.append({'id': mid, 'data': quando, 'de': de_email, 'assunto': assunto,
                          'anexos': [n for n, _ in _anexos(msg)], 'pasta_que_seria_criada': pasta})
            continue
        rec = os.path.join(pasta, '01_RECEBIDO')
        os.makedirs(rec, exist_ok=True)
        os.makedirs(os.path.join(pasta, '02_PREPARADO'), exist_ok=True)
        os.makedirs(os.path.join(pasta, '03_INTERNO'), exist_ok=True)
        arquivos = []
        for nome, dados in _anexos(msg):
            alvo = os.path.join(rec, limpo(nome, 120))
            if not os.path.exists(alvo):
                with open(alvo, 'wb') as f:
                    f.write(dados)
            arquivos.append(os.path.basename(alvo))
        pedido = {'id': mid, 'thread_id': raw.get('threadId'), 'message_id_header': msg.get('Message-ID'),
                  'references': msg.get('References') or '', 'de_nome': de_nome, 'de_email': de_email,
                  'assunto': assunto, 'data': quando, 'corpo': _corpo(msg)[:20000], 'anexos': arquivos,
                  'pasta': pasta}
        with open(os.path.join(rec, 'pedido.json'), 'w', encoding='utf-8') as f:
            json.dump(pedido, f, ensure_ascii=False, indent=1)
        est[mid] = {'status': 'novo', 'pasta': pasta, 'de': de_email, 'assunto': assunto, 'data': quando,
                    'em': datetime.now().isoformat(timespec='seconds')}
        salvar_estado(est)
        novos.append(est[mid] | {'id': mid, 'anexos': arquivos})
    print(json.dumps({'novos': novos}, ensure_ascii=False, indent=1))


def _pedido(mid):
    est = ler_estado()
    if mid not in est:
        raise SystemExit(f'Pedido {mid} não está no estado. Rode "novos" antes.')
    with open(os.path.join(est[mid]['pasta'], '01_RECEBIDO', 'pedido.json'), encoding='utf-8') as f:
        return est, json.load(f)


def _raw(msg):
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


def _anexar(msg, arquivos):
    import mimetypes
    total = 0
    for caminho in arquivos:
        total += os.path.getsize(caminho)
        if total > LIMITE_MB * 1024 * 1024:
            raise SystemExit(f'Anexos passam de {LIMITE_MB} MB: reduza os arquivos em 02_PREPARADO.')
        tipo, _ = mimetypes.guess_type(caminho)
        principal, sub = (tipo or 'application/octet-stream').split('/', 1)
        with open(caminho, 'rb') as f:
            msg.add_attachment(f.read(), maintype=principal, subtype=sub, filename=os.path.basename(caminho))


def cmd_preparar(a):
    est, ped = _pedido(a.id)
    if est[a.id]['status'] not in ('novo', 'preparado'):
        raise SystemExit(f"Pedido já está como {est[a.id]['status']}.")
    prep = os.path.join(ped['pasta'], '02_PREPARADO')
    resp_md, resumo_md = os.path.join(prep, 'resposta_parceiro.md'), os.path.join(prep, 'resumo.md')
    for p in (resp_md, resumo_md):
        if not os.path.exists(p):
            raise SystemExit(f'Falta {p}: a rotina tem de escrever a resposta e o resumo antes.')
    resposta = open(resp_md, encoding='utf-8').read().strip()
    resumo = open(resumo_md, encoding='utf-8').read().strip()
    anexos = sorted(os.path.join(prep, f) for f in os.listdir(prep)
                    if f not in ('resposta_parceiro.md', 'resumo.md') and not f.startswith(('~$', '.'))
                    and os.path.isfile(os.path.join(prep, f)))
    pend = pendencias(resposta) + [f'{os.path.basename(x)}: {", ".join(p[:3])}' for x in anexos
                                   for p in [pendencias(texto_arquivo(x))] if p]
    svc = _svc_envio()
    conta = svc.users().getProfile(userId='me').execute().get('emailAddress')

    # 1) rascunho da resposta ao parceiro, na mesma conversa
    if est[a.id].get('draft_id'):
        try:
            svc.users().drafts().delete(userId='me', id=est[a.id]['draft_id']).execute()
        except Exception:  # noqa: BLE001
            pass
    m = EmailMessage()
    m['To'] = ped['de_email']
    m['Subject'] = ped['assunto'] if ped['assunto'].lower().startswith('re:') else 'Re: ' + ped['assunto']
    if ped.get('message_id_header'):
        m['In-Reply-To'] = ped['message_id_header']
        m['References'] = (ped.get('references', '') + ' ' + ped['message_id_header']).strip()
    m.set_content(resposta)
    _anexar(m, anexos)
    draft = svc.users().drafts().create(userId='me', body={'message': {'raw': _raw(m), 'threadId': ped['thread_id']}}).execute()

    # 2) resumo para a Dra. Faya (unico envio sem OK: e para ela mesma)
    para = os.getenv('CALCULOS_AVISO_PARA') or conta
    r = EmailMessage()
    r['To'] = para
    r['Subject'] = f"{MARCA.format(id=a.id[-8:])} Revisar: {ped['assunto']} ({ped['de_nome'] or ped['de_email']})"
    corpo = [resumo, '', '---',
             f"Pedido de: {ped['de_nome']} <{ped['de_email']}> em {ped['data']}",
             f"Pasta: {ped['pasta']}",
             f"Anexos que vão na resposta: {', '.join(os.path.basename(x) for x in anexos) or 'nenhum'}",
             ('PENDÊNCIAS ainda no texto: ' + '; '.join(pend)) if pend else 'Sem pendências marcadas no texto.',
             '', 'A resposta ao parceiro está nos seus RASCUNHOS, na conversa dele. Pode editar lá.',
             'Para ENVIAR: responda este e-mail começando com OK. Para não enviar, não responda (ou apague o rascunho).',
             '', '--- Resposta que irá ao parceiro ---', resposta]
    r.set_content('\n'.join(corpo))
    _anexar(r, anexos)
    enviado = svc.users().messages().send(userId='me', body={'raw': _raw(r)}).execute()

    est[a.id].update(status='preparado', draft_id=draft['id'], resumo_id=enviado['id'],
                     resumo_thread=enviado.get('threadId'), aviso_para=para, pendencias=pend,
                     preparado_em=datetime.now().isoformat(timespec='seconds'),
                     valor=a.valor, servico=a.servico)
    salvar_estado(est)
    print(f"Preparado: rascunho {draft['id']} + resumo enviado para {para}. Pendências: {len(pend)}")


def cmd_ignorar(a):
    est = ler_estado()
    if a.id not in est:
        raise SystemExit('Pedido não encontrado.')
    est[a.id].update(status='ignorado', motivo=a.motivo, em=datetime.now().isoformat(timespec='seconds'))
    salvar_estado(est)
    print('Ignorado:', a.id, '-', a.motivo)


def cmd_aprovacoes(_a):
    est = ler_estado()
    pend = {k: v for k, v in est.items() if v.get('status') == 'preparado'}
    if not pend:
        print(json.dumps({'enviados': [], 'aguardando': 0}))
        return
    svc = _svc_envio()
    enviados, aguardando = [], []
    for mid, v in pend.items():
        th = svc.users().threads().get(userId='me', id=v['resumo_thread'], format='full').execute()
        aprovado = False
        for m in th.get('messages', []):
            if m['id'] == v['resumo_id']:
                continue
            texto = _texto_api(m)
            if eh_ok(texto):
                aprovado = True
                break
        if not aprovado:
            aguardando.append(mid)
            continue
        try:
            svc.users().drafts().get(userId='me', id=v['draft_id'], format='minimal').execute()
        except Exception:  # noqa: BLE001
            v.update(status='cancelado', motivo='rascunho apagado ou enviado à mão antes do OK')
            salvar_estado(est)
            print(f'{mid}: rascunho não existe mais; marcado como cancelado, nada enviado.')
            continue
        r = svc.users().drafts().send(userId='me', body={'id': v['draft_id']}).execute()
        v.update(status='enviado', enviado_id=r.get('id'), enviado_em=datetime.now().isoformat(timespec='seconds'),
                 financeiro='pendente' if v.get('valor') else 'sem valor')
        salvar_estado(est)
        notion = _fluxo_rt(v)
        enviados.append({'id': mid, 'de': v['de'], 'assunto': v['assunto'], 'pasta': v['pasta'],
                         'valor': v.get('valor'), 'servico': v.get('servico'), 'notion': notion})
    print(json.dumps({'enviados': enviados, 'aguardando': len(aguardando)}, ensure_ascii=False, indent=1))


def _texto_api(m):
    def partes(p):
        if p.get('mimeType') == 'text/plain' and p.get('body', {}).get('data'):
            yield base64.urlsafe_b64decode(p['body']['data'] + '===').decode('utf-8', 'replace')
        for q in p.get('parts', []) or []:
            yield from partes(q)
    return next(partes(m.get('payload', {})), m.get('snippet', ''))


def _fluxo_rt(v):
    """Lanca a entrega no Fluxo RT do Notion (so cria linha). Falha nao desfaz o envio: so avisa."""
    try:
        import notion_escritorio as ne
        r = ne.criar('calculos', {'titulo': f"{v['de']} - {v['assunto']}"[:180], 'data_entrega': date.today().isoformat(),
                                  'etapa': None, 'status': 'Concluído'}, gravar=True)
        return r.get('url') or r.get('id') or 'não gravado'
    except Exception as e:  # noqa: BLE001
        return f'falhou: {str(e)[:80]}'


def cmd_financeiro_pendente(_a):
    """Enviados com valor ainda nao lancados no FINANCEIRO (a rotina das 7h lanca pelo ArtifactData)."""
    est = ler_estado()
    lista = [{'id': k, 'de': v['de'], 'assunto': v['assunto'], 'valor': v.get('valor'), 'servico': v.get('servico'),
              'enviado_em': v.get('enviado_em')} for k, v in est.items()
             if v.get('status') == 'enviado' and v.get('financeiro') == 'pendente']
    print(json.dumps({'a_lancar': lista}, ensure_ascii=False, indent=1))


def cmd_lancado(a):
    est = ler_estado()
    if est.get(a.id, {}).get('financeiro') != 'pendente':
        raise SystemExit('Esse pedido não está pendente de lançamento.')
    est[a.id]['financeiro'] = 'lançado ' + date.today().isoformat()
    salvar_estado(est)
    print('Marcado como lançado no FINANCEIRO:', a.id)


def cmd_status(_a):
    est = ler_estado()
    for mid, v in sorted(est.items(), key=lambda x: x[1].get('em', '')):
        print(f"{v['status']:<10} {v.get('data','')} {v.get('de','')[:30]:<30} {v.get('assunto','')[:50]}  ({mid})")
    if not est:
        print('Nenhum pedido ainda.')


def main():
    ap = argparse.ArgumentParser(description='Pedidos de cálculo por e-mail', epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('autorizar').set_defaults(f=cmd_autorizar)
    n = sub.add_parser('novos'); n.add_argument('--dias', type=int, default=3)
    n.add_argument('--simular', action='store_true', help='só lista, sem baixar nem criar pasta'); n.set_defaults(f=cmd_novos)
    p = sub.add_parser('preparar'); p.add_argument('id')
    p.add_argument('--valor', type=float, help='valor combinado com o parceiro, se constar no e-mail')
    p.add_argument('--servico', help='tipo do cálculo (ex.: Liquidação, Planejamento)'); p.set_defaults(f=cmd_preparar)
    i = sub.add_parser('ignorar'); i.add_argument('id'); i.add_argument('--motivo', required=True); i.set_defaults(f=cmd_ignorar)
    sub.add_parser('aprovacoes').set_defaults(f=cmd_aprovacoes)
    sub.add_parser('financeiro-pendente').set_defaults(f=cmd_financeiro_pendente)
    la = sub.add_parser('lancado'); la.add_argument('id'); la.set_defaults(f=cmd_lancado)
    sub.add_parser('status').set_defaults(f=cmd_status)
    a = ap.parse_args()
    a.f(a)


if __name__ == '__main__':
    main()
