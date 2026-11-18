# Faya Barreiros Advocacia - Central de Automações

> Escritório: **Faya Barreiros Sociedade Individual de Advocacia** (CNPJ 67.928.823/0001-52),
> Av. Tancredo Neves, 1283, Sala 1001, Salvador/BA. Atendimento presencial em Salvador e online para todo o Brasil.
> Advogados: **Dra. Faya Milla Magalhães Mascarenhas Barreiros** (previdenciário, cálculos e serviços avulsos)
> e **Dr. William Ricardo Coelho** (tributário: execução fiscal e gestão de passivo).
> Equipe: Bárbara (secretária: e-mails, prazos, recibos, pasta no drive) e um estagiário (petições, pushs
> processuais, baixa de decisões).
> Ferramentas do escritório: **Notion** (prazos, financeiro, processos), **Tramitação Inteligente** (assinatura
> digital e andamento), **Asaas** (cobrança), **OneDrive/SharePoint** (documentos), PJe, Claude.
> Quer rodar na **nuvem**. Não usa ADVBOX, Google Workspace nem CRM de WhatsApp.

## Estado do projeto
Ambiente montado em **22/10/2026** a partir do briefing de 18/10/2026 e **completado em 23/10/2026** com o material
que a Dra. Faya e o Dr. William enviaram: timbrados oficiais dos dois, contratos, procuração e declaração oficiais,
DNA das peças. Tudo que ainda não veio está marcado com `[CONFERIR]` ou `[PREENCHER]` e **trava o envio** de propósito.
A lista do que falta é **`docs/ONBOARDING.md`**.

**Duas áreas, dois advogados.** Previdenciário = Dra. Faya (timbrado bordô, padrão do sistema). Tributário = Dr. William
(timbrado azul-marinho; `novo_documento('william')`). A pasta do cliente nasce em `PREVIDENCIARIO/` ou `TRIBUTARIO/` e
o contrato certo sai pela área (`CONTRATACAO/documentos.py`, `docs/CAMPOS_DOS_MODELOS.md`).

## Regra de ouro
- **A IA não protocola e não envia nada ao cliente nem ao processo sem flag explícita.**
  Toda peça, mensagem e relatório sai para revisão humana (Faya e William revisam, sempre).
- Exceção prevista no briefing: a IA pode **definir a estratégia sozinha** só em casos simples e
  padronizados e em **petições de andamento**. Isso ainda não está habilitado; ligar exige decisão
  dos advogados e um tipo de peça novo em `JUDICIAL/main.py`.
- Nunca inventar dado de cliente, CDA, valor, data, número de processo ou jurisprudência.
  Sem dado: `[CONFERIR]`.
- Prescrição e decadência: só calcular com as datas-chave nos documentos, mostrando a conta.
- Documento com `[CONFERIR]` ou `[PREENCHER]` **nunca** vai para assinatura (trava no código).
- **Inegociáveis do escritório:** a reunião de fechamento com o cliente (William) e o ciclo dos prazos
  das demandas externas de cálculos e serviços avulsos (Faya). A automação apoia esses dois pontos,
  não os substitui.
- Pilar da atuação: **analisar a origem dos débitos antes de qualquer medida.**

## Mapa: etapa do escritório -> módulo
| Etapa | Módulo | Comandos |
|---|---|---|
| Lead chega (WhatsApp, Instagram, indicação), qualificação e agendamento | `COMERCIAL/` | `qualificar`, `transcrever`, `lead`, `painel`, `mensagem` |
| Fechou: contrato, procuração, pasta, cobrança de documentos | `CONTRATACAO/` | `novo`, `enviar`, `acompanhar`, `painel`, `exemplo` |
| Análise e peças: relatório de CDAs, recursos, embargos, exceção, parecer previdenciário | `JUDICIAL/` | `checklist`, `peca --tipo ...`, `tipos` |
| **Motor tributário**: relatório de passivo fiscal federal (16 seções) a partir dos PDFs do e-CAC/Regularize/CDAs; consulta de legislação; prospecção PGFN | `TRIBUTARIO/` | `passivo`, `legislacao`, `prospeccao/` |
| Processo andando: intimações (DJEN), prazos, avisos ao cliente; prazo no Notion com `varredura --notion` | `CONTROLADORIA/` | `varredura`, `avisos-cliente`, `relatorio-clientes`, `planilha`, `parados`, `finalizar` |
| Honorários, inadimplência, fechamento (Asaas); Asaas → Notion com `notion` | `FINANCEIRO/` | `cobranca`, `inadimplencia`, `fechamento`, `honorarios-novos`, `notion` |

| **Kit previdenciário** (importado do pacote `faya-barreiros-previdenciario` em 18/11/2026): 27 iniciais e 14 relatórios da Dra. Faya com `{{campos}}`, base de leis por artigo, calculadora de apoio (tempo, carência, graça, EC 103), POPs, checklists por produto e mensagens | `KIT_PREVIDENCIARIO/` | `pecas/gerar_peca.py listar\|campos\|preencher\|conferir\|docx`, `leis/buscar_lei.py --lei 8213 --art 15`, `calculos/simular.py caso.json` |

Uso: `python MODULO/main.py <comando>` na pasta do sistema. Quase todo comando aceita `--exemplo`.

## Estrutura
```
NUCLEO/          ambiente (.env, caminhos), ia (Claude), docx_escritorio (timbrado), caminhos
INTEGRACOES/     tramitacao_integration (Tramitação Inteligente: clientes, processos, publicações, atividades, assinaturas; token `TRAMITACAO_API_TOKEN`; ligada em 23/10/2026, só o cliente da API, ainda não plugada nos módulos), asaas, zapsign, dapi_whatsapp, comunica_djen (DJEN/PJe), jurisprudencias_ia (pesquisa de decisões, MCP), advbox (NÃO usado), meta_ads, gmail, gcalendar (Google Agenda: criar/listar eventos sem convidar ninguém; cliente OAuth em `config/credentials_gcalendar.json`, 1ª vez `python INTEGRACOES/gcalendar_integration.py autorizar`; ainda não plugada nos módulos)
COMERCIAL/       qualificação do lead, transcrição, funil local
CONTRATACAO/     triagem pela IA, documentos, pasta do cliente, envio, acompanhamento
JUDICIAL/        checklist de documentos e minutas (tributário e previdenciário)
TRIBUTARIO/      motor tributário: passivo fiscal federal, base de legislação (CTN, LEF, Leis 10.522/13.988...), prospecção PGFN
CONTROLADORIA/   varredura do DJEN, prazos, avisos e relatório ao cliente
FINANCEIRO/      cobrança (Asaas + WhatsApp), inadimplência, fechamento
BASE_CONHECIMENTO/  DNA_PECAS.md (DNA ativo: estrutura e citações das peças reais; o texto delas fica em MATERIAL_FAYA/, fora do git)
DOCS_MODELOS/    contratos, procurações, declaração e termo de renúncia OFICIAIS (campos {{...}}); só a procuração tributária ainda é provisória
config/          escritorio.py, equipe.py, .env (não versionado)
deploy/          instalador Windows, agendador, gerador dos modelos provisórios, cron para servidor
SAIDA/           relatórios gerados (não versionado: tem dado de cliente)
CLIENTES/        pastas dos clientes (não versionado)
```

## Pontos que ainda não casam com a realidade do escritório (decidir antes de implantar)
1. **Tarefas e prazos:** o código de Controladoria/Contratação cria tarefas no ADVBOX. O escritório usa Notion.
   Sem `ADVBOX_API_TOKEN` o sistema apenas lista o que seria feito (modo seguro). Integração com Notion
   (ou com a Tramitação Inteligente) é módulo novo: precisa do token/API e do desenho das abas.
2. **Documentos no OneDrive/SharePoint:** o sistema grava na pasta apontada por `PASTA_CLIENTES_RAIZ`.
   Numa máquina com o OneDrive sincronizado isso já funciona. Em servidor na nuvem, é preciso montar o
   OneDrive (rclone) ou usar a Microsoft Graph API. Ver `docs/DEPLOY_NUVEM.md`.
3. **Assinatura:** o escritório assina dentro da Tramitação Inteligente; o código usa ZapSign. Sem
   `ZAPSIGN_API_TOKEN` os documentos ficam prontos na pasta para assinar do jeito que o escritório já faz.
4. **Áreas:** resolvido em 23/10/2026. A esteira escolhe a área pelo cadastro/triagem (`PREVIDENCIARIO` ou
   `TRIBUTARIO`; `AMBOS` segue tributário) e usa o contrato certo.

## Primeiros passos na máquina do escritório
```
git clone https://github.com/pabadvogados-hub/faya-barreiros-advocacia.git
cd faya-barreiros-advocacia
deploy\instalar_windows.bat
copy config\.env.example config\.env     (e preencher)
python CONTRATACAO/main.py exemplo        (teste com caso fictício)
```

## O que NÃO fazer
- Não colocar chave de API, token ou senha em arquivo versionado: tudo no `config/.env`.
- Não apagar os `[PREENCHER]` dos modelos sem o texto oficial do escritório - eles são a trava.
- Não subir para este repositório nada com dado real de cliente (nome, CPF, CNPJ, CDA, documento).
  Os arquivos que o escritório manda (contratos e peças reais) ficam em `MATERIAL_FAYA/` (ignorada pelo git);
  só sobe o que virou modelo com `{{CAMPOS}}`. Conta bancária e Pix dos contratos ficam no `config/.env`.
  O repositório é **público**: serve para instalar o sistema em qualquer máquina do escritório.

## Kit previdenciário (`KIT_PREVIDENCIARIO/`)
Trazido em 18/11/2026 do repositório `faya-barreiros-previdenciario`. **Não confundir com a pasta `PREVIDENCIARIO/` do
cliente no OneDrive**: esta (`KIT_`) é código e modelos. Regras valem as mesmas do sistema (revisão humana, nada inventado).
- `pecas/` modelos anonimizados + `gerar_peca.py` (põe no timbrado; com `[CONFERIR]`/`{{campo}}` sai "MINUTA - NÃO PROTOCOLAR"). Pauta de revisão em `pecas/00_INDICE.md`.
- `leis/` texto vigente por artigo (16 normas, `buscar_lei.py`). Antes de citar artigo, puxar daqui. IN 128/2022 só na redação original.
- `calculos/` simulador de apoio (56 testes); **o número oficial é o do software da Dra. Faya**.
- `pops/`, `checklists/`, `mensagens/` (MSG-01 a 07) — os POPs citam rotinas do outro sistema (`automacoes/...`) que aqui não existem; usar os módulos equivalentes (CONTROLADORIA, FINANCEIRO, CONTRATACAO).
- Agentes `previdenciario`, `calculista`, `revisor-pecas` e skill `triagem-previdenciaria` em `.claude/`.
- **Adaptação à nossa realidade:** leia `KIT_PREVIDENCIARIO/ADAPTACAO.md` antes dos POPs: ela traduz rotinas, pastas e Notion do kit para o que existe aqui. **Não importado** (decidir): painel de demandas externas de cálculo (a fila já é o banco Fluxo RT do Notion), Pix/NF/backup do pacote de origem, agentes `atendimento`/`controladoria`/`financeiro`.
- **Integração com o JUDICIAL:** `python JUDICIAL/main.py modelos` lista os modelos; `peca "CLIENTE" --tipo peticao-inicial-previdenciaria --modelo <slug>` entrega o modelo da Dra. Faya como referência à IA. O `gerar_peca.py docx` do kit continua sendo o caminho para pôr a minuta no timbrado e travar pendências. Não há geração duplicada: o JUDICIAL redige, o kit formata e confere.

## Notion (ligado em 18/11/2026)
`INTEGRACOES/notion_escritorio.py` grava nas bases que a Dra. Faya já tem (IDs e colunas reais em `docs/NOTION_MAPA.md`):
Prazos/Tarefas (prazos do DJEN), Transações Financeiras (Asaas), Fluxo RT (demandas de cálculo, inclusive de parceiros).
Só cria linha; só altera linha que ele mesmo criou; nunca apaga; não cria opção nova em coluna de seleção.
Simula por padrão e, gravando, pergunta item a item: **agendado sem terminal, não grava nada**.
Asaas: em 18/11/2026 a conta da chave configurada tinha 0 cobranças e 0 clientes.

## Financeiro (decidido em 18/11/2026)
**O Asaas está pausado.** A fonte do financeiro é o artefato **FINANCEIRO FAYA BARREIROS**
(https://claude.ai/artifact/TLTNLuxv8MAJrQUy86fa4M): entradas, saídas e caixa 12% (coleção `lanc`, um documento por
mês) e a aba **Despesas mensais** (privada de cada pessoa, `data/users/<id>/budget`), que absorveu o antigo artefato
DESPESAS MENSAIS. Ler e lançar por ele, com a ferramenta `ArtifactData`. Script local não lê esse banco (não há
chave de API para ele). `FINANCEIRO/` (Python, Asaas) e `FINANCEIRO/main.py notion` ficam parados até o Asaas voltar.

