# POP-OP-02 — Controladoria: intimações, prazos do INSS e do Judiciário

Versão 1 — 18/11/2026

| | |
|---|---|
| **Dono do POP** | Dra. Faya |
| **Quem executa** | Bárbara (agenda de prazos); estagiário(a) (pushs processuais e baixa de decisões); Dra. Faya confirma a classificação de decisão, sentença e laudo |
| **Gatilho** | Todo dia útil, 8h (publicações do DJEN, pushs do PJe, Meu INSS, e-mail) |
| **Termina quando** | Toda intimação do dia classificada, com prazo e tarefa no Notion e o cliente avisado quando for o caso |
| **Prazo** | Leitura até 9h30; tarefas criadas até 12h |

## Objetivo

Nenhum prazo perdido — nem do processo judicial, nem das **demandas externas de cálculo**, cujo ciclo de prazos a
Dra. Faya declarou **inegociável**. Em previdenciário há três fontes de prazo, e as três entram aqui.

## As três fontes

| Fonte | Onde aparece | Exemplos |
|---|---|---|
| **Judicial** | DJEN (OAB/BA 64.723 e OAB/SP 308.385), pushs do PJe (TRF1 / JEF da Seção Judiciária da Bahia; Justiça Estadual nas acidentárias) | Perícia designada, laudo juntado, sentença, cálculo do INSS para impugnar, RPV expedida |
| **Administrativa (INSS)** | Meu INSS do cliente, carta pelos Correios | Carta de exigência, indeferimento, cessação, convocação para perícia, decisão da Junta de Recursos |
| **Demandas externas de cálculo** | E-mail/WhatsApp do advogado parceiro | Prazo que o parceiro tem no processo dele (POP-PREV-06) |

## O que a automação faz e o que a pessoa faz

| A automação faz (`CONTROLADORIA/`) | A pessoa faz |
|---|---|
| `python CONTROLADORIA/main.py varredura --dias 1` lê o DJEN pelas OABs e a Tramitação Inteligente, classifica cada publicação e calcula prazo fatal e interno (só relatório; nada sai) | Confere se não sobrou publicação sem classificação |
| Com `--criar-tarefas`, cria a atividade/prazo **na Tramitação**, item a item, **pedindo confirmação** | Confirma responsável e data de cada item |
| `python CONTROLADORIA/main.py avisos-cliente` gera o aviso e um CSV para revisar (só envia com `--enviar`) | Revisa e libera (decisão, sentença e laudo: Dra. Faya antes) |
| `python CONTROLADORIA/prazos_administrativos.py 30` lê o e-mail e propõe a data preliminar de exigência/recurso do INSS (só leitura; não cria tarefa nem responde) | Confere na carta e lança |
| Relatório do dia na pasta `SAIDA/` | Lê e fecha o dia |

O INSS e as demandas externas **não** chegam pelo DJEN: o prazo do INSS por e-mail sai, preliminar, no `prazos_administrativos.py`; a carta pelos Correios e a demanda externa a Bárbara lança à mão no Notion, no mesmo dia em que chegam.

## Classificação e prazo — previdenciário

| O que chegou | Prazo | Quem |
|---|---|---|
| **Carta de exigência do INSS** | O prazo da própria carta (em regra 30 dias) `[CONFERIR na carta]` | Bárbara pede o documento ao cliente (MSG-02); Dra. Faya responde |
| **Indeferimento ou cessação** | Recurso à Junta de Recursos (CRPS): **30 dias** da ciência | Dra. Faya decide: recurso (POP-PREV-03), novo pedido ou ação (POP-PREV-04) |
| **Perícia médica ou social designada** (INSS ou judicial) | Data da perícia | Avisar o cliente (MSG-03); quesitos e assistente técnico, se houver prazo aberto |
| **Laudo pericial juntado** | Manifestação: prazo do despacho (no JEF costuma ser 5 a 10 dias) `[CONFERIR no despacho]` | Dra. Faya |
| **Sentença no JEF** | Recurso inominado: **10 dias úteis** (Lei 9.099/95, arts. 42 e 12-A, c/c Lei 10.259/2001, art. 1º); embargos de declaração: **5 dias** | Dra. Faya |
| **Acórdão da Turma Recursal** | Pedido de uniformização (Lei 10.259/2001, art. 14) e recurso extraordinário: **15 dias** `[CONFERIR regimento da TNU/TRU]` | Dra. Faya |
| **Sentença na Vara Federal / Estadual** | Apelação: **15 dias úteis** (CPC, arts. 1.003, § 5º, e 219); embargos: 5 dias úteis | Dra. Faya |
| **Decisão interlocutória (Vara)** | Agravo de instrumento: 15 dias úteis, se no rol do art. 1.015 do CPC | Dra. Faya |
| **Cálculo do INSS / contadoria para manifestar** | Prazo do despacho | Dra. Faya confere com o cálculo do escritório (POP-PREV-07) |
| **RPV/precatório expedido ou pago** | Sem prazo processual; aviso ao cliente e cobrança dos honorários | POP-PREV-07 |
| **Mero andamento** (conclusão, remessa, juntada) | Sem prazo | Só registra |

Na dúvida sobre a classificação: **tratar como prazo** e pedir a confirmação da Dra. Faya no mesmo dia.

## Como contar

1. Judicial: **dias úteis** (CPC, art. 219; no JEF, Lei 9.099/95, art. 12-A). Exclui o dia do começo, inclui o do vencimento (CPC, art. 224).
2. DJEN: publicação no 1º dia útil seguinte à disponibilização; o prazo começa no 1º dia útil seguinte à publicação (CPC, art. 224, §§ 2º e 3º).
3. Intimação pelo sistema: no dia da consulta; sem consulta, 10 dias corridos após o envio (Lei 11.419/2006, art. 5º, § 3º).
4. **O INSS tem prazo em dobro** (CPC, art. 183); **o segurado não**. No JEF não há prazo diferenciado para a Fazenda (Lei 10.259/2001, art. 9º).
5. Recesso de 20/12 a 20/01 suspende os prazos judiciais (CPC, art. 220). **Não suspende** prazo administrativo do INSS.
6. Feriados: o sistema aplica só os **nacionais** e o que estiver em `FERIADOS_EXTRAS` no `config/.env` (`DD/MM`, separados por vírgula). **O 2 de julho (Independência da Bahia) e os feriados municipais de Salvador não entram sozinhos** `[CONFERIR no calendário do TRF1/Justiça Federal e do TJBA e preencher FERIADOS_EXTRAS]`.
7. Registrar **o prazo fatal e o prazo interno**. O interno do sistema é o fatal menos **3 dias úteis** (`PRAZO_INTERNO_DIAS_ANTES` no `.env`); o kit original usava 2. Vale o do `.env`.

## O que vira tarefa no Notion

> Lançar no banco **Prazos/Tarefas** do Notion conforme `ADAPTACAO.md` §3 (título em `Texto`, prazo em `Data`, etapa em `Fluxo RT`). Hoje o lançamento é manual: nenhum módulo grava no Notion.

| Tarefa | Responsável | Prazo |
|---|---|---|
| `[PRAZO] {{peça}} - {{cliente}} - {{processo}}` | Dra. Faya | Prazo interno (fatal anotado) |
| `[EXIGÊNCIA INSS] {{cliente}} - NB {{nb}}` | Dra. Faya | Prazo da carta menos 5 dias úteis |
| `[PERÍCIA] {{cliente}} - {{data}}` | Bárbara avisa o cliente | 5 dias úteis antes da perícia |
| `[CÁLCULO EXTERNO] {{parceiro}} - {{caso}}` | Dra. Faya | Prazo do parceiro menos 2 dias úteis |
| `[AVISAR CLIENTE] {{assunto}}` | Bárbara | 1 dia útil |

## Onde salva

- Ato processual e carta do INSS: `CLIENTES FAYA/01 - EM ANDAMENTO/<CLIENTE>/10 PREVIDENCIARIO/AAAA-MM-DD_{{tipo}}.pdf` (ver `ADAPTACAO.md` §2)
- Relatório do dia: pasta `SAIDA/` do sistema

## Pendências

- A Tramitação Inteligente **já entrega** os andamentos (API integrada em 23/10/2026): a Controladoria lê as movimentações de cada processo ativo e o DJEN confere. `[CONFERIR]` se todos os processos previdenciários já estão cadastrados lá.
- `[A CONFIRMAR]` Quantos processos ativos e em quais tribunais (TRF1, TJBA, TRF3 pela OAB/SP).
