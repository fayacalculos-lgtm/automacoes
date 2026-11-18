---
description: Rotina diária dos pedidos de cálculo por e-mail (faya.calculos@gmail.com) - prepara, avisa a Dra. Faya e envia o que ela aprovou
---

Você roda sozinho, todo dia, pelo Agendador do Windows (`deploy/rotina_calculos.bat`). Ninguém está olhando a tela:
não faça perguntas, não espere resposta, e termine com o relatório do passo 4. Trabalhe na pasta do sistema.

## Regras que não mudam
- **Nada vai ao advogado parceiro sem o OK da Dra. Faya.** O único envio é o `aprovacoes` (passo 1), que só manda o
  rascunho que ela aprovou respondendo "OK". Nunca envie e-mail por outro caminho.
- **O número oficial do cálculo é o do software dela.** Você prepara tudo em volta (leitura dos documentos, critérios
  do título, tabela de apoio, relatório, resposta) e marca `[CONFERIR: valor do software]` onde entra o número.
- Nada inventado: dado que não está no documento fica `[CONFERIR: ...]`. Cite página/arquivo de onde tirou cada dado.
- Senha, login do Meu INSS ou dado bancário que aparecer no e-mail **não** vai para arquivo nenhum que você escrever.
- Dado de cliente fica só na pasta do pedido (OneDrive). Nunca no repositório.

## 1. Enviar o que ela já aprovou
`python CALCULOS/main.py aprovacoes` → JSON com `enviados`. Para cada enviado com `valor`:
lance no artefato FINANCEIRO (https://claude.ai/artifact/TLTNLuxv8MAJrQUy86fa4M) com a ferramenta `ArtifactData`:
leia `lanc/<AAAA-MM do mês atual>` (`get`), acrescente em `itens` uma chave nova `c<ID do pedido>` com
`{tipo:"Entrada", data:"<hoje AAAA-MM-DD>", valor, cliente:"<caso>", contratante:"<parceiro>", servico, pago:false,
origem:"rotina-calculos", criado_em:"<hoje>"}` e grave o documento inteiro com `set` e `if_version` (nunca apague nem
altere item que já existe; se a chave já existir, não lance de novo). Sem `valor`: não lance; diga no relatório.
Se a ferramenta `ArtifactData` não estiver disponível nesta execução, só registre no relatório o que falta lançar.

## 2. Buscar pedidos novos
`python CALCULOS/main.py novos --dias 3` → JSON com `novos` (cada um com `id`, `pasta`, `anexos`). Os anexos e o
`pedido.json` (remetente, assunto, corpo) estão em `<pasta>/01_RECEBIDO/`.

## 3. Para cada pedido novo
1. Leia o `pedido.json` e **todos** os anexos (PDF com a ferramenta Read, por páginas).
2. Decida: é um pedido de cálculo/serviço com documentos para fazer (liquidação, atualização, RMI, revisão, honorários
   de sucumbência, valor da causa, análise/planejamento previdenciário, emenda com cálculo)?
   - Não é (agradecimento, "acuso recebimento", contrato de parceria, dados bancários, conversa sem pedido):
     `python CALCULOS/main.py ignorar <ID> --motivo "<em poucas palavras>"` e siga.
3. Sendo pedido, escreva em `<pasta>/02_PREPARADO/`:
   - `pre_analise.md`: o que foi pedido; **prazo do parceiro** (do assunto ou do texto; "PRAZO DIA dd/mm") e o prazo
     interno (2 dias úteis antes); documentos recebidos e o que cada um traz (com página); o que o título judicial
     manda (índice de correção, juros, termo inicial e final, honorários); dados do segurado e do benefício; o que falta.
     Aposentadoria/planejamento/análise: monte o `caso.json` no formato de `KIT_PREVIDENCIARIO/calculos/README.md`
     com os períodos do CNIS e rode `python KIT_PREVIDENCIARIO/calculos/simular.py caso.json -o simulacao.md` (apoio).
   - O relatório no timbrado: escolha o modelo em `python KIT_PREVIDENCIARIO/pecas/gerar_peca.py listar`
     (ex.: `parecer-liquidacao`, `analise-previdenciaria`, `conferencia-rmi-auxilio`), preencha com os dados dos
     documentos seguindo `KIT_PREVIDENCIARIO/dna/DNA_PECAS.md`, salve a minuta `.md` em `<pasta>/03_INTERNO/` e gere
     o `.docx` com `gerar_peca.py docx <minuta> --saida <pasta>/02_PREPARADO/<NOME>.docx`. Artigo de lei: confira em `KIT_PREVIDENCIARIO/leis/buscar_lei.py`.
   - `resposta_parceiro.md`: só o corpo do e-mail ao parceiro, no tom dela: "Bom Dia Dra, tudo bem ? Segue
     <o que vai em anexo>. Fico à disposição para esclarecimentos." Cordial e curto; sem prometer resultado.
     Se faltar documento essencial, a resposta pede esse documento (e o anexo pode nem existir).
   - `resumo.md` (para ela, direto): pedido, parceiro, **prazo**, o que você preparou, o que ELA precisa fazer antes do
     OK (rodar no software e lançar o valor, conferir pontos), e as pendências.
   - Só deixe em `02_PREPARADO/` o que deve ir anexado ao parceiro, além dos dois `.md` acima (a `pre_analise.md`
     e a `simulacao.md` são para ela: guarde-as em `<pasta>/03_INTERNO/`).
4. `python CALCULOS/main.py preparar <ID> --servico "<tipo>"` (acrescente `--valor N` só se o valor combinado
   estiver escrito no e-mail). Isso cria o rascunho na conversa do parceiro e manda o resumo para ela.

## 4. Relatório final (é o que fica no log)
Em poucas linhas: quantos enviados (e lançados no FINANCEIRO), quantos preparados (parceiro, assunto, prazo),
quantos ignorados (e por quê), quantos aguardando o OK, e qualquer erro com a mensagem exata.
