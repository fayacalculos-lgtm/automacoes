"""Relatório dos prazos NÃO INICIADOS (Notion, aba Prazos/Tarefas), separado por contratante.

Lê o Notion ao vivo e grava o PDF em OneDrive\\DEMANDAS A FAZER (ou na pasta de DEMANDAS_A_FAZER_DIR no .env).
Uso: python CONTROLADORIA/relatorio_nao_iniciados.py
Uso interno: traz nomes de clientes finais; não repassar ao contratante sem revisar.
"""
import os, re, sys, shutil, unicodedata, collections
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from NUCLEO import ambiente  # noqa: E402,F401  (carrega o .env)
from INTEGRACOES import notion_integration as nt  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether  # noqa: E402

DB_PRAZOS = '40e7b6d5-dac6-839a-b006-01b423a08d5a'
DESTINO = os.environ.get('DEMANDAS_A_FAZER_DIR') or os.path.join(os.path.expanduser('~'), 'OneDrive', 'DEMANDAS A FAZER')
SAIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SAIDA')
BORDO, AZUL, VERDE, AMBAR, CINZA, VERM = '#7A1F3D', '#2B6CB0', '#2F9E6E', '#E0A030', '#6B6B6B', '#C0392B'
HOJE = date.today()


def _txt(p):
    if not p:
        return ''
    t = p.get('type')
    v = p.get(t)
    if t in ('title', 'rich_text'):
        return ''.join(x.get('plain_text', '') for x in v)
    if t in ('select', 'status'):
        return (v or {}).get('name', '')
    if t == 'date':
        return ((v or {}).get('start') or '')[:10]
    if t == 'people':
        return ', '.join(x.get('name', '') for x in v)
    if t == 'multi_select':
        return ', '.join(x.get('name', '') for x in v)
    return ''  # relation, formula etc.: não usado


def _flat(page):
    return {k.strip(): _txt(v) for k, v in page['properties'].items()}


def _sa(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def _nome(c):
    c = re.sub(r'\s+', ' ', c or '').strip()
    k = _sa(c).upper()
    if not k or k.startswith('PRAZO') or k in ('ACAO TRABALHISTA', 'ANA MOACIR'):
        return 'Sem contratante identificado'
    if k.startswith('CLIENTES FAYA') or k.startswith('CLIENTE FAYA') or k.startswith('DIRETO'):
        return 'Clientes diretos do escritório'
    return c


def coletar():
    filtro = {'property': 'Status', 'select': {'equals': 'Não iniciada'}}
    try:
        pags = nt.consultar_banco(DB_PRAZOS, filtro=filtro, limit=2000)
    except Exception:  # coluna pode ser do tipo status em vez de select
        filtro = {'property': 'Status', 'status': {'equals': 'Não iniciada'}}
        pags = nt.consultar_banco(DB_PRAZOS, filtro=filtro, limit=2000)
    g = collections.defaultdict(list)
    for p in pags:
        f = _flat(p)
        if f.get('Status') != 'Não iniciada':
            continue
        g[_nome(f.get('Contratante'))].append(dict(
            cliente=re.sub(r'\s+', ' ', f.get('Cliente', '')).strip() or '—', etapa=f.get('Fluxo RT') or '—',
            data=f.get('Data') or '', resp=f.get('Responsável') or '—', prio=f.get('Prioridade') or '',
            proc=f.get('Processo') or '', texto=re.sub(r'\s+', ' ', f.get('Texto', '')).strip()))
    return g


def dbr(d):
    return f'{d[8:10]}/{d[5:7]}/{d[:4]}' if d else '—'


def esc(t):
    return (t or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def situacao(d):
    if not d:
        return 'Sem data', CINZA
    dias = (HOJE - date.fromisoformat(d)).days
    if dias > 0:
        return f'Atrasado {dias} d', VERM
    if dias == 0:
        return 'Vence hoje', AMBAR
    return f'Em {-dias} d', AZUL


def gerar(g):
    ss = lambda **k: ParagraphStyle('x', fontName=k.pop('f', 'Helvetica'), **k)
    H1 = ss(f='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor(BORDO))
    H2 = ss(f='Helvetica-Bold', fontSize=11.5, leading=15, textColor=colors.HexColor(BORDO), spaceBefore=10, spaceAfter=3)
    SUB = ss(fontSize=9, leading=12, textColor=colors.HexColor(CINZA))
    SMALL = ss(fontSize=7.5, leading=10, textColor=colors.HexColor(CINZA))
    CEL = ss(fontSize=7.8, leading=9.6)
    CELW = ss(f='Helvetica-Bold', fontSize=7.8, leading=9.6, textColor=colors.white)

    def tab(head, rows, widths):
        t = Table([[Paragraph(h, CELW) for h in head]] + rows, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(BORDO)),
                               ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F6F1F3')]),
                               ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 3),
                               ('BOTTOMPADDING', (0, 0), (-1, -1), 3), ('LEFTPADDING', (0, 0), (-1, -1), 4)]))
        return t

    def key(it):
        return it['data'] or '9999'

    ordem = sorted(g, key=lambda c: (-len(g[c]), c))
    total = sum(len(v) for v in g.values())
    atr = sum(1 for v in g.values() for t in v if t['data'] and t['data'] < HOJE.isoformat())
    E = [Paragraph('Prazos não iniciados por contratante', H1),
         Paragraph(f'Faya Barreiros Advocacia · Notion, aba Prazos/Tarefas · posição em {HOJE:%d/%m/%Y}', SUB), Spacer(1, 8),
         Paragraph(f'<b>{total}</b> prazos não iniciados, de <b>{len(g)}</b> contratantes; <b>{atr}</b> com data já vencida.', ss(fontSize=10, leading=14)),
         Spacer(1, 6)]
    resumo = []
    for c in ordem:
        v = g[c]
        a = sum(1 for t in v if t['data'] and t['data'] < HOJE.isoformat())
        d = [t['data'] for t in v if t['data']]
        resumo.append([Paragraph(esc(c), CEL), Paragraph(str(len(v)), CEL), Paragraph(str(a), CEL), Paragraph(dbr(min(d)) if d else '—', CEL)])
    E.append(tab(['Contratante', 'Não iniciados', 'Vencidos', 'Data mais antiga'], resumo, [8.5 * cm, 2.6 * cm, 2.2 * cm, 3.2 * cm]))
    E.append(Spacer(1, 6))
    E.append(Paragraph('A coluna Data de Prazos/Tarefas pode ser a data de entrada e não o vencimento real: confirmar antes de cobrar os "vencidos".', SMALL))
    for c in ordem:
        v = sorted(g[c], key=key)
        rows = []
        for t in v:
            s, cor = situacao(t['data'])
            obs = esc(t['texto'])[:140]
            if t['proc']:
                obs = f'Proc. {esc(t["proc"])}. ' + obs
            rows.append([Paragraph(esc(t['cliente']), CEL), Paragraph(esc(t['etapa']), CEL), Paragraph(dbr(t['data']), CEL),
                         Paragraph(f'<font color="{cor}"><b>{s}</b></font>', CEL), Paragraph(esc(t['resp']), CEL), Paragraph(obs or '—', CEL)])
        E.append(KeepTogether([Paragraph(f'{esc(c)} · {len(v)} não iniciado(s)', H2),
                               tab(['Cliente', 'Etapa', 'Data', 'Situação', 'Responsável', 'Observação'], rows,
                                   [4.6 * cm, 2.6 * cm, 1.9 * cm, 2.2 * cm, 2.4 * cm, 3.7 * cm])]))

    def rodape(cv, d):
        cv.saveState(); cv.setFont('Helvetica', 7); cv.setFillColor(colors.HexColor(CINZA))
        cv.drawString(1.8 * cm, 1.1 * cm, 'Faya Barreiros Sociedade Individual de Advocacia · Prazos não iniciados · uso interno')
        cv.drawRightString(A4[0] - 1.8 * cm, 1.1 * cm, f'Página {d.page}'); cv.restoreState()

    os.makedirs(SAIDA, exist_ok=True)
    nome = f'Prazos_Nao_Iniciados_por_Contratante_{HOJE:%Y-%m-%d}.pdf'
    local = os.path.join(SAIDA, nome)
    SimpleDocTemplate(local, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.6 * cm, bottomMargin=1.8 * cm,
                      title='Prazos não iniciados por contratante').build(E, onFirstPage=rodape, onLaterPages=rodape)
    os.makedirs(DESTINO, exist_ok=True)
    dest = os.path.join(DESTINO, nome)
    shutil.copyfile(local, dest)
    return dest, total, len(g), atr


if __name__ == '__main__':
    dest, total, nc, atr = gerar(coletar())
    print(f'{total} prazos não iniciados, {nc} contratantes, {atr} vencidos\nsalvo em: {dest}')
