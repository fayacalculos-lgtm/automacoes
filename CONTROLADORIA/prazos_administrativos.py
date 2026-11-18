"""
PRAZOS ADMINISTRATIVOS (INSS, orgaos e calculos) a partir do e-mail.

Le as caixas configuradas (INTEGRACOES/gmail_leitura.py, SOMENTE LEITURA), acha o prazo em cada
mensagem e calcula a data limite PRELIMINAR:
  1. data explicita no texto perto de "ate / prazo / data limite / vencimento / comparecer" -> usa ela;
  2. exigencia ou recurso administrativo sem data -> ciencia (data do e-mail) + 30 dias (padrao do
     INSS; CONFERIR no documento);
  3. sem nenhum dos dois -> "sem prazo identificado" (revisao humana).
Contagem administrativa (Lei 9.784/99, art. 66): dias corridos, exclui o dia da ciencia, inclui o do
vencimento; vencendo em dia sem expediente, vai para o proximo dia util. Sempre preliminar.

Prazo interno = D-N dias uteis do fatal (PRAZO_INTERNO_DIAS_ANTES).
Saida: SAIDA/controladoria/prazos_admin/AAAA-MM-DD.txt (+ console).
Aviso: so com --notificar, por WhatsApp INTERNO (AVISO_WHATSAPP no .env, numero do escritorio).
Nunca escreve ao cliente, nunca responde e-mail, nunca cria tarefa.

Uso:  python CONTROLADORIA/prazos_administrativos.py [dias=30] [--notificar]
"""
import os
import re
import sys
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'NUCLEO'))
sys.path.insert(0, os.path.join(RAIZ, 'INTEGRACOES'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ambiente  # noqa: E402,F401
import gmail_leitura  # noqa: E402
import prazos  # noqa: E402

PRAZO_PADRAO_DIAS = 30
DIAS_ANTES = int(os.getenv('PRAZO_INTERNO_DIAS_ANTES', '3') or 3)
_DATA = re.compile(r'\b(\d{2})/(\d{2})/(\d{4})\b')
_GATILHO = re.compile(r'(at[ée]|prazo|data limite|vencimento|compare[çc]|agendad|per[ií]cia|at[ée] o dia)', re.I)
_TIPOS = [
    ('Exigência', r'exig[êe]ncia'),
    ('Recurso administrativo', r'recurso'),
    ('Perícia/Agendamento', r'per[ií]cia|agendament|compare[çc]'),
    ('Cálculo', r'c[áa]lculo|conta de liquida'),
    ('Notificação', r'notifica|intima'),
]


def _tipo(txt):
    for nome, rx in _TIPOS:
        if re.search(rx, txt, re.I):
            return nome
    return 'Outro'


def _datas_com_gatilho(corpo):
    ach = []
    for m in _DATA.finditer(corpo):
        try:
            d = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            continue
        if _GATILHO.search(corpo[max(0, m.start() - 90):m.start()]):
            ach.append(d)
    return sorted(set(ach))


def _ciencia(x):
    try:
        return parsedate_to_datetime(x['data']).date()
    except Exception:
        return None


def _vencimento_corrido(ciencia, dias):
    fim = ciencia + timedelta(days=dias)
    while not prazos.dia_util(fim):
        fim += timedelta(days=1)
    return fim


# Ruido: andamentos judiciais (a Controladoria ja trata), avisos de seguranca/cobranca/apps
_RUIDO = re.compile(r'movimenta[çc][ãa]o processual|eproc:|alerta de seguran|partilhou|asaas|peticionamento eletr', re.I)


def analisar(msgs, hoje=None):
    hoje = hoje or date.today()
    itens = []
    for x in msgs:
        if _RUIDO.search(x['assunto']):
            continue
        corpo = x.get('corpo', '')
        tipo = _tipo(x['assunto'] + ' ' + corpo[:600])
        explicitas = [d for d in _datas_com_gatilho(corpo) if d >= hoje - timedelta(days=1)]
        ciencia = _ciencia(x)
        if explicitas:
            fatal, base = explicitas[0], 'data indicada no e-mail'
        elif tipo in ('Exigência', 'Recurso administrativo') and ciencia:
            fatal, base = _vencimento_corrido(ciencia, PRAZO_PADRAO_DIAS), f'ciência {ciencia:%d/%m/%Y} + {PRAZO_PADRAO_DIAS} dias (padrão, CONFERIR)'
        else:
            fatal, base = None, 'sem prazo identificado'
        interno = prazos.prazo_interno(fatal, DIAS_ANTES, hoje)[0] if fatal else None
        itens.append({**x, 'tipo': tipo, 'fatal': fatal, 'interno': interno, 'base': base,
                      'faltam': (fatal - hoje).days if fatal else None})
    itens.sort(key=lambda i: (i['fatal'] is None, i['fatal'] or date.max))
    return itens


def _linha(i):
    f = f"{i['fatal']:%d/%m/%Y}" if i['fatal'] else '—'
    n = f"{i['interno']:%d/%m/%Y}" if i['interno'] else '—'
    fal = '' if i['faltam'] is None else (f"{i['faltam']}d" if i['faltam'] >= 0 else f"VENCIDO há {-i['faltam']}d")
    return f"{f} | interno {n} | {fal:>12} | {i['tipo']:<22} | {i['conta'][:18]} | {i['assunto'][:70]} | {i['base']}"


def main(argv):
    from dotenv import load_dotenv  # noqa: F401  (ambiente ja carrega)
    dias = next((int(a) for a in argv if a.isdigit()), 30)
    itens = analisar(gmail_leitura.buscar(dias))
    linhas = [f'PRAZOS ADMINISTRATIVOS (PRELIMINAR) - gerado em {datetime.now():%d/%m/%Y %H:%M} - ultimos {dias} dias', '']
    linhas += [_linha(i) for i in itens] or ['Nenhuma mensagem encontrada.']
    texto = '\n'.join(linhas)
    pasta = os.path.join(RAIZ, 'SAIDA', 'controladoria', 'prazos_admin')
    os.makedirs(pasta, exist_ok=True)
    arq = os.path.join(pasta, f'{date.today():%Y-%m-%d}.txt')
    open(arq, 'w', encoding='utf-8').write(texto)
    print(texto, f'\n\nSalvo em {arq}')
    if '--notificar' in argv:
        import dapi_whatsapp
        dest = os.getenv('AVISO_WHATSAPP', '')
        urgentes = [i for i in itens if i['fatal'] and i['faltam'] <= 7]
        if not (dest and dapi_whatsapp.configurada()):
            print('Notificacao nao enviada: AVISO_WHATSAPP e/ou D-API nao configurados.')
        elif urgentes:
            msg = 'Prazos administrativos (preliminar, conferir):\n' + '\n'.join(
                f"- {i['fatal']:%d/%m} ({i['tipo']}) {i['assunto'][:60]}" for i in urgentes[:10])
            dapi_whatsapp.enviar_texto(dest, msg)
            print(f'Aviso interno enviado ({len(urgentes)} prazos em ate 7 dias).')
        else:
            print('Nenhum prazo em ate 7 dias; nada a notificar.')


if __name__ == '__main__':
    main(sys.argv[1:])
