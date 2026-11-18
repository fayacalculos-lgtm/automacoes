# POP-ATD-03 — Onboarding do cliente novo (contrato, pasta, documentos)

Versão 1 — 18/11/2026

| | |
|---|---|
| **Dono do POP** | Dra. Faya |
| **Quem executa** | Bárbara; Dra. Faya assina e define honorários |
| **Gatilho** | Cliente fechou na reunião |
| **Termina quando** | Kit assinado, pasta criada no OneDrive, card no Notion, cobrança no Asaas (se houver honorário inicial) e documentos mínimos recebidos |
| **Prazo** | Kit enviado no mesmo dia; documentos cobrados até ficarem completos (MSG-02) |

## Passo a passo

1. **Gerar o kit de representação** com os dados do cliente, por `python CONTRATACAO/main.py novo ...` (modelos oficiais em `DOCS_MODELOS/`, campos em `docs/CAMPOS_DOS_MODELOS.md`): — *mesmo dia*
   - `PROCURACAO_PREVIDENCIARIA_MODELO` (com o objeto da ação);
   - `PREV_CONTRATO_EXITO` ou `PREV_CONTRATO_EXITO_SALARIOS`, conforme o combinado com o cliente `[CONFERIR a variante]`;
   - `DECLARACAO_HIPOSSUFICIENCIA_MODELO`, se a inicial vai pedir gratuidade;
   - `PREV_TERMO_RENUNCIA_JEF`, **só** depois da conta do valor da causa (POP-PREV-02).
   A geração trava documento com `[CONFERIR]` ou `[PREENCHER]`: corrigir antes de mandar.
2. **Assinatura** pela Tramitação Inteligente. Depois de revisar os `.docx`, `python CONTRATACAO/main.py enviar "PASTA DO CLIENTE"`; a integração (`INTEGRACOES/tramitacao_integration.py`) cria o envelope em **rascunho** e só envia com confirmação humana. — *mesmo dia*
3. **Boas-vindas** com a MSG-04: canais oficiais, o que esperar e o alerta do golpe do falso advogado. — *depois da assinatura*
4. **Pasta no OneDrive**: o `CONTRATACAO/main.py novo` já cria `PREVIDENCIARIO/<NOME>/` com as subpastas padrão (`ADAPTACAO.md` §2). — *mesmo dia*
5. **Card no Notion** (banco **Base de Dados Clientes Law Notion**, `Área` = Previdenciário; cliente + caso): benefício, NB, DER, classificação da triagem, responsável. — *mesmo dia*
6. **Asaas**: só se houver honorário inicial ou parcelado (`python FINANCEIRO/main.py honorarios-novos` lista contrato novo sem cobrança). Honorário de
   implantação e de êxito só se cobra quando o benefício sai (POP-PREV-07). — *mesmo dia*
7. **Cobrar os documentos** do checklist do produto (`KIT_PREVIDENCIARIO/checklists/diagnostico/CK-DIAG-PREV-*`) com a MSG-02, até completar. — *D+2, D+5, D+10*

## O que vira tarefa no Notion

> Lançar no banco **Prazos/Tarefas** do Notion conforme `ADAPTACAO.md` §3 (título em `Texto`, prazo em `Data`, etapa em `Fluxo RT`). Hoje o lançamento é manual: nenhum módulo grava no Notion.

| Tarefa | Responsável | Prazo |
|---|---|---|
| `[ASSINATURA] Kit - {{cliente}}` | Bárbara | D+1 |
| `[DOCUMENTOS] Cobrar - {{cliente}}` | Bárbara | D+2, D+5, D+10 |
| `[CÁLCULO] {{cliente}} - {{produto}}` | Dra. Faya | 2 dias úteis após CNIS completo (POP-PREV-02) |

## Pendências

- `[CONFERIR]` Como o documento assinado volta para a pasta do cliente (a API de envelopes está integrada; o retorno ainda é à mão).
- Bases do Notion: mapeadas em `docs/NOTION_MAPA.md`; falta só um módulo que grave tarefa nelas.
