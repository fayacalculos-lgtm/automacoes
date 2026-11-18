"""
Integracao com API Notion - Faya Barreiros Sociedade Individual de Advocacia
Modulo para buscar paginas, consultar bancos (prazos, financeiro, processos) e criar itens.

API Base: https://api.notion.com/v1
Auth: Bearer NOTION_TOKEN (integracao interna; compartilhe as paginas/bancos com ela)
"""
import os
import sys
import time
import requests


NOTION_BASE_URL = 'https://api.notion.com/v1'
NOTION_VERSION = '2022-06-28'


def _get_token():
    token = os.getenv('NOTION_TOKEN')
    if not token:
        print('ERRO: NOTION_TOKEN nao encontrado no .env')
        sys.exit(1)
    return token


def _headers():
    return {
        'Authorization': f'Bearer {_get_token()}',
        'Notion-Version': NOTION_VERSION,
        'Content-Type': 'application/json',
    }


def _request(method, endpoint, params=None, json_data=None, retries=2):
    url = f'{NOTION_BASE_URL}{endpoint}'
    for tentativa in range(retries + 1):
        try:
            resp = requests.request(method, url, headers=_headers(),
                                    params=params, json=json_data, timeout=30)
            if resp.status_code == 429:
                wait = int(resp.headers.get('Retry-After', 5))
                print(f'  Rate limit Notion. Aguardando {wait}s...')
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json() if resp.text else {}
        except requests.exceptions.HTTPError:
            print(f'  Notion erro ({resp.status_code}): {resp.text[:200]}')
            if tentativa < retries and resp.status_code >= 500:
                time.sleep(3)
                continue
            raise
        except requests.exceptions.RequestException as e:
            print(f'  Notion conexao falhou: {e}')
            if tentativa < retries:
                time.sleep(3)
                continue
            raise
    return None


def testar_conexao():
    """Retorna o bot da integracao (confirma que o token vale)."""
    return _request('GET', '/users/me')


def buscar(texto='', tipo=None, limit=100):
    """Busca paginas/bancos compartilhados com a integracao. tipo: 'page' ou 'database'."""
    corpo = {'query': texto, 'page_size': min(limit, 100)}
    if tipo:
        corpo['filter'] = {'property': 'object', 'value': tipo}
    return _request('POST', '/search', json_data=corpo).get('results', [])


def consultar_banco(database_id, filtro=None, ordem=None, limit=100):
    """Consulta um banco (paginando). filtro/ordem seguem o formato da API do Notion."""
    resultados, cursor = [], None
    while len(resultados) < limit:
        corpo = {'page_size': min(limit - len(resultados), 100)}
        if filtro:
            corpo['filter'] = filtro
        if ordem:
            corpo['sorts'] = ordem
        if cursor:
            corpo['start_cursor'] = cursor
        r = _request('POST', f'/databases/{database_id}/query', json_data=corpo)
        resultados += r.get('results', [])
        if not r.get('has_more'):
            break
        cursor = r.get('next_cursor')
    return resultados


def criar_pagina(database_id, propriedades):
    """Cria um item num banco. propriedades no formato da API (ver docs do Notion)."""
    return _request('POST', '/pages', json_data={
        'parent': {'database_id': database_id},
        'properties': propriedades,
    })


def atualizar_pagina(page_id, propriedades):
    return _request('PATCH', f'/pages/{page_id}', json_data={'properties': propriedades})


def titulo(objeto):
    """Titulo legivel de uma pagina ou banco retornado pela API."""
    if objeto.get('object') == 'database':
        return ''.join(t.get('plain_text', '') for t in objeto.get('title', []))
    for prop in objeto.get('properties', {}).values():
        if prop.get('type') == 'title':
            return ''.join(t.get('plain_text', '') for t in prop['title'])
    return ''


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from NUCLEO import ambiente  # noqa: F401  (carrega o .env)
    bot = testar_conexao()
    print(f"Conectado como: {bot.get('name')} ({bot.get('bot', {}).get('workspace_name')})")
    achados = buscar()
    print(f'{len(achados)} item(ns) compartilhado(s) com a integracao:')
    for o in achados:
        print(f"  [{o['object']}] {titulo(o)}  {o['id']}")
