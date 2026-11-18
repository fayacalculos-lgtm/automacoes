# MSG-07 — Lembretes de cobrança financeira (honorários)

Versão 1 — 16/11/2026 · Usado no Módulo 2 (financeiro) e no POP-ATD-03, passo 5

## Como funciona

- As cobranças ficam registradas no **Asaas** (boletos no DDA do cliente, link de pagamento com boleto e Pix).
- Os lembretes saem pelo WhatsApp do escritório, **uma mensagem em cada data**. A régua que o sistema roda (`config/regras_financeiras.py`, `python FINANCEIRO/main.py cobranca`) é **3 dias antes e no dia**; os modelos 1 e 2 (10 e 5 dias antes) **ficam sem uso** até a Dra. Faya decidir `[CONFERIR]`.
- Pagou antes: os lembretes seguintes são cancelados e vai o modelo 6.
- Cliente que exige **nota fiscal antes do pagamento**: a nota sai junto com o lembrete de 10 dias (modelo 1-NF).
- Após o vencimento o sistema cobra em **D+1, D+5 e D+15**. O modelo 7 serve ao D+1; o modelo 8 foi escrito para D+7, então o D+5 e o D+15 ainda não têm texto aqui `[CONFERIR: dias e tom com a Dra. Faya]`.

## Variáveis

| Variável | O que é |
|---|---|
| `{{nome_cliente}}` | Primeiro nome do responsável financeiro |
| `{{nome_escritorio}}` | Nome comercial `[A CONFIRMAR]` |
| `{{referencia}}` | Ex.: "honorários iniciais", "parcela 3 de 10 dos honorários de êxito" |
| `{{valor}}` | Valor |
| `{{vencimento}}` | Data de vencimento |
| `{{link_pagamento}}` | Link do Asaas (boleto e Pix) |
| `{{link_nota}}` | Link da nota fiscal, quando houver |

---

## Modelo 1 — 10 dias antes

> {{nome_cliente}}, tudo bem? Passando para lembrar que os {{referencia}}, no valor de R$ {{valor}}, vencem em {{vencimento}}.
>
> Para sua comodidade, segue o link de pagamento (boleto ou Pix): {{link_pagamento}}
>
>

**1-NF — cliente que recebe a nota antes do pagamento**: acrescentar
> A nota fiscal correspondente está disponível aqui: {{link_nota}}

## Modelo 2 — 5 dias antes

> {{nome_cliente}}, lembrete: os {{referencia}} (R$ {{valor}}) vencem em {{vencimento}}. Link de pagamento: {{link_pagamento}}

## Modelo 3 — 3 dias antes

> {{nome_cliente}}, faltam 3 dias para o vencimento dos {{referencia}} (R$ {{valor}}), em {{vencimento}}. Link: {{link_pagamento}}

## Modelo 4 — No dia do vencimento

> {{nome_cliente}}, bom dia! Hoje vencem os {{referencia}} (R$ {{valor}}). Se já estiver programado, desconsidere esta mensagem. Link para pagamento: {{link_pagamento}}

## Modelo 5 — E-mail (opcional, junto com o lembrete de 10 dias)

Assunto: `{{referencia}} — vencimento em {{vencimento}}`
> Prezado(a) {{nome_cliente}},
>
> Lembramos que os {{referencia}}, no valor de R$ {{valor}}, vencem em {{vencimento}}.
>
> Link para pagamento (boleto ou Pix): {{link_pagamento}}
>
> Atenciosamente,
> {{nome_escritorio}}

## Modelo 6 — Pagamento recebido

> {{nome_cliente}}, recebemos o pagamento dos {{referencia}}. Obrigado! [Se a nota sai após o pagamento: "A nota fiscal está aqui: {{link_nota}}"]

## Modelo 7 — 1 dia após o vencimento, sem pagamento `[A CONFIRMAR]`

> {{nome_cliente}}, não identificamos ainda o pagamento dos {{referencia}} (R$ {{valor}}), vencidos em {{vencimento}}. Se já pagou, pode desconsiderar. Caso contrário, segue o link atualizado: {{link_pagamento}}

## Modelo 8 — 7 dias após o vencimento `[A CONFIRMAR]`

> {{nome_cliente}}, os {{referencia}} (R$ {{valor}}) seguem em aberto desde {{vencimento}}. Podemos ajudar com alguma coisa? Link para pagamento: {{link_pagamento}}

Depois do modelo 8, a Dra. Faya decide o contato pessoal. Cliente previdenciário nunca recebe cobrança em tom de ameaça.
