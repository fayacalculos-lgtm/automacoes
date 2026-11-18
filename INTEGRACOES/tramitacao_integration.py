"""
Integracao com a API do Tramitacao Inteligente - Faya Barreiros Sociedade Individual de Advocacia
Clientes, processos, movimentacoes, publicacoes (intimacoes), atividades (prazos/tarefas) e assinaturas.

API Base: https://planilha.tramitacaointeligente.com.br/api
Auth: Authorization: Bearer TRAMITACAO_API_TOKEN (chave gerada em /api/chaves por usuario logado)
Docs: https://planilha.tramitacaointeligente.com.br/api/docs.json (catalogo navegavel)

Regra do escritorio: leitura e livre; escrita (criar/alterar/enviar para assinatura) so por chamada
explicita, nunca em lote automatico. Envio de envelope para assinatura exige confirmar=True.
"""
import os
import sys
import time
import requests


TRAMITACAO_BASE_URL = 'https://planilha.tramitacaointeligente.com.br/api'


def _get_token():
    token = os.getenv('TRAMITACAO_API_TOKEN')
    if not token:
        print('ERRO: TRAMITACAO_API_TOKEN nao encontrado no .env')
        sys.exit(1)
    return token


def _headers():
    return {
        'Authorization': f'Bearer {_get_token()}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'faya-barreiros-automacoes/1.0',
    }


def _request(method, endpoint, params=None, json_data=None, retries=2, esperas_429=15):
    url = f'{TRAMITACAO_BASE_URL}{endpoint}'
    tentativa = 0
    while tentativa <= retries:
        try:
            resp = requests.request(method, url, headers=_headers(),
                                    params=params, json=json_data, timeout=30)
            if resp.status_code == 429:
                # limite de requisicoes: espera e tenta de novo SEM gastar as tentativas de erro
                esperas_429 -= 1
                if esperas_429 < 0:
                    raise RuntimeError('Tramitacao: limite de requisicoes (429) persistente em ' + endpoint)
                wait = int(resp.headers.get('Retry-After', 30))
                print(f'  Rate limit Tramitacao. Aguardando {wait}s...')
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json() if resp.text else {}
        except requests.exceptions.HTTPError:
            print(f'  Tramitacao erro ({resp.status_code}): {resp.text[:200]}')
            if tentativa < retries and resp.status_code >= 500:
                tentativa += 1
                time.sleep(3)
                continue
            raise
        except requests.exceptions.RequestException as e:
            print(f'  Tramitacao conexao falhou: {e}')
            if tentativa < retries:
                tentativa += 1
                time.sleep(3)
                continue
            raise
    return None


def _listar(endpoint, chave, params=None, limit=200):
    """Pagina uma listagem (per_page max 100) ate `limit` itens."""
    itens, pagina = [], 1
    while len(itens) < limit:
        p = dict(params or {})
        p.update({'page': pagina, 'per_page': min(100, limit - len(itens))})
        r = _request('GET', endpoint, params=p) or {}
        itens += r.get(chave, [])
        if not (r.get('pagination') or {}).get('next'):
            break
        pagina += 1
    return itens


def _total(endpoint, params=None):
    r = _request('GET', endpoint, params={**(params or {}), 'per_page': 1}) or {}
    return (r.get('pagination') or {}).get('count')


# ---------- Usuarios e clientes ----------

def listar_usuarios():
    return _listar('/v1/usuarios', 'users')


def testar_conexao():
    """Lista os usuarios do escritorio (confirma que o token vale)."""
    return listar_usuarios()


def listar_clientes(limit=200, **filtros):
    """filtros: cpf_cnpj, tags, updated_at_start_date (AAAA-MM-DD), order_by..."""
    return _listar('/v1/clientes', 'customers', filtros, limit)


def buscar_cliente_por_documento(cpf_cnpj):
    achados = listar_clientes(limit=1, cpf_cnpj=cpf_cnpj)
    return achados[0] if achados else None


def buscar_cliente(cliente_id):
    return _request('GET', f'/v1/clientes/{cliente_id}').get('customer')


def criar_cliente(nome, **campos):
    """campos: cpf_cnpj, email, phone_mobile, state, city, birthdate, tags... (ver CustomerInput)."""
    return _request('POST', '/v1/clientes',
                    json_data={'customer': {'name': nome, **campos}}).get('customer')


def atualizar_cliente(cliente_id, **campos):
    return _request('PATCH', f'/v1/clientes/{cliente_id}',
                    json_data={'customer': campos}).get('customer')


def adicionar_etiquetas_cliente(cliente_id, etiquetas):
    return _request('POST', f'/v1/clientes/{cliente_id}/etiquetas', json_data={'tags': etiquetas})


# ---------- Processos ----------

def listar_processos(limit=200, **filtros):
    """filtros: customer_id, number, status, kind, court, tags..."""
    return _listar('/v1/processos', 'lawsuits', filtros, limit)


def buscar_processo(processo_id_ou_numero):
    return _request('GET', f'/v1/processos/{processo_id_ou_numero}').get('lawsuit')


def listar_movimentacoes(processo_id_ou_numero, limit=100):
    return _listar(f'/v1/processos/{processo_id_ou_numero}/movimentacoes', 'movements', None, limit)


# ---------- Publicacoes (intimacoes) ----------

def listar_publicacoes(limit=200, **filtros):
    """filtros: status (nao_lida|tratada|arquivada), lawsuit_id, query,
    disponibilizacao_de/ate (AAAA-MM-DD), court."""
    return _listar('/v1/publicacoes', 'publications', filtros, limit)


# ---------- Atividades (prazos, tarefas, audiencias) ----------

def listar_atividades(limit=200, **filtros):
    """filtros: completed, customer_id, lawsuit_id, from, to, user_id, tags; type[]=Deadline etc."""
    return _listar('/v1/atividades', 'activities', filtros, limit)


def criar_atividade(titulo, tipo, criador_id, **campos):
    """tipo: Task, Event, Meeting, Dispatch, Hearing, Deadline... campos: start, end,
    deadline_on, customer_id, lawsuit_id, description, assignments."""
    return _request('POST', '/v1/atividades', json_data={'activity': {
        'title': titulo, 'type': tipo, 'creator_id': criador_id, **campos}}).get('activity')


def atualizar_atividade(atividade_id, **campos):
    return _request('PATCH', f'/v1/atividades/{atividade_id}',
                    json_data={'activity': campos}).get('activity')


# ---------- Assinaturas ----------

def enviar_arquivo(caminho, content_type='application/pdf', customer_id=None):
    """Sobe um arquivo para a Tramitacao (envio direto em 3 passos) e devolve o id do arquivo."""
    import base64
    import hashlib
    with open(caminho, 'rb') as f:
        conteudo = f.read()
    corpo = {'direct_upload': {
        'filename': os.path.basename(caminho), 'byte_size': len(conteudo), 'content_type': content_type,
        'checksum': base64.b64encode(hashlib.md5(conteudo).digest()).decode()}}
    envio = _request('POST', '/v1/arquivos/envios-diretos', json_data=corpo)['direct_upload']
    # o PUT vai direto ao storage: so os cabecalhos indicados, NUNCA o token da API
    r = requests.put(envio['upload_url'], data=conteudo, headers=envio.get('upload_headers') or {}, timeout=120)
    r.raise_for_status()
    registro = {'signed_id': envio['signed_id']}
    if customer_id:
        registro['customer_id'] = customer_id
    return _request('POST', '/v1/arquivos', json_data={'upload': registro})['upload']['id']


def criar_envelope_rascunho(nome, usuario_id, pdfs, assinantes):
    """Cria o envelope em RASCUNHO (nada e enviado a ninguem). pdfs: [caminhos].
    assinantes: [{'signer_type': 'customer'|'user'|'third_party', 'customer_id'|'user_id'|'full_name'+'email', ...}].
    Cada assinante recebe todos os documentos do envelope."""
    upload_ids = [enviar_arquivo(p) for p in pdfs]
    env = _request('POST', '/v2/assinaturas', json_data={'envelope': {
        'user_id': usuario_id, 'name': nome, 'upload_ids': upload_ids,
        'signers': [{'signature_type': 'assinante', **a} for a in assinantes]}})['envelope']
    return env


def excluir_envelope(envelope_id):
    return _request('DELETE', f'/v2/assinaturas/{envelope_id}')


def listar_envelopes(limit=100, **filtros):
    return _listar('/v2/assinaturas', 'envelopes', filtros, limit)


def buscar_envelope(envelope_id):
    return _request('GET', f'/v2/assinaturas/{envelope_id}')


def enviar_envelope(envelope_id, confirmar=False):
    """Dispara o envio aos signatarios. Exige confirmar=True (regra de ouro: so apos revisao humana)."""
    if not confirmar:
        print('  Envio NAO feito: passe confirmar=True depois da revisao da Dra. Faya / Dr. William.')
        return None
    return _request('POST', f'/v2/assinaturas/{envelope_id}/envio')


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from NUCLEO import ambiente  # noqa: F401  (carrega o .env)
    usuarios = testar_conexao()
    print(f'Conectado. {len(usuarios)} usuario(s):')
    for u in usuarios:
        print(f"  {u.get('id')}  {u.get('name')}")
    print('Clientes cadastrados:', _total('/v1/clientes'))
    print('Processos cadastrados:', _total('/v1/processos'))
    print('Publicacoes nao lidas:', _total('/v1/publicacoes', {'status': 'nao_lida'}))
    print('Atividades pendentes:', _total('/v1/atividades', {'completed': 'false'}))
