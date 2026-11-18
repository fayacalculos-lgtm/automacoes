# -*- coding: utf-8 -*-
"""
Integracao com o Jurisprudencias.ai (servidor MCP sobre HTTP) - so leitura.

Pesquisa decisoes de tribunais brasileiros (STF, STJ, TRFs, TJs, CARF...) e traz a ementa.
Endpoint: https://jurisprudencias.ai/mcp  (JSON-RPC, autenticacao Bearer)
Credencial no config/.env:  JURISPRUDENCIAS_IA_API_KEY  (JURISPRUDENCIAS_IA_BASE_URL e opcional)

Ferramentas do servidor: list_courts, search_decisions, lookup_decision.

REGRA DO ESCRITORIO: o que vem daqui e material de pesquisa, nunca citacao pronta.
Toda decisao usada em peca sai com [CONFERIR] ate o advogado abrir a fonte e validar.

CLI:
    python INTEGRACOES/jurisprudencias_ia.py tribunais
    python INTEGRACOES/jurisprudencias_ia.py buscar --tribunal stj --termos "prescricao intercorrente" "execucao fiscal"
    python INTEGRACOES/jurisprudencias_ia.py buscar --tribunal trf1 --frase "denuncia espontanea" --de 2024-01-01
    python INTEGRACOES/jurisprudencias_ia.py decisao --tribunal stj --processo 202201407090
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'NUCLEO'))
import ambiente  # noqa: E402,F401  (carrega config/.env)
import requests  # noqa: E402

URL_PADRAO = "https://jurisprudencias.ai/mcp"
TIMEOUT = 60


class JurisprudenciasIAErro(RuntimeError):
    pass


def configurado():
    return ambiente.tem_credencial("JURISPRUDENCIAS_IA_API_KEY")


def _chamar(metodo, params=None):
    if not configurado():
        raise JurisprudenciasIAErro("JURISPRUDENCIAS_IA_API_KEY nao preenchida no config/.env")
    url = os.getenv("JURISPRUDENCIAS_IA_BASE_URL") or URL_PADRAO
    resp = requests.post(
        url,
        headers={
            "Authorization": "Bearer " + os.environ["JURISPRUDENCIAS_IA_API_KEY"],
            "MCP-Protocol-Version": "2025-06-18",
            "Accept": "application/json, text/event-stream",
        },
        json={"jsonrpc": "2.0", "id": 1, "method": metodo, "params": params or {}},
        timeout=TIMEOUT,
    )
    if resp.status_code != 200:
        raise JurisprudenciasIAErro(f"HTTP {resp.status_code}: {resp.text[:300]}")
    corpo = resp.json()
    if "error" in corpo:
        raise JurisprudenciasIAErro(str(corpo["error"]))
    return corpo["result"]


def _ferramenta(nome, argumentos):
    res = _chamar("tools/call", {"name": nome, "arguments": argumentos})
    if res.get("isError"):
        texto = " ".join(c.get("text", "") for c in res.get("content", []))
        raise JurisprudenciasIAErro(texto or "erro na ferramenta " + nome)
    return res.get("structuredContent") or res


def listar_tribunais():
    """Tribunais e bases disponiveis (sigla, total indexado, orgaos julgadores)."""
    return _ferramenta("list_courts", {})


def buscar(tribunal, termos=None, qualquer=None, frases=None, excluir=None, texto=None,
           orgaos=None, pagina=0, ordenar="publication_date",
           pub_de=None, pub_ate=None, julg_de=None, julg_ate=None):
    """
    Busca decisoes. Prefira termos/qualquer/frases/excluir (consulta estruturada) a `texto`.
    termos = todos devem aparecer; qualquer = sinonimos (OR); frases = expressao exata.
    """
    args = {"court": tribunal.lower(), "page": pagina, "sort_by": ordenar}
    intencao = {k: v for k, v in (("required", termos), ("any_of", qualquer),
                                  ("phrases", frases), ("exclude", excluir)) if v}
    if intencao:
        args["query_intent"] = intencao
    elif texto:
        args["query"] = texto
    else:
        raise ValueError("informe termos, frases ou texto")
    for chave, valor in (("chambers", orgaos), ("pub_from", pub_de), ("pub_to", pub_ate),
                         ("trial_from", julg_de), ("trial_to", julg_ate)):
        if valor:
            args[chave] = valor
    return _ferramenta("search_decisions", args)


def decisao(tribunal, numero_processo):
    """Dados completos de uma decisao (ementa integral, relator, datas, URL da fonte)."""
    return _ferramenta("lookup_decision", {"court": tribunal.lower(), "process_number": numero_processo})


def _imprimir_busca(res):
    for d in res.get("data", []):
        print(f"- {d.get('process_type')} | proc. {d.get('process_number')} | {d.get('rapporteur')}")
        print(f"  {d.get('adjudicating_body')} | julg. {d.get('trial_date')} | publ. {d.get('publication_date')}")
        print("  " + (d.get("excerpt") or "").replace("\n", " ")[:400])
        print("  fonte: " + str(d.get("url")) + "   [CONFERIR]\n")


def main():
    p = argparse.ArgumentParser(description="Pesquisa de jurisprudencia (Jurisprudencias.ai)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tribunais")
    b = sub.add_parser("buscar")
    b.add_argument("--tribunal", required=True)
    b.add_argument("--termos", nargs="*")
    b.add_argument("--qualquer", nargs="*")
    b.add_argument("--frase", nargs="*", dest="frases")
    b.add_argument("--excluir", nargs="*")
    b.add_argument("--texto")
    b.add_argument("--pagina", type=int, default=0)
    b.add_argument("--de", dest="pub_de")
    b.add_argument("--ate", dest="pub_ate")
    b.add_argument("--json", action="store_true")
    d = sub.add_parser("decisao")
    d.add_argument("--tribunal", required=True)
    d.add_argument("--processo", required=True)
    a = p.parse_args()
    try:
        if a.cmd == "tribunais":
            print(json.dumps(listar_tribunais(), ensure_ascii=False, indent=1))
        elif a.cmd == "buscar":
            res = buscar(a.tribunal, a.termos, a.qualquer, a.frases, a.excluir, a.texto,
                         pagina=a.pagina, pub_de=a.pub_de, pub_ate=a.pub_ate)
            print(json.dumps(res, ensure_ascii=False, indent=1)) if a.json else _imprimir_busca(res)
        else:
            print(json.dumps(decisao(a.tribunal, a.processo), ensure_ascii=False, indent=1))
    except (JurisprudenciasIAErro, ValueError, requests.RequestException) as e:
        sys.exit("Erro: " + str(e))


if __name__ == "__main__":
    main()
