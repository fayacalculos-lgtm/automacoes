# POP-PREV-06 — Demandas externas de cálculo e serviços avulsos (para outros advogados)

Versão 1 — 18/11/2026

| | |
|---|---|
| **Dono do POP** | Dra. Faya |
| **Quem executa** | Bárbara (entrada, prazo, cobrança); agente `calculista` (pré-apuração e conferência); Dra. Faya (cálculo e entrega) |
| **Gatilho** | Advogado parceiro pede cálculo, parecer ou serviço avulso (e-mail, WhatsApp, indicação) |
| **Termina quando** | Cálculo entregue ao parceiro **antes do prazo dele**, pago, e arquivado |
| **Prazo** | O prazo processual do parceiro menos 2 dias úteis (nunca no último dia) |

## Por que este POP existe

No briefing, a Dra. Faya declarou **inegociável o ciclo dos prazos das demandas externas de cálculos e serviços
avulsos**. Aqui o cliente é outro advogado, e o prazo é o do processo dele: atraso nosso vira prazo perdido dele.

## Ferramenta: o banco Fluxo RT do Notion

Aqui **não há painel nem link de pedido** para o parceiro. A fila das demandas é o banco **Fluxo RT** do Notion
(`Cliente x Empresa`, `Fluxo RT`, `Prioridade`, `Resposável` [sic], `Status`, `Data Entrega`; ver `docs/NOTION_MAPA.md`). A
entrada é por e-mail ou WhatsApp. Painel com semáforo, ranking de parceiros e link de pedido, se um dia for
desejado, é módulo novo a construir.

## Passo a passo

1. **Entrada** — a Bárbara lança a demanda no **Fluxo RT** (ou `criar_demanda_calculo` de `INTEGRACOES/notion_escritorio.py`): parceiro, caso, tipo, **prazo processual do parceiro** (em `Data Entrega`)
   e valor combinado no `Cliente x Empresa`/observação. — *no mesmo dia*
2. **Pasta** separada dos clientes do escritório, com o que o parceiro enviou: `ADVOCACIA/CALCULOS 2026/<CASO>` ou
   `ADVOCACIA/PARCEIROS/<PARCEIRO>`, como o escritório já faz `[CONFERIR qual]`. — *mesmo dia*
3. **Prazo**: prazo interno = prazo do parceiro menos **2 dias úteis** (nunca o último dia). Pedido **sem prazo**: perguntar
   antes de aceitar. Os dias úteis seguem `CONTROLADORIA/prazos.py` (lembrar de `FERIADOS_EXTRAS`). — *mesmo dia*
4. **Conferir os documentos** em até 1 dia útil: sentença/acórdão (os critérios de correção e juros vêm do título),
   CNIS, carta de concessão, cálculo da parte contrária. Faltou: pedir ao parceiro **no mesmo dia** (o relógio é dele).
5. **Cálculo** no software, conferido pelo agente `calculista` contra o título judicial e contra
   `KIT_PREVIDENCIARIO/calculos/FORMATO_DOS_CALCULOS.md`. — *até o prazo interno*
6. **Entrega**: PDF do cálculo + nota técnica curta (critérios usados, divergência com o cálculo adversário). — *prazo interno*
7. **Status "Concluído"** no Fluxo RT, na data da entrega. — *na entrega*
8. **Cobrança**: lançar em **Transações Financeiras** (`Classificação`, `Pago`) e cobrar pelo Asaas conforme o combinado;
   marcar `Pago` quando pagar. — *na entrega*

## Regras

- Os critérios de correção e juros são **os do título** (sentença/acórdão), não os do nosso gosto. Se o título é
  omisso, a nota técnica diz qual critério foi usado e por quê.
- Demanda sem prazo informado pelo parceiro: perguntar antes de aceitar.
- Dado do cliente do parceiro tem o mesmo cuidado de LGPD que o nosso.

## Pendências

- `[A CONFIRMAR]` Tabela de preços por tipo de cálculo e se há contrato padrão com o parceiro (hoje não há modelo).
- `[A CONFIRMAR]` Qual software de cálculo o escritório usa (o formato dos relatórios está descrito em
  `KIT_PREVIDENCIARIO/calculos/FORMATO_DOS_CALCULOS.md`).
