# Documento Chave da campanha (Aula 1 da Fazedoria)

Escritório: Faya Barreiros Sociedade Individual de Advocacia, Salvador/BA, atendimento online para todo o Brasil.
Criado em 18/11/2026. **Rascunho**: tudo que não veio de documento do escritório está como `[A CONFIRMAR]`.
Regra do curso: não inventar. As frases de cliente precisam vir de conversas reais (WhatsApp, transcrições), não da IA.

> Meta e token: a integração atual é só leitura (`INTEGRACOES/meta_ads_integration.py`). Nada neste documento
> sobe anúncio, mexe em verba ou usa token.

## Limites da OAB (valem para os dois DCs)
Provimento 205/2021: informar e explicar direitos pode. Não pode: prometer ou sugerir resultado, usar honorário
ou "grátis" como chamariz, captação ostensiva, afirmar a situação de quem vê o anúncio.
Troca típica: em vez de "garantimos sua revisão", "veja quais direitos a lei prevê para quem teve o benefício negado".
Quem responde pela publicidade é a advogada responsável; toda peça de anúncio passa pela Dra. Faya antes de ir ao ar.

---

## Como este documento foi preenchido
Fonte: `banco_teses/` (323 peças reais anonimizadas: 170 de aposentadoria por idade/carência e 108 de liquidação
de sentença previdenciária no banco de cálculos). Tudo marcado **[HIPÓTESE]** foi deduzido dessas peças e do que
o escritório faz, NÃO de falas de cliente. **[FALTA]** é o que só conversa real fornece. Nenhuma frase de cliente
foi inventada.

## DC 1: Previdenciário, planejamento e cálculo de aposentadoria (Dra. Faya)

1. **Oferta em uma frase** [HIPÓTESE, escolhida pelo maior volume do banco]: "Descubra, com cálculo de tempo de
   contribuição e carência, se você já tem direito a se aposentar e qual regra de transição vale para o seu caso."
2. **Cliente**: pessoa física, segurado do INSS perto da aposentadoria ou com dúvida sobre carência/tempo.
   Faixa etária, renda e localização [FALTA].
3. **Dores** [HIPÓTESE]: não saber se já pode se aposentar; confusão entre as regras (EC 103/2019, regras de
   transição); períodos sem contribuição e medo de ter perdido a qualidade de segurado; CNIS com lacunas; INSS
   que indefere ou concede valor menor que o esperado.
4. **Desejos** [HIPÓTESE]: saber a data certa e a regra mais vantajosa; ter um número (tempo, carência, RMI)
   explicado de forma clara; segurança antes de pedir o benefício.
5. **Objeções e respostas** [HIPÓTESE]:
   - "Posso fazer sozinho no Meu INSS." Resposta: o INSS aplica a regra que encontra; o cálculo compara regras e
     aponta pendências antes do pedido.
   - "Tenho medo de custar caro." Resposta: apresentar o valor do cálculo de forma clara, sem usar "grátis" (OAB). Valor [FALTA, Dra. Faya].
   - "Atendimento online não é confiável." Resposta: escritório com endereço físico em Salvador (Av. Tancredo Neves, 1283), reunião por vídeo.
6. **Palavras do cliente**: [FALTA]. Fontes a minerar: conversas de WhatsApp de leads e transcrições
   (`COMERCIAL/main.py transcrever`). Meta do curso: 10 frases literais.
7. **Decisão**: o próprio segurado decide, em geral rápido se a dor for atual [HIPÓTESE; confirmar com Dra. Faya].
8. **Quatro filtros** [HIPÓTESE]: dor atual, sim (aposentadoria próxima); decide sozinho, sim; honorário cabe,
   [FALTA preço]; escala, sim (cálculo padronizado, 133 relatórios no banco).
9. **Limites da OAB**: não afirmar "você tem direito"; falar em "verifique se pode ter direito".
10. **Ganchos** (3 s) [HIPÓTESE, para a Dra. Faya revisar]:
   - "Você sabe qual regra de aposentadoria vale para você?"
   - "Ficou anos sem contribuir? Isso pode não atrapalhar sua aposentadoria por idade."
   - "Já tem 15 anos de contribuição? Veja o que mais falta."

## DC 2: Cálculos avulsos, liquidação de sentença previdenciária (Dra. Faya)

1. **Oferta em uma frase** [HIPÓTESE, 2º maior volume do banco]: "Cálculo de liquidação de sentença previdenciária
   (correção, juros e SELIC da EC 113/2021), pronto para instruir o cumprimento de sentença."
2. **Cliente** [HIPÓTESE]: principalmente advogados e escritórios que ganharam a ação mas não têm quem calcule
   (B2B); em segundo lugar, o segurado com sentença favorável. Confirmar com a Dra. Faya qual é o público principal.
   Para advogados o canal e a linguagem são outros, e o Provimento 205 se aplica do mesmo jeito.
3. **Dores** [HIPÓTESE]: prazo apertado para executar; cálculo contestado pela Fazenda; dúvida sobre índice de
   correção e juros em cada período; falta de equipe de cálculo.
4. **Desejos** [HIPÓTESE]: cálculo conferível, com memória detalhada, entregue no prazo.
5. **Objeções e respostas** [HIPÓTESE]: "Faço eu mesmo na planilha." Resposta: exibir a memória por etapas e a
   conformidade com os temas do STJ/STF; "demora." Resposta: prazo de entrega [FALTA, ciclo dos prazos].
6. **Palavras do cliente**: [FALTA]. Fonte: mensagens de advogados parceiros.
7. **Decisão**: o advogado decide sozinho e rápido quando há prazo [HIPÓTESE].
8. **Quatro filtros** [HIPÓTESE]: dor atual, sim; decide sozinho, sim; preço [FALTA]; escala, depende da
   capacidade de entrega (o ciclo dos prazos é inegociável, então limitar a verba ao que a Dra. Faya consegue entregar).
9. **Limites da OAB**: publicidade entre advogados também segue o Provimento 205; sem prometer resultado.
10. **Ganchos** [HIPÓTESE]:
   - "Ganhou a ação e agora precisa liquidar? Veja o que o cálculo precisa trazer."
   - "Qual índice usar na liquidação depois da EC 113?"

---

## Antes de passar para a Aula 2
- [ ] Dra. Faya revisar todas as [HIPÓTESE] e responder os [FALTA] (preço, prazo de entrega, público do DC 2).
- [ ] Escolher uma das áreas para começar (o curso recomenda um DC por vez, uma oferta por campanha).
- [ ] Reunir 10+ frases reais de clientes de cada DC.
- [ ] Decidir quem faz SDR (qualifica) e quem fecha. Hoje: William fecha o tributário; Faya fecha o previdenciário.
- [ ] Definir se a escrita na Meta será ligada (exige token novo com `ads_management`, que só você gera). Pendente.
