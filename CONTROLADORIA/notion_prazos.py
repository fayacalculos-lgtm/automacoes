"""
Prazos da varredura do DJEN -> banco Prazos/Tarefas do Notion da Dra. Faya.

Mesmas travas da tarefa no ADVBOX/Tramitacao:
- sem `gravar`, so mostra o que iria (simulacao);
- com `gravar`, pergunta item a item (s/N). Sem terminal (rodando agendado) a resposta e "nao": nada e gravado;
- nao duplica: registro local por publicacao (DJEN#id) + busca no proprio Notion pelo "DJEN#id" no Texto;
- so CRIA linha (INTEGRACOES/notion_escritorio.py); nunca altera nem apaga.

Como a linha fica (o banco so tem UMA data):
  Contratante (titulo) = NOTION_CONTRATANTE_PADRAO do .env (padrao "Particular": caso do proprio escritorio)
  Cliente = cliente do processo | Data = prazo INTERNO (ou o dia da audiencia/pericia)
  Texto = DJEN#id, prazo FATAL e interno, providencia, peca, link | Status = PRAZO | Fluxo RT = PRAZO
  Prioridade = gravidade (ALTA/MEDIA/BAIXA) | Tribunal = so se for opcao que ja existe na coluna
"""
import json
import os
import sys
from datetime import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'INTEGRACOES'))
import comum  # noqa: E402

PRIORIDADE = {'ALTA': 'Alta', 'MEDIA': 'Média', 'MÉDIA': 'Média', 'BAIXA': 'Baixa'}


def _registro():
    return os.path.join(comum.pasta_saida('controladoria'), '_notion_prazos_criados.json')


def _ler():
    try:
        with open(_registro(), encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _perguntar(texto):
    try:
        return input(texto).strip().lower()
    except EOFError:  # agendado, sem terminal: nunca grava
        return 'n'


def candidatos(itens):
    """Prazo do escritorio com data (interna ou de evento). Nao exige o processo cadastrado em lugar nenhum."""
    return [i for i in itens
            if i['prazo_nosso'] == 'SIM' and i['categoria'] != 'DESPACHO' and (i['interno_iso'] or i['evento_data'])]


def _data(i):
    if i['interno_iso']:
        return i['interno_iso']
    d = comum.data(i['evento_data'])
    return d.isoformat() if d else None


def valores(i, texto):
    return {
        'titulo': os.getenv('NOTION_CONTRATANTE_PADRAO') or 'Particular',
        'cliente': i['cliente'], 'texto': texto, 'data': _data(i), 'status': 'PRAZO', 'etapa': 'PRAZO',
        'prioridade': PRIORIDADE.get((i['gravidade'] or '').upper()), 'tribunal': i['tribunal'],
    }


def _ja_no_notion(ne, chave):
    filtro = {'property': ne.CAMPOS['prazos']['texto'], 'rich_text': {'contains': f'DJEN#{chave}'}}
    return bool(ne.ni.consultar_banco(ne.base_id('prazos'), filtro=filtro, limit=1))


def enviar(itens, texto_da_tarefa, gravar=False, exemplo=False):
    cands = candidatos(itens)
    print(f'\n=== PRAZOS NO NOTION (Prazos/Tarefas): {len(cands)} candidato(s) ===')
    for n, i in enumerate(cands, 1):
        print(f"  {n:2}. [{i['gravidade']}] data {_data(i) or '-'} | fatal {i['fatal'] or '-'} | "
              f"{i['processo']} | {i['cliente']} | {i['rotulo']}")
    if not cands:
        return []
    if exemplo or not gravar:
        print('  SIMULAÇÃO: nada foi gravado no Notion. Para gravar: --notion --gravar-notion '
              '(confirmação item a item).')
        return []
    if not os.getenv('NOTION_TOKEN'):
        print('  Sem NOTION_TOKEN: nada gravado (modo seguro).')
        return []

    import notion_escritorio as ne
    esq = ne.esquema('prazos')
    registro = _ler()
    criadas = []
    for i in cands:
        chave = str(i['id_djen'])
        if chave in registro:
            print(f"  {i['processo']}: já gravado em {registro[chave]['em']} (pulado)")
            continue
        try:
            if _ja_no_notion(ne, chave):
                print(f"  {i['processo']}: o Notion já tem a linha desta publicação (pulado)")
                continue
        except Exception as e:  # noqa: BLE001
            print(f"  {i['processo']}: não consegui conferir duplicidade no Notion ({str(e)[:80]}); pulado.")
            continue
        print(f"\n  {i['processo']} | {i['cliente']}\n  {i['rotulo']} | data {_data(i)} | fatal {i['fatal']}")
        if _perguntar('  Gravar este prazo no Notion? (s/N): ') != 's':
            print('  Pulado.')
            continue
        r = ne.criar('prazos', valores(i, texto_da_tarefa(i)), gravar=True, esq=esq)
        for a in r['avisos']:
            print(f'  aviso: {a}')
        if not r['gravado']:
            print('  Não gravado.')
            continue
        registro[chave] = {'em': datetime.now().isoformat(timespec='seconds'), 'processo': i['processo'],
                           'notion_id': r['id']}
        with open(_registro(), 'w', encoding='utf-8') as f:
            json.dump(registro, f, ensure_ascii=False, indent=1)
        criadas.append(chave)
        print(f"  Gravado: {r.get('url') or r['id']}")
    print(f'\n  {len(criadas)} prazo(s) gravado(s) no Notion.')
    return criadas
