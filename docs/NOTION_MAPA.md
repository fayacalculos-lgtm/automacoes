# Mapa do Notion do escritorio

Gerado em 23/10/2026 pela integracao `AUTOMACOES` (workspace "Advocacia Faya Barreiros").
Lido pela API: 786 paginas e 33 bancos. So estrutura aqui; nenhum dado de cliente.
Uso: `INTEGRACOES/notion_integration.py` (`consultar_banco(id)`, `criar_pagina`, `atualizar_pagina`).

## Bancos que o sistema deve usar (os "vivos", com mais itens)

| Banco | ID | Itens | Para que serve no sistema |
|---|---|---|---|
| **Base de Dados Clientes Law Notion** | `51d7b6d5-dac6-829d-9b39-010518728754` | 148 | Cadastro/funil do cliente. Substitui o funil local do COMERCIAL e a pasta do cliente da CONTRATACAO |
| **Transacoes Financeiras** | `d647b6d5-dac6-83df-aaa5-01049cba9dda` | 201 | Honorarios e despesas. Alimenta/confere FINANCEIRO (Asaas) |
| **Prazos/Tarefas** | `40e7b6d5-dac6-839a-b006-01b423a08d5a` | 81 | Prazos e tarefas. Destino da CONTROLADORIA e da CONTRATACAO no lugar do ADVBOX |
| **Fluxo RT** | `5d37b6d5-dac6-83c6-ad8f-014a5ae8fbf2` | 172 | Fila de calculos (demandas externas da Dra. Faya) |
| **Audiencias/Pericias** | `36c7b6d5-dac6-8173-956d-c2f69f150da5` | 10 | Audiencias e pericias |
| Honorarios Projetados | `f7b7b6d5-dac6-8366-9b4d-0122976a5c9f` | 2 | Previsao de recebimento (relacao com Clientes) |
| Reunioes Agendadas | `baa7b6d5-dac6-83e0-ae23-8131c9cb9e6e` | 5 | Reunioes (inclui a de fechamento) |
| Base dados Comercial | `d737b6d5-dac6-832d-ba70-01cb4685ec98` | 2 | Metricas mensais de leads por canal |
| Manuais e Procedimentos Internos | `4487b6d5-dac6-834e-9049-8167bce000e2` | 11 | POPs por cargo/setor |
| Documentos | `a987b6d5-dac6-83f8-9cdc-81be83efd905` | 6 | Modelos por area |
| Teses RT | `5217b6d5-dac6-83eb-b6d8-01e464fbd934` | 3 | Teses trabalhistas |
| Planejamento de redes sociais / Projetos OCP / People / Menu | varios | 2-16 | Marketing, projetos, equipe: fora do escopo da automacao |

Existem **copias duplicadas** de varios bancos (modelos/templates antigos, com poucos itens). Usar sempre os IDs da tabela.

## Colunas (nomes exatos, com acento e espacos)

**Base de Dados Clientes Law Notion**: `Cliente ` (titulo, tem espaco no fim), `N Processo`, `Responsável`, `Telefone`,
`Área` (Previdenciário, Tributário, Cível, Penal, Trabalhista), `Produtos`, `Tribunal`, `Honorários Totais`,
`Status ` (Pendente Distribuição, Recebendo acordo, Em trâmite, Encerrado, Desistiu), `Cartão` (multi: ATENDIMENTO AGENDADO,
DEMANDAS FAYA, DOCUMENTOS PENDENTES, AGUARDANDO ASSINATURA DOCS, AÇÃO DISTRIBUÍDA/EM TRÂMITE, RECEBENDO ACORDO, PROCESSOS FINALIZADOS),
`Prospecção` (JUSBRASIL, PARTICULAR, INSTAGRAM, FACEBOOK, GOOGLE ADS, INDICAÇÃO, PARCERIA), `Prioridade` (Urgente, Quente, Frio),
`Contratante`, `Parceria`, `Cidade Ingresso`, `Agendamento`, `Mês/Ano entrada`, `SENHA GOV`, `Caixa - 12%`.

**Prazos/Tarefas**: `Contratante` (titulo), `Cliente`, `Texto`, `Data`, `Responsável`, `Prioridade` (Baixa/Média/Alta),
`Tribunal`, `Status` (PRAZO, Não iniciada, Em andamento, Revisar, Assinar, Concluído), `Fluxo RT` (FINANCEIRO, PRAZO, PENDENCIA,
REVISÃO, ADMINISTRATIVO, PLANEJAMENTO, LIQUIDAÇÃO, ANÁLISE PREV, Protocolo/Distribuição, INICIAL, CÁLCULO, PETIÇÃO).

**Transações Financeiras**: `Cliente` (titulo), `Contratante` (relacao -> Clientes), `Tipo` (Entrada/Saída), `Valor`, `Valor Total`,
`Núm`, `Parcela Atual`, `Valor Parcela` (formula), `Pago` (checkbox), `Data do pagamento`, `Recorrência` (Mensal/Única/Parcelado),
`Classificação` (Honorários, Honorários 30%, Defesa, Sucumbenciais, Despesa Cliente, Parceria, Calculista, Aluguel, Marketing...),
`Tipo de Despesa`, `Área`, `Adv Responsável`, `Serviço`, `Caixa - 12%` (formula).

**Fluxo RT**: `Cliente x Empresa` (titulo), `Fluxo RT` (PLANEJAMENTO, LIQUIDAÇÃO, ANÁLISE PREV/REVISÃO, PROTOCOLO - DISTRIBUIÇÃO, PRAZOS),
`Prioridade`, `Resposável` (sic), `Status` (Não iniciada, Em andamento, Assinar, Concluído), `Data Entrega`.

**Audiências/Perícias**: `Cliente x Parte Contrária` (titulo), `Processo`, `Evento`, `Tribunal - Cidade`, `Resposável` (sic),
`Modalidade`, `Área`, `Data e Hora`, `Status` (Não iniciada, Em andamento, Realizada, Acordo, Redesignada).

## Atencao
- **"Senhas Tamara Costa"** (2 copias) guarda login e senha em texto. O sistema **nao deve ler** esse banco.
- Nomes de coluna tem erros de grafia e espacos no fim (`Resposável`, `Cliente `, `Status `). Usar exatamente como acima.
- A integracao ve so o que foi compartilhado com ela. Banco novo => compartilhar com `AUTOMACOES`.
- Ha banco "Auditoria de Processos – Gilvania Araujo" (vazio) na raiz: teste, ignorar.
- O Notion mostra a equipe atual (Gabriela, Thais, Tamara) e contratantes (Dr. Marcelo, Dra Vivian...) de outro modelo de escritorio:
  conferir com a Dra. Faya o que ainda vale antes de gravar nesses campos `[CONFERIR]`.
