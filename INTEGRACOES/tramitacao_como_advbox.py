"""
Adaptador: entrega os dados do Tramitacao Inteligente no FORMATO do ADVBOX.

A Controladoria foi escrita em cima das funcoes do advbox_integration. Como o escritorio usa a
Tramitacao Inteligente, este modulo expoe as mesmas funcoes (mesmos nomes e mesmo formato de
retorno) lendo da API da Tramitacao. `CONTROLADORIA/comum.backend()` escolhe qual usar.

Diferencas que importam:
- A Tramitacao nao tem "responsavel" nem "fase" no processo: `stage` vem do status (ativo/arquivado...)
  e o responsavel cai no cargo da acao (config/equipe.py).
- Nao ha endpoint de movimentacoes por periodo: lemos as movimentacoes de cada processo ativo
  (uma chamada por processo, resultado guardado em memoria na execucao).
- Tipo de tarefa = tipo de atividade da Tramitacao (Task, Deadline...). Prazo vira `Deadline`.
- A API nao conclui atividades por aqui; criar atividade so ocorre quando a Controladoria pede
  (varredura --criar-tarefas, item a item, com confirmacao humana).
"""
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tramitacao_integration as ti  # noqa: E402

_CACHE = {}

# Tipos de atividade da Tramitacao -> nome legivel (o "tipo de tarefa" do ADVBOX)
TIPOS = {
    'Task': 'TAREFA', 'Deadline': 'PRAZO', 'Hearing': 'AUDIENCIA', 'Meeting': 'REUNIAO',
    'Event': 'EVENTO', 'Dispatch': 'DESPACHO', 'MedicalExam': 'PERICIA',
}
_STATUS_FASE = {'ativo': '', 'arquivado': 'ARQUIVADO', 'encerrado': 'ENCERRADO', 'suspenso': 'SUSPENSO'}


def _digitos(s):
    return ''.join(c for c in str(s or '') if c.isdigit())


def _telefones():
    if 'tel' not in _CACHE:
        _CACHE['tel'] = {str(c['id']): c.get('phone_mobile') or c.get('phone_1') or c.get('phone_2') or ''
                         for c in ti.listar_clientes(limit=20000)}
    return _CACHE['tel']


def _processo(l):
    tel = _telefones()
    clientes = [{'id': c['id'], 'customer_id': c['id'], 'name': c.get('name') or '',
                 'cellphone': tel.get(str(c['id']), '')}
                for c in l.get('customers') or [] if c.get('role') in (None, 'ativo')] or \
               [{'id': c['id'], 'customer_id': c['id'], 'name': c.get('name') or '',
                 'cellphone': tel.get(str(c['id']), '')} for c in l.get('customers') or []]
    return {
        'id': l['id'], 'process_number': l.get('number') or '', 'protocol_number': '',
        'stage': _STATUS_FASE.get(l.get('status'), (l.get('status') or '').upper()),
        'status_closure': '' if l.get('status') == 'ativo' else (l.get('updated_at') or '')[:10],
        'customers': clientes, 'responsible': '', 'responsible_id': '',
        'parte_contraria': '', 'title': l.get('title') or '', 'court': l.get('court') or '',
    }


def listar_processos_todos(**filtros):
    if 'processos' not in _CACHE:
        _CACHE['processos'] = [_processo(l) for l in ti.listar_processos(limit=20000)]
    return _CACHE['processos']


def paginar_ritmado(endpoint, params=None, **_):
    """So o que a Controladoria pede: /customers (telefones)."""
    if endpoint == '/customers':
        return [{'id': c['id'], 'name': c.get('name'), 'cellphone': c.get('phone_mobile') or c.get('phone_1') or ''}
                for c in ti.listar_clientes(limit=20000)]
    raise NotImplementedError(f'endpoint {endpoint} nao existe no adaptador da Tramitacao')


def indice_processos_por_numero(processos):
    indice = {}
    for p in processos or []:
        num = _digitos(p.get('process_number'))
        if len(num) >= 15:
            indice.setdefault(num, p)
    return indice


def obter_cliente(cliente_id):
    c = ti.buscar_cliente(cliente_id) or {}
    return {**c, 'cellphone': c.get('phone_mobile') or c.get('phone_1') or ''}


def buscar_processo(cliente_id=None, numero_processo=None, nome=None):
    if numero_processo:
        achados = ti.listar_processos(limit=5, number=numero_processo)
    elif cliente_id:
        achados = ti.listar_processos(limit=100, customer_id=cliente_id)
    else:
        return []
    return [_processo(l) for l in achados]


def atualizar_processo(lawsuit_id, campos):
    if campos.get('status_closure'):
        return ti._request('PATCH', f'/v1/processos/{lawsuit_id}', json_data={'lawsuit': {'status': 'encerrado'}})
    return None


# ---------- usuarios e tipos ----------

def usuarios_advbox():
    return [{'id': u['id'], 'name': u.get('name')} for u in ti.listar_usuarios()]


def id_usuario_por_nome(nome):
    alvo = (nome or '').strip().upper()
    if not alvo:
        return None
    for u in usuarios_advbox():
        n = str(u.get('name', '')).upper()
        if alvo in n or n in alvo:
            return u['id']
    return None


def usuario_padrao():
    """Unico (ou primeiro) usuario do escritorio na Tramitacao: recebe as tarefas quando o cargo nao tem ID."""
    us = usuarios_advbox()
    return us[0]['id'] if us else ''


def buscar_tipo_tarefa(nome_parcial):
    """Nome do tipo de tarefa do escritorio -> tipo de atividade da Tramitacao."""
    n = (nome_parcial or '').upper()
    if any(k in n for k in ('PRAZO', 'RECURSO', 'MANIFEST', 'CONTEST', 'EMBARGO', 'CUMPR', 'ELABORAR')):
        return 'Deadline'
    if 'AUDIEN' in n:
        return 'Hearing'
    return 'Task'


# ---------- atividades (= tarefas) ----------

def _tarefa(a):
    l = a.get('lawsuit') or {}
    us = a.get('users') or []
    concluida = (a.get('completed_on') or '')[:19] if a.get('completed') else ''
    return {
        'id': a['id'], 'task': TIPOS.get(a.get('type'), a.get('type') or ''),
        'created_at': a.get('created_at') or '', 'date': a.get('start') or a.get('created_at') or '',
        'date_deadline': a.get('deadline_on') or '', 'lawsuits_id': l.get('id'),
        'lawsuit': {'id': l.get('id'), 'process_number': l.get('number') or '',
                    'customers': ([{'name': (a.get('customer') or {}).get('name') or ''}]
                                  if a.get('customer') else [])},
        'users': [{'id': u.get('id'), 'name': u.get('name'), 'completed': concluida} for u in us],
        'comments': '\n'.join(x for x in (a.get('title'), a.get('description')) if x),
    }


def listar_tarefas_ritmado(**filtros):
    params = {}
    if filtros.get('lawsuit_id'):
        params['lawsuit_id'] = filtros['lawsuit_id']
    if filtros.get('date_start'):
        params['from'] = filtros['date_start']
    if filtros.get('date_end'):
        params['to'] = filtros['date_end']
    return [_tarefa(a) for a in ti.listar_atividades(limit=20000, **params)]


def criar_publicacao(lawsuit_id, task_id, guest_ids, comments='', from_id=None, date_deadline=None, urgent=False):
    """Cria a atividade no processo. task_id e o tipo (Task/Deadline...). Retorna a atividade criada."""
    titulo = (comments or 'Tarefa da Controladoria').strip().split('\n')[0][:120]
    campos = {'description': comments, 'lawsuit_id': int(lawsuit_id)}
    if task_id == 'Deadline':
        campos['deadline_on'] = date_deadline or date.today().isoformat()
    else:
        campos['start'] = (date_deadline or date.today().isoformat()) + 'T09:00:00-03:00'
        campos['end'] = (date_deadline or date.today().isoformat()) + 'T10:00:00-03:00'
    guests = [g for g in (guest_ids or []) if g and g != from_id]
    if guests:
        campos['assignments'] = [{'user_id': g, 'role': 'executor'} for g in guests]
    return ti.criar_atividade(('[URGENTE] ' if urgent else '') + titulo, task_id, from_id, **campos)


# ---------- movimentacoes ----------

def listar_movimentacoes_periodo(date_start, date_end):
    """Movimentacoes dos processos ativos no periodo (uma chamada por processo; demora)."""
    chave = ('mov', date_start, date_end)
    if chave in _CACHE:
        return _CACHE[chave]
    ini, fim = str(date_start)[:10], str(date_end)[:10]
    saida, falhas = [], []
    ativos = [p for p in listar_processos_todos() if not p['stage'] and _digitos(p['process_number'])]
    print(f'   Tramitação: lendo movimentações de {len(ativos)} processo(s) ativo(s) (uma chamada cada)...')
    for n, p in enumerate(ativos, 1):
        try:
            movs = ti.listar_movimentacoes(p['id'], limit=100)
        except Exception as e:
            falhas.append(p['process_number'])
            print(f"   (processo {p['process_number']}: movimentações não lidas: {str(e)[:60]})")
            continue
        for m in movs:
            d = (m.get('data_hora') or '')[:10]
            if ini <= d <= fim:
                saida.append({'lawsuit_id': p['id'], 'process_number': p['process_number'], 'date': d,
                              'description': m.get('descricao') or ''})
        if n % 100 == 0:
            print(f'   ... {n}/{len(ativos)}')
    if falhas:
        # sem isso, processo nao lido seria contado como "parado"
        raise RuntimeError(f'{len(falhas)} processo(s) sem leitura de movimentações; relatório não confiável. '
                           'Rode de novo.')
    _CACHE[chave] = saida
    return saida
