"""
Integracao com a API do LegalMail - Faya Barreiros Sociedade Individual de Advocacia
Somente LEITURA: saldo, intimacoes capturadas, processos e detalhe do processo.

API Base: https://api.legalmail.com.br  (NUNCA app.legalmail.com.br)
Auth: parametro api_key na query string (LEGALMAIL_API_KEY no config/.env)
Docs: https://app.legalmail.com.br/api/docs  |  regras: https://app.legalmail.com.br/agents.md

Regras da API que este modulo respeita:
- Nao ha sandbox; toda chamada vai para producao. Peticionar (pleading/send, complaint/send),
  apagar processo e afins NAO estao implementados aqui de proposito: exigem confirmacao humana.
- Limite de 120 req/min por workspace. Ritmo seguro: ~1 req/s. Um 429 PARA o fluxo (nao ha retry):
  3 respostas 429 em 10 min bloqueiam o workspace inteiro por 10 min ate 7 dias.
- Cobrado por requisicao: notices R$0,05/pagina, lawsuit/detail R$0,05, lawsuit/search R$0,07.
  Pagine sempre com paginas cheias (limit=50). Consulta repetida em 5 min (notices) e gratis.
- Datas em horario de Brasilia, formato YYYY-MM-DD.
"""
import os
import sys
import time
import requests

LEGALMAIL_BASE_URL = 'https://api.legalmail.com.br'
_INTERVALO_S = 1.0
_ultima = 0.0


class LegalMailErro(RuntimeError):
    pass


def _get_key():
    key = os.getenv('LEGALMAIL_API_KEY')
    if not key:
        print('ERRO: LEGALMAIL_API_KEY nao encontrado no config/.env')
        sys.exit(1)
    return key


def _get(endpoint, params=None):
    """GET com ~1 req/s. 402 (sem saldo) e 429 (limite/bloqueio) interrompem com erro claro."""
    global _ultima
    espera = _INTERVALO_S - (time.time() - _ultima)
    if espera > 0:
        time.sleep(espera)
    q = {k: v for k, v in (params or {}).items() if v is not None}
    q['api_key'] = _get_key()
    resp = requests.get(f'{LEGALMAIL_BASE_URL}{endpoint}', params=q, timeout=30,
                        headers={'Accept': 'application/json', 'User-Agent': 'faya-barreiros-automacoes/1.0'})
    _ultima = time.time()
    restante = resp.headers.get('X-RateLimit-Remaining')
    if restante is not None and restante.isdigit() and int(restante) < 30:
        print(f'  LegalMail: so restam {restante} requisicoes na janela; aguardando 60s...')
        time.sleep(60)
    if resp.status_code == 429:
        try:
            d = resp.json()
        except ValueError:
            d = {}
        raise LegalMailErro(
            f"LegalMail 429 ({d.get('error', 'limite')}): aguarde {resp.headers.get('Retry-After', '?')}s "
            f"(bloqueado_ate={d.get('blocked_until')}). Fluxo interrompido de proposito, nao repita.")
    if resp.status_code == 402:
        raise LegalMailErro('LegalMail 402: saldo de creditos insuficiente. Recarregue no Painel da API.')
    if not resp.ok:
        raise LegalMailErro(f'LegalMail erro {resp.status_code} em {endpoint}: {resp.text[:200]}')
    return resp.json() if resp.text else {}


def saldo():
    """Saldo de creditos (gratuito). Use para conferir a chave/workspace antes de lotes."""
    return _get('/api/v1/balance')


def listar_intimacoes(data_captura_inicio=None, data_captura_fim=None, max_paginas=20, **filtros):
    """Intimacoes capturadas, paginando (limit=50, ordem asc por captura). Custa R$0,05 por pagina.
    Filtros extras: processo, partes, tipo, fonte, tribunal, destinatario_id, prazo_status
    ('pendente'|'cumprido'|'excedido'), data_disponibilizacao_inicio/fim, teor..."""
    itens, offset = [], 0
    for _ in range(max_paginas):
        r = _get('/api/v1/notices', dict(filtros, data_captura_inicio=data_captura_inicio,
                                         data_captura_fim=data_captura_fim, ordenar_por='data_captura',
                                         ordem='asc', limit=50, offset=offset))
        lote = r.get('notices', [])
        itens += lote
        offset += 50
        if not lote or offset >= r.get('total', 0):
            break
    else:
        print(f'  LegalMail: parou em {max_paginas} paginas; ha mais intimacoes (use filtros/datas).')
    return itens


def intimacoes_do_dia(data=None):
    """Intimacoes capturadas em um dia (YYYY-MM-DD; padrao hoje)."""
    data = data or time.strftime('%Y-%m-%d')
    return listar_intimacoes(data, data)


def detalhe_processo(numero_processo=None, idprocessos=None):
    """Detalhe de um processo (R$0,05; mesma consulta em 24h e gratis)."""
    return _get('/api/v1/lawsuit/detail', {'numero_processo': numero_processo, 'idprocessos': idprocessos})


def listar_processos(max_paginas=20):
    """Processos do workspace (id, numero, classe)."""
    itens, offset = [], 0
    for _ in range(max_paginas):
        r = _get('/api/v1/lawsuit/all', {'limit': 50, 'offset': offset})
        lote = r if isinstance(r, list) else r.get('lawsuits') or r.get('data') or []
        itens += lote
        offset += 50
        if len(lote) < 50:
            break
    return itens


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'saldo'
    if cmd == 'saldo':
        print(saldo())
    elif cmd == 'hoje':
        for n in intimacoes_do_dia():
            print(n.get('data_captura'), n.get('numero_processo'), n.get('tipo'), n.get('tribunal'), n.get('prazo_status'))
    else:
        print('uso: python legalmail_integration.py [saldo|hoje]')
