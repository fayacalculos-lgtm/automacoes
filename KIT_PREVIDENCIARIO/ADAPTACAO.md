# Adaptação do kit à realidade do escritório

Feito em 18/11/2026. O kit veio de outro pacote (`faya-barreiros-previdenciario`), pensado para uma VPS com
Notion, OneDrive por rclone, painel web e Asaas direto. Aqui o sistema é outro. **Esta página é a tradução**:
quando um POP, checklist ou mensagem citar algo da coluna "No kit", vale a coluna "Aqui".

## 1. Rotinas: o que o kit chama de... e o que existe aqui

| No kit | Aqui | Observação |
|---|---|---|
| `automacoes/controladoria/` (DJEN → Notion) | `python CONTROLADORIA/main.py varredura --dias 1` | Lê o DJEN pelas OABs e a Tramitação Inteligente. A tarefa sai **na Tramitação** (atividade/prazo), com `--criar-tarefas`, item a item, com confirmação humana. Não grava no Notion |
| Prazo do e-mail do INSS (lançado à mão) | `python CONTROLADORIA/prazos_administrativos.py 30` | Lê só e-mail, data preliminar (ciência + 30 dias na exigência/recurso). Nunca cria tarefa nem responde |
| Aviso de decisão ao cliente | `python CONTROLADORIA/main.py avisos-cliente` | Gera o texto e um CSV para revisar; só envia com `--enviar` |
| Relatório periódico ao cliente | `python CONTROLADORIA/main.py relatorio-clientes --dias 30` | Idem |
| Processo parado | `python CONTROLADORIA/main.py parados --dias 30` | |
| Encerramento do caso | `python CONTROLADORIA/main.py finalizar "PASTA DO CLIENTE"` | |
| `automacoes/comum/tramitacao.py` ("esqueleto") | `INTEGRACOES/tramitacao_integration.py` | **Tem API**: clientes, processos, movimentações, publicações, atividades e envelopes de assinatura. Envelope nasce em rascunho; **enviar** exige `confirmar=True` |
| `automacoes/drive/criar_estrutura.py` (pasta do cliente) | `python CONTRATACAO/main.py novo ...` | Cria `CLIENTES FAYA/01 - EM ANDAMENTO/<NOME>/` com as subpastas abaixo |
| `automacoes/drive/arquivar_documento.py` | à mão, nas subpastas abaixo | Não há automação equivalente |
| `modelos/01..05` (kit de representação) | `DOCS_MODELOS/` (procuração e contratos previdenciários, declaração, termo de renúncia do JEF) | Já são os oficiais. Campos em `docs/CAMPOS_DOS_MODELOS.md`. Substabelecimento: não há modelo oficial aqui |
| `automacoes/financeiro/regua_cobranca.py` | `python FINANCEIRO/main.py cobranca` (e `--enviar`) | Régua em `config/regras_financeiras.py`: lembrete D-3 e no dia; atraso D+1, D+5 e D+15. Ver §4 |
| `automacoes/financeiro/nova_cobranca.py` | `python FINANCEIRO/main.py honorarios-novos` | Lista contratos novos sem cobrança no Asaas |
| Relatório diário / inadimplência | `FINANCEIRO/main.py inadimplencia` e `fechamento MM/AAAA` | |
| Nota fiscal, Pix agendado da equipe, backup cifrado | **não existe aqui** | POP-ADM-02 fica como roteiro manual; ver o aviso nele |
| Painel de demandas externas e link de pedido dos parceiros | **não existe aqui**. A fila já é o banco **Fluxo RT** do Notion | Ver POP-PREV-06 |
| Agentes `atendimento`, `controladoria`, `financeiro` | **não importados**. Os POPs que os citam: a sessão do Claude Code propõe o texto e a pessoa envia | Só `previdenciario`, `calculista` e `revisor-pecas` existem |
| `--go` / "dry-run" | `--enviar`, `--criar-tarefas`, `--atualizar-advbox` (sem a flag, nada sai) | Mesma ideia: simula por padrão |
| ADVBOX | não usado. `INTEGRACOES/tramitacao_como_advbox.py` entrega a Tramitação no formato que a Controladoria espera | |

## 2. Pasta do cliente

Raiz = `PASTA_CLIENTES_RAIZ` = `C:\Users\Faya\OneDrive\ADVOCACIA` (definida em 18/11/2026). As áreas ficam em
`config/escritorio.py`:

| Área | Pasta real |
|---|---|
| Previdenciário (Dra. Faya) | `CLIENTES FAYA/01 - EM ANDAMENTO/<NOME>` (arquivados em `02 - ARQUIVADOS`, triagem em `03 - A VERIFICAR`) |
| Tributário | `CLIENTE TRIBUTÁRIOS/TRIBUTARIO/<NOME>` |

As pastas **que já existem** têm a organização que a equipe deu a elas: use o que estiver lá. As subpastas numeradas
abaixo só nascem nas pastas que o `CONTRATACAO/main.py novo` criar:

| Subpasta | Usar para |
|---|---|
| `00 CONTRATACAO` | triagem, contrato, procuração, declaração, `caso.json` |
| `01 DOCUMENTOS PESSOAIS` | RG, CPF, CNH |
| `03 COMPROVANTE DE ENDERECO` | comprovante |
| `10 PREVIDENCIARIO` | CNIS, CTPS, PPP/LTCAT, laudos e exames, **cartas e decisões do INSS**, sentenças e atos recebidos |
| `11 PECAS` | minutas e peças (as geradas pelo `JUDICIAL` caem aqui), relatórios e cálculos |
| `12 PROTOCOLOS` | comprovantes de protocolo |

As subpastas `02`, `04` a `09` são do fluxo tributário (empresa, CDAs, execução fiscal): **ficam vazias** no
previdenciário. As pastas numeradas do kit (`02_CNIS_E_VINCULOS`, `04_SAUDE`, `05_INSS_ADMINISTRATIVO`,
`08_PROCESSO_JUDICIAL`...) **não existem aqui**; use a tabela acima. Se a Dra. Faya quiser separar CNIS, saúde e
INSS dentro de `10 PREVIDENCIARIO`, é decisão dela `[CONFERIR]`.

Demanda de cálculo: a fila é o banco **Fluxo RT** do Notion (decidido em 18/11/2026). No OneDrive já existem
`ADVOCACIA/CALCULOS 2026/<CASO>` (uma pasta por cálculo) e `ADVOCACIA/PARCEIROS/<PARCEIRO>`: guardar lá, como o
escritório já faz `[CONFERIR qual das duas para o pedido novo de parceiro]`.

## 3. Notion: onde cai cada tarefa

Mapa completo em `docs/NOTION_MAPA.md` (nomes exatos das colunas, com os espaços e erros de grafia).
**Ligado em 18/11/2026** (simulação por padrão; gravando, pergunta item a item):
- `python CONTROLADORIA/main.py varredura --dias 1 --notion [--gravar-notion]`: prazo do DJEN vira linha em
  Prazos/Tarefas (`Contratante` = "Particular", `Data` = prazo interno, fatal no `Texto` com `DJEN#id`).
- `python FINANCEIRO/main.py notion --dias 7 [--gravar]`: cobrança emitida e pagamento do Asaas viram linha em
  Transações Financeiras (`ASAAS#id` no `Texto`); possível duplicata de lançamento manual é pulada.
- Base: `INTEGRACOES/notion_escritorio.py` (só cria; só altera linha que ele mesmo criou). Testes:
  `INTEGRACOES/teste_notion_escritorio.py` e `teste_notion_rotinas.py`.

Onde o POP diz "vira tarefa no Notion", a pessoa lança em
**Prazos/Tarefas** assim:

| Campo da tarefa no POP | Coluna do banco Prazos/Tarefas |
|---|---|
| Título da linha | `Contratante` (**quem contratou**: advogado parceiro ou "Particular"; não é o nome da tarefa) |
| Descrição (`[PRAZO] ...`, fatal e interno) | `Texto` |
| Cliente final | `Cliente` |
| Prazo | `Data` |
| Responsável | `Responsável` |
| Urgência | `Prioridade` (Baixa/Média/Alta) |
| Tribunal | `Tribunal` |
| Situação | `Status` (`PRAZO`, `Não iniciada`, `Em andamento`, `Revisar`, `Assinar`, `Concluído`) |
| Etapa | `Fluxo RT` (`PRAZO`, `INICIAL`, `CÁLCULO`, `ANÁLISE PREV`, `LIQUIDAÇÃO`, `REVISÃO`, `PETIÇÃO`, `Protocolo/Distribuição`, `FINANCEIRO`...) |

Outros bancos: perícia e audiência → **Audiências/Perícias**; demanda de cálculo (inclusive de parceiro) →
**Fluxo RT**; cadastro e situação do cliente → **Base de Dados Clientes Law Notion** (`Área` = Previdenciário,
`Status`, `Cartão`); dinheiro → **Transações Financeiras**.

## 4. Números que o kit e o sistema definem diferente (decidir)

| Item | Kit | Aqui | Em vigor nos POPs |
|---|---|---|---|
| Prazo interno do ato judicial | fatal − 2 dias úteis | `PRAZO_INTERNO_DIAS_ANTES`, padrão **3** (`CONTROLADORIA/configuracao.py`) | o do sistema (3), ajustável no `.env` |
| Prazo interno da demanda externa de cálculo | parceiro − 2 dias úteis | sem regra no código | **2**, regra do kit para o ciclo inegociável |
| Régua de cobrança | 10, 5 e 3 dias antes e no dia | D-3 e no dia; atraso D+1, D+5, D+15 | a do sistema; as MSG-07 antigas (10 e 5 dias) ficam sem uso até a Dra. Faya decidir `[CONFERIR]` |
| Feriados | 2 de julho aplicado | só nacionais + `FERIADOS_EXTRAS` no `.env` | **2 de julho não entra sozinho**: pôr `FERIADOS_EXTRAS=02/07` e conferir os municipais de Salvador |

## 5. Equipe

`config/equipe.py` coloca o **Dr. William** no comercial (qualificação, agenda e reunião de fechamento). O kit
punha a Dra. Faya e a Bárbara no lead previdenciário. **Quem atende o lead previdenciário é decisão do
escritório** `[CONFERIR]`; os POPs ATD-02 e ATD-03 foram mantidos como estavam nisso.

## 6. Jurisprudência e teses

O kit só citava a jurisprudência que já vinha nos modelos. Aqui há mais duas fontes, **sempre com `[CONFERIR]` até o
advogado abrir a fonte**:
- **Jurisprudências.ai** (`INTEGRACOES/jurisprudencias_ia.py`; `buscar`, `decisao`; chave só no `config/.env`): pesquisa de
  decisões. Ainda não está ligada ao `JUDICIAL`; hoje se consulta à parte.
- **Banco de teses** (`banco_teses/`, no OneDrive, fora do git): teses dos cálculos e das petições do escritório.

A base de leis do kit (`leis/`) segue valendo para artigo de lei: puxar de lá, não de memória.

