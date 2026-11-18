"""
Asaas -> banco Transacoes Financeiras do Notion da Dra. Faya.

    python FINANCEIRO/main.py notion --dias 7              simulacao: o que iria para o Notion
    python FINANCEIRO/main.py notion --dias 7 --gravar     grava (confirmacao item a item)

O que vai:
- cobranca EMITIDA no periodo (criada no Asaas, ainda nao paga) -> linha Entrada, Pago = nao;
- pagamento RECEBIDO no periodo -> se a linha da cobranca foi criada por este sistema, marca Pago e a data
  NELA (so nela); senao, cria a linha ja paga.

Travas:
- simula por padrao; gravando, pergunta item a item (sem terminal = nao grava);
- uma linha por cobranca do Asaas (marcador ASAAS#<id> no Texto + registro local); nunca duplica;
- POSSIVEL DUPLICATA de lancamento manual (mesmo cliente, mesmo valor, data proxima) e avisada e pulada;
- so altera linha que ESTE sistema criou (registro local + marcador no Texto); linha da equipe nunca e tocada;
- Classificacao e Area so se configuradas (NOTION_FIN_CLASSIFICACAO / NOTION_FIN_AREA no .env): nao adivinho.
"""
import json
import os
import sys
from datetime import date, datetime, timedelta

import comum

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'INTEGRACOES'))

TOLERANCIA_DIAS = 5


def _registro():
    return os.path.join(comum.pasta_saida(None, 'notion'), '_notion_financeiro.json')


def _ler():
    try:
        with open(_registro(), encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _salvar(reg):
    with open(_registro(), 'w', encoding='utf-8') as f:
        json.dump(reg, f, ensure_ascii=False, indent=1)


def _perguntar(texto):
    try:
        return input(texto).strip().lower()
    except EOFError:
        return 'n'


def marcador(p):
    return f"ASAAS#{p['id']}"


def texto(p):
    partes = [marcador(p), p.get('description') or '', f"venc. {comum.data_br(p.get('dueDate'))}",
              p.get('billingType') or '']
    if p.get('installmentNumber'):
        partes.append(f"parcela {p['installmentNumber']}")
    return ' | '.join(x for x in partes if x)


def valores(p, nome_cliente, pago, contratante_id=None):
    return {
        'titulo': nome_cliente, 'valor': p.get('value'), 'tipo': 'Entrada', 'pago': pago,
        'data_pagamento': (p.get('paymentDate') or p.get('clientPaymentDate')) if pago else None,
        'texto': texto(p), 'contratante': contratante_id,
        'classificacao': os.getenv('NOTION_FIN_CLASSIFICACAO') or None,
        'area': os.getenv('NOTION_FIN_AREA') or None,
        'recorrencia': 'Parcelado' if p.get('installment') else None,
    }


def parece_duplicata(nome, valor, quando, existentes):
    """Linha ja lancada (provavelmente a mao) com o mesmo cliente, valor e data proxima. Funcao pura."""
    alvo = comum.para_data(quando)
    for e in existentes:
        if not comum.nomes_parecidos(nome, e.get('titulo', '')):
            continue
        if abs(comum.num(e.get('valor')) - comum.num(valor)) > 0.01:
            continue
        d = comum.para_data(e.get('data_pagamento'))
        if alvo is None or d is None or abs((d - alvo).days) <= TOLERANCIA_DIAS:
            return e
    return None


def planejar(emitidas, recebidas, registro, nomes, existentes):
    """Lista de acoes {'acao': criar|marcar_pago|pular, ...} sem rede. Funcao pura (testavel)."""
    acoes, vistos = [], set()
    for p in recebidas:
        vistos.add(p['id'])
        nome = nomes.get(p['customer'], '')
        meu = registro.get(p['id'])
        if meu and meu.get('pago'):
            acoes.append({'acao': 'pular', 'motivo': 'já lançado como pago', 'p': p, 'nome': nome})
        elif meu:
            acoes.append({'acao': 'marcar_pago', 'p': p, 'nome': nome, 'notion_id': meu['notion_id']})
        else:
            dup = parece_duplicata(nome, p.get('value'), p.get('paymentDate'), existentes)
            if dup:
                acoes.append({'acao': 'pular', 'motivo': f"parece já lançado à mão ({dup.get('titulo')}, "
                              f"{dup.get('data_pagamento') or 'sem data'})", 'p': p, 'nome': nome})
            else:
                acoes.append({'acao': 'criar', 'pago': True, 'p': p, 'nome': nome})
    for p in emitidas:
        if p['id'] in vistos:
            continue
        nome = nomes.get(p['customer'], '')
        if p['id'] in registro:
            acoes.append({'acao': 'pular', 'motivo': 'já lançado', 'p': p, 'nome': nome})
            continue
        dup = parece_duplicata(nome, p.get('value'), p.get('dueDate'), existentes)
        if dup:
            acoes.append({'acao': 'pular', 'motivo': f"parece já lançado à mão ({dup.get('titulo')})", 'p': p,
                          'nome': nome})
        else:
            acoes.append({'acao': 'criar', 'pago': False, 'p': p, 'nome': nome})
    return acoes


def _coletar(dias):
    fim = date.today()
    ini = fim - timedelta(days=max(1, int(dias)) - 1)
    recebidas = comum.cobrancas_recebidas(ini.isoformat(), fim.isoformat())
    emitidas = [p for p in comum._paginar('/payments', {'dateCreated[ge]': ini.isoformat(),
                                                         'dateCreated[le]': fim.isoformat()})
                if not p.get('deleted') and p.get('status') not in comum.STATUS_RECEBIDO]
    return ini, fim, emitidas, recebidas


def executar(dias=7, gravar=False, exemplo=False):
    print('\n=== ASAAS -> NOTION (Transações Financeiras) ===')
    if exemplo:
        print('   Modo exemplo não implementado para esta rotina: use sem --exemplo (ela só lê, sem --gravar).')
        return []
    if not comum.asaas_configurado():
        print('   Sem ASAAS_API_TOKEN: nada a fazer (modo seguro).')
        return []
    ini, fim, emitidas, recebidas = _coletar(dias)
    print(f'   Período {comum.data_br(ini)} a {comum.data_br(fim)}: {len(emitidas)} emitida(s) em aberto, '
          f'{len(recebidas)} recebida(s)')
    clientes = comum.ClientesAsaas()
    nomes = {p['customer']: (clientes.get(p['customer']).get('name') or p['customer'])
             for p in emitidas + recebidas}

    import notion_escritorio as ne
    existentes = ne.listar('financeiro', n=500) if os.getenv('NOTION_TOKEN') else []
    registro = _ler()
    acoes = planejar(emitidas, recebidas, registro, nomes, existentes)

    for n, a in enumerate(acoes, 1):
        p = a['p']
        rot = {'criar': 'CRIAR ' + ('(pago)' if a.get('pago') else '(em aberto)'), 'marcar_pago': 'MARCAR PAGO',
               'pular': 'pular'}[a['acao']]
        extra = f" - {a['motivo']}" if a['acao'] == 'pular' else ''
        print(f"  {n:2}. {rot:<17} {a['nome'][:38]:<38} R$ {comum.moeda(p.get('value'))} | "
              f"venc {comum.data_br(p.get('dueDate'))} | pago {comum.data_br(p.get('paymentDate')) or '-'}{extra}")
    fazer = [a for a in acoes if a['acao'] != 'pular']
    print(f'   {len(fazer)} a gravar, {len(acoes) - len(fazer)} pulado(s).')
    if not gravar:
        print('   SIMULAÇÃO: nada foi gravado. Para gravar: --gravar (confirmação item a item).')
        return []
    if not os.getenv('NOTION_TOKEN'):
        print('   Sem NOTION_TOKEN: nada gravado.')
        return []

    esq = ne.esquema('financeiro')
    feitos = []
    for a in fazer:
        p = a['p']
        try:
            ja = ne.ni.consultar_banco(ne.base_id('financeiro'), limit=1, filtro={
                'property': ne.CAMPOS['financeiro']['texto'], 'rich_text': {'contains': marcador(p)}})
        except Exception as e:  # noqa: BLE001
            print(f"  {a['nome']}: não consegui conferir duplicidade ({str(e)[:80]}); pulado.")
            continue
        if a['acao'] == 'criar' and ja:
            print(f"  {a['nome']}: o Notion já tem {marcador(p)} (pulado)")
            continue
        print(f"\n  {a['nome']} | R$ {comum.moeda(p.get('value'))} | {p.get('description') or ''}")
        pergunta = '  Marcar como pago no Notion? (s/N): ' if a['acao'] == 'marcar_pago' else '  Lançar no Notion? (s/N): '
        if _perguntar(pergunta) != 's':
            print('  Pulado.')
            continue
        if a['acao'] == 'marcar_pago':
            r = ne.atualizar_propria('financeiro', a['notion_id'], {
                'pago': True, 'data_pagamento': p.get('paymentDate')}, marcador(p), esq=esq)
        else:
            cid = ne.achar_cliente(a['nome']) if a['nome'] else None
            r = ne.criar('financeiro', valores(p, a['nome'], a['pago'], cid), gravar=True, esq=esq)
        for av in r.get('avisos', []):
            print(f'  aviso: {av}')
        if not r.get('gravado'):
            print('  Não gravado.')
            continue
        registro[p['id']] = {'notion_id': r.get('id') or a.get('notion_id'), 'pago': bool(a.get('pago')) or
                             a['acao'] == 'marcar_pago', 'em': datetime.now().isoformat(timespec='seconds')}
        _salvar(registro)
        feitos.append(p['id'])
        print('  Gravado.')
    print(f'\n   {len(feitos)} lançamento(s) gravado(s) no Notion.')
    return feitos
