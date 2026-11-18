"""
Notion do escritorio: leitura e escrita nas bases que a Dra. Faya JA TEM (nao cria base nem coluna).

Bases (IDs de docs/NOTION_MAPA.md; podem ser trocados por NOTION_DB_<BASE> no config/.env):
  prazos      Prazos/Tarefas              (prazos e tarefas)
  financeiro  Transacoes Financeiras      (honorarios, cobrancas, pagamentos)
  clientes    Base de Dados Clientes      (cliente + n do processo = "processos")
  calculos    Fluxo RT                    (demandas de calculo, inclusive de parceiros)
  pericias    Audiencias/Pericias

Regras:
- O tipo de cada coluna vem do esquema real (API); os NOMES das colunas estao em CAMPOS, com os erros de grafia e
  espacos que existem no Notion de verdade.
- Valor de select/status/multi-select que NAO existe na coluna e IGNORADO (e avisado): o Notion criaria uma opcao
  nova e isso mexeria na estrutura da base dela. Pessoa (people) so entra se o id do usuario for informado.
- So CRIA pagina. Nunca apaga. Unica alteracao possivel: `atualizar_propria`, numa linha que o proprio sistema
  criou (confere o marcador no Texto). Linha da equipe nunca e alterada.
- Escrita so com gravar=True (ou --gravar na linha de comando). Sem isso, mostra o que gravaria.

CLI:
    python INTEGRACOES/notion_escritorio.py esquema [base]
    python INTEGRACOES/notion_escritorio.py abertas prazos [-n 5]
    python INTEGRACOES/notion_escritorio.py listar clientes [-n 5]
    python INTEGRACOES/notion_escritorio.py teste-tarefa [--gravar]       cria "[TESTE] apagar" em Prazos/Tarefas
    python INTEGRACOES/notion_escritorio.py teste-financeiro [--gravar]   cria "[TESTE] apagar" em Transacoes
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import notion_integration as ni  # noqa: E402

BASES = {
    'prazos': '40e7b6d5-dac6-839a-b006-01b423a08d5a',
    'financeiro': 'd647b6d5-dac6-83df-aaa5-01049cba9dda',
    'clientes': '51d7b6d5-dac6-829d-9b39-010518728754',
    'calculos': '5d37b6d5-dac6-83c6-ad8f-014a5ae8fbf2',
    'pericias': '36c7b6d5-dac6-8173-956d-c2f69f150da5',
}

# campo logico -> nome EXATO da coluna no Notion
CAMPOS = {
    'prazos': {
        'titulo': 'Contratante', 'cliente': 'Cliente', 'texto': 'Texto', 'data': 'Data',
        'responsavel': 'Responsável', 'prioridade': 'Prioridade', 'tribunal': 'Tribunal',
        'status': 'Status', 'etapa': 'Fluxo RT',
    },
    'financeiro': {
        'titulo': 'Cliente', 'contratante': 'Contratante', 'tipo': 'Tipo', 'valor': 'Valor',
        'pago': 'Pago', 'data_pagamento': 'Data do pagamento', 'recorrencia': 'Recorrência',
        'classificacao': 'Classificação', 'area': 'Área', 'servico': 'Serviço', 'texto': 'Texto',
        'parcela_atual': 'Parcela Atual', 'num_parcelas': 'Núm', 'valor_total': 'Valor Total',
    },
    'clientes': {
        'titulo': 'Cliente ', 'processo': 'N Processo', 'status': 'Status ', 'area': 'Área',
        'tribunal': 'Tribunal', 'telefone': 'Telefone', 'responsavel': 'Responsável',
    },
    'calculos': {
        'titulo': 'Cliente x Empresa', 'etapa': 'Fluxo RT', 'prioridade': 'Prioridade',
        'responsavel': 'Resposável', 'status': 'Status', 'data_entrega': 'Data Entrega',
    },
    'pericias': {
        'titulo': 'Cliente x Parte Contrária', 'processo': 'Processo', 'evento': 'Evento',
        'local': 'Tribunal - Cidade', 'responsavel': 'Resposável', 'modalidade': 'Modalidade',
        'area': 'Área', 'data': 'Data e Hora', 'status': 'Status',
    },
}

# Colunas de resultado: o que mostrar ao listar
MOSTRAR = {
    'prazos': ['titulo', 'texto', 'data', 'status', 'etapa'],
    'clientes': ['titulo', 'processo', 'status', 'area', 'tribunal'],
}

STATUS_ABERTOS_PRAZOS = ['PRAZO', 'Não iniciada', 'Em andamento', 'Revisar', 'Assinar']


def base_id(base):
    if base not in BASES:
        raise SystemExit(f'Base desconhecida: {base}. Opcoes: {", ".join(BASES)}')
    return os.getenv(f'NOTION_DB_{base.upper()}') or BASES[base]


def esquema(base):
    """{nome_da_coluna: {'type': ..., 'opcoes': [...]}} lido da API."""
    banco = ni._request('GET', f'/databases/{base_id(base)}')
    saida = {}
    for nome, p in banco.get('properties', {}).items():
        t = p['type']
        item = {'type': t}
        if t in ('select', 'status', 'multi_select'):
            item['opcoes'] = [o['name'] for o in p[t].get('options', [])]
        saida[nome] = item
    return saida


def _texto(valor):
    return [{'type': 'text', 'text': {'content': str(valor)[i:i + 1900]}} for i in range(0, max(len(str(valor)), 1), 1900)]


def montar_propriedades(base, valores, esq):
    """valores {campo_logico: valor} -> (propriedades da API, avisos). Funcao pura (sem rede)."""
    props, avisos = {}, []
    for campo, valor in valores.items():
        if valor in (None, ''):
            continue
        coluna = CAMPOS[base].get(campo)
        if not coluna:
            avisos.append(f'campo "{campo}" nao mapeado em {base}')
            continue
        info = esq.get(coluna)
        if not info:
            avisos.append(f'coluna "{coluna}" nao existe no Notion ({campo} ignorado)')
            continue
        t = info['type']
        if t == 'title':
            props[coluna] = {'title': _texto(valor)}
        elif t == 'rich_text':
            props[coluna] = {'rich_text': _texto(valor)}
        elif t == 'number':
            props[coluna] = {'number': float(valor)}
        elif t == 'checkbox':
            props[coluna] = {'checkbox': bool(valor)}
        elif t == 'date':
            props[coluna] = {'date': {'start': str(valor)}}
        elif t == 'phone_number':
            props[coluna] = {'phone_number': str(valor)}
        elif t in ('select', 'status'):
            if valor in info.get('opcoes', []):
                props[coluna] = {t: {'name': valor}}
            else:
                avisos.append(f'"{valor}" nao e opcao de "{coluna}" (nao crio opcao nova; ignorado)')
        elif t == 'multi_select':
            itens = valor if isinstance(valor, (list, tuple)) else [valor]
            ok = [v for v in itens if v in info.get('opcoes', [])]
            for v in itens:
                if v not in ok:
                    avisos.append(f'"{v}" nao e opcao de "{coluna}" (ignorado)')
            if ok:
                props[coluna] = {'multi_select': [{'name': v} for v in ok]}
        elif t == 'people':
            ids = valor if isinstance(valor, (list, tuple)) else [valor]
            props[coluna] = {'people': [{'id': i} for i in ids]}
        elif t == 'relation':
            ids = valor if isinstance(valor, (list, tuple)) else [valor]
            props[coluna] = {'relation': [{'id': i} for i in ids]}
        else:
            avisos.append(f'coluna "{coluna}" e do tipo {t} (somente leitura: ignorada)')
    return props, avisos


def criar(base, valores, gravar=False, esq=None):
    """Cria UMA pagina. Sem gravar=True nao escreve: devolve o que gravaria."""
    esq = esq or esquema(base)
    props, avisos = montar_propriedades(base, valores, esq)
    resultado = {'base': base, 'propriedades': props, 'avisos': avisos, 'gravado': False, 'id': None}
    if gravar and props:
        pagina = ni.criar_pagina(base_id(base), props)
        resultado.update(gravado=True, id=pagina.get('id'), url=pagina.get('url'))
    return resultado


def atualizar_propria(base, page_id, valores, marcador, esq=None):
    """UNICA excecao ao "so cria": altera uma linha que ESTE SISTEMA criou. Confere o `marcador` (ex.: ASAAS#id)
    no Texto da propria linha antes de mexer; sem ele, recusa. Linha da equipe nunca e alterada."""
    esq = esq or esquema(base)
    pagina = ni._request('GET', f'/pages/{page_id}')
    coluna_texto = CAMPOS[base].get('texto')
    atual = _valor(pagina['properties'][coluna_texto]) if coluna_texto in pagina.get('properties', {}) else ''
    if marcador not in atual:
        return {'gravado': False, 'avisos': [f'linha {page_id} não tem o marcador {marcador}: não é do sistema, recusada']}
    props, avisos = montar_propriedades(base, valores, esq)
    if props:
        ni.atualizar_pagina(page_id, props)
    return {'gravado': bool(props), 'id': page_id, 'avisos': avisos}


# ---------- atalhos de negocio ----------

def criar_tarefa(contratante, cliente=None, texto=None, data=None, status='Não iniciada', etapa=None,
                 prioridade=None, tribunal=None, responsavel_id=None, gravar=False):
    """Tarefa/prazo em Prazos/Tarefas. `contratante` e o TITULO da linha: quem contratou (advogado parceiro ou
    "Particular"); o cliente final vai em `cliente`. `data` = prazo INTERNO; ponha o fatal em `texto` (so ha uma data)."""
    return criar('prazos', {'titulo': contratante, 'cliente': cliente, 'texto': texto, 'data': data, 'status': status,
                            'etapa': etapa, 'prioridade': prioridade, 'tribunal': tribunal,
                            'responsavel': responsavel_id}, gravar)


def lancar_financeiro(cliente, valor, tipo='Entrada', pago=False, data_pagamento=None, classificacao=None,
                      recorrencia=None, area='Previdenciário', servico=None, texto=None, contratante_id=None,
                      gravar=False):
    """Lancamento em Transacoes Financeiras (cobranca emitida: pago=False; recebimento: pago=True + data)."""
    return criar('financeiro', {'titulo': cliente, 'valor': valor, 'tipo': tipo, 'pago': pago,
                                'data_pagamento': data_pagamento, 'classificacao': classificacao,
                                'recorrencia': recorrencia, 'area': area, 'servico': servico, 'texto': texto,
                                'contratante': contratante_id}, gravar)


def criar_demanda_calculo(cliente_ou_parceiro, data_entrega, etapa=None, prioridade=None, gravar=False):
    """Demanda de calculo (inclusive de advogado parceiro) em Fluxo RT. Status inicial: Nao iniciada."""
    return criar('calculos', {'titulo': cliente_ou_parceiro, 'data_entrega': data_entrega, 'etapa': etapa,
                              'prioridade': prioridade, 'status': 'Não iniciada'}, gravar)


# ---------- leitura ----------

def _valor(p):
    t = p['type']
    v = p.get(t)
    if t in ('title', 'rich_text'):
        return ''.join(x.get('plain_text', '') for x in v)
    if t in ('select', 'status'):
        return (v or {}).get('name', '')
    if t == 'multi_select':
        return ', '.join(x['name'] for x in v)
    if t == 'date':
        return (v or {}).get('start', '') or ''
    if t == 'people':
        return ', '.join(x.get('name', '') for x in v)
    if t in ('number', 'checkbox', 'phone_number'):
        return '' if v is None else str(v)
    return ''


def listar(base, n=5, filtro=None):
    """Primeiras n paginas, so leitura: lista de {campo_logico: texto}."""
    paginas = ni.consultar_banco(base_id(base), filtro=filtro, limit=n)
    inverso = {c: k for k, c in CAMPOS[base].items()}
    saida = []
    for pg in paginas:
        linha = {'_id': pg['id']}
        for coluna, p in pg['properties'].items():
            campo = inverso.get(coluna)
            if campo:
                linha[campo] = _valor(p)
        saida.append(linha)
    return saida


def tarefas_abertas(n=5):
    col = CAMPOS['prazos']['status']
    filtro = {'or': [{'property': col, 'status': {'equals': s}} for s in STATUS_ABERTOS_PRAZOS]}
    return listar('prazos', n, filtro)


def achar_cliente(nome):
    """Id da pagina do cliente (para a relacao do financeiro). Leitura. None se nao achar ou se houver mais de um."""
    col = CAMPOS['clientes']['titulo']
    achados = ni.consultar_banco(base_id('clientes'), filtro={'property': col, 'title': {'contains': nome}}, limit=3)
    return achados[0]['id'] if len(achados) == 1 else None


# ---------- linha de comando ----------

def _mostrar(base, linhas):
    cols = MOSTRAR.get(base) or list(CAMPOS[base])
    for l in linhas:
        print(' | '.join(f'{c}={l.get(c, "")}'[:70] for c in cols))


def _mostrar_resultado(r):
    print(f'Base: {r["base"]}')
    for k, v in r['propriedades'].items():
        print(f'  {k}: {v}')
    for a in r['avisos']:
        print(f'  AVISO: {a}')
    if r['gravado']:
        print(f'GRAVADO: {r.get("url") or r["id"]}  (confira no Notion e apague)')
    else:
        print('NADA GRAVADO (simulacao). Use --gravar para criar.')


def main():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from NUCLEO import ambiente  # noqa: F401
    ap = argparse.ArgumentParser(description='Notion do escritorio', epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('esquema')
    e.add_argument('base', nargs='?')
    a = sub.add_parser('abertas')
    a.add_argument('base', choices=['prazos'])
    a.add_argument('-n', type=int, default=5)
    l = sub.add_parser('listar')
    l.add_argument('base', choices=list(BASES))
    l.add_argument('-n', type=int, default=5)
    for nome in ('teste-tarefa', 'teste-financeiro'):
        t = sub.add_parser(nome)
        t.add_argument('--gravar', action='store_true')
    args = ap.parse_args()

    if args.cmd == 'esquema':
        for b in ([args.base] if args.base else list(BASES)):
            print(f'== {b}')
            for nome, i in esquema(b).items():
                print(f'   {nome!r}: {i["type"]}' + (f' {i["opcoes"]}' if 'opcoes' in i else ''))
    elif args.cmd == 'abertas':
        _mostrar('prazos', tarefas_abertas(args.n))
    elif args.cmd == 'listar':
        _mostrar(args.base, listar(args.base, args.n))
    elif args.cmd == 'teste-tarefa':
        _mostrar_resultado(criar_tarefa('[TESTE] apagar', cliente='[TESTE] apagar',
                                        texto='Teste do conector. Pode apagar.', status='Não iniciada',
                                        gravar=args.gravar))
    elif args.cmd == 'teste-financeiro':
        _mostrar_resultado(lancar_financeiro('[TESTE] apagar', 1, texto='Teste do conector. Pode apagar.',
                                             gravar=args.gravar))


if __name__ == '__main__':
    main()
