# Squad do @lucasjesus.oficial

Um post por dia, todos os dias, publicado às **18h** (horário de Brasília) no feed e no story. Ninguém aprova: o squad cria, revisa e agenda sozinho. Por isso a régua de verdade e de qualidade é alta.

O orquestrador (a rotina diária do Claude) lê todos os arquivos desta pasta, dispara os agentes com a ferramenta Agent (cada um recebe o texto do seu arquivo e o contexto), junta as respostas e decide.

| Agente | Arquivo | Responde |
|---|---|---|
| Estrategista | estrategista.md | Qual é o post de hoje e para que ele serve? |
| Pesquisador | pesquisador.md | Qual fato real, recente e com fonte sustenta o post? |
| Copywriter | copywriter.md | Como o Lucas diria isso, de um jeito que faça parar de rolar? |
| Diretor de Arte | diretor_arte.md | Como isso vira arte no sistema visual da marca? |
| Revisor | revisor.md | Está verdadeiro, bonito e sem cara de IA? |
| Analista | analista.md | O que funcionou nas últimas semanas? (lido no passo 1) |

Leia também: `voz.md` (como o Lucas fala), `calendario.md` (o que sai em cada dia), `marca.md` (o sistema visual).

## Fluxo

0. **Fotos novas.** Se houver arquivos em `fotos/novas/` (fora o LEIA-ME), catalogue cada um:
   - abra a foto, descreva o que se vê (lugar, roupa, momento, expressão, enquadramento), dê um nome curto em kebab-case e mova com `git mv` para `fotos/`;
   - rode `python3 kit/foto.py fotos/NOME.jpg` e copie para o catálogo a `qualidade` e a `deteccao`;
   - registre em `fotos/fotos.json`: arquivo, descricao, contexto, qualidade, modelos_indicados (ex.: retrato P&B para foto pensativa; capa e dividido para foto de corpo inteiro ou meio corpo; moldura e foto para palco e bastidor).
   Nunca invente onde ou quando a foto foi tirada: se não der para saber, escreva "contexto: não informado". Foto com marca d'água de outro app ou que pareça gerada por IA não entra: anote `"qualidade": "recusada"` e o motivo.
1. **Contexto.** Leia o calendário do dia, `pautas/ideias.md` (ideias que o Lucas deixou: têm prioridade sobre o calendário quando couberem no dia), o radar mais recente em `radar/`, `metricas/ultimas.json` se existir, e os `post.json` dos 10 últimos posts.
2. **Estrategista** → briefing.
3. **Pesquisador** → fatos com fonte (pula nos dias de frase e pergunta, a não ser que o briefing cite um dado).
4. **Copywriter** → 3 propostas. O orquestrador dá nota de 0 a 5 em: para o dedo, clareza em 1 segundo, soa como o Lucas, utilidade para quem lê, verdade. Fica com a maior soma; empate vence a que soa mais como o Lucas.
5. **Diretor de Arte** → `arte.json` + imagens; renderiza com `python3 kit/render.py posts/PASTA/arte.json posts/PASTA`.
6. **Revisor** (agente NOVO, que não viu a produção) abre TODOS os JPGs e a legenda. Corrija e revise de novo (no máximo 2 rodadas). Se ainda reprovar, troque por um post de frase, que é o mais seguro.
7. **Agendar** e conferir pendências (ver o prompt da rotina).

## Regras de ouro

- **Uma ideia por post.**
- **Nada inventado.** Número, lançamento, preço e citação só com fonte verificada. Nenhuma história pessoal do Lucas que não esteja em `voz.md`, `pautas/ideias.md` ou na descrição de uma foto.
- **Sem cara de IA.** Ver `marca.md` e a lista do revisor. Na dúvida, menos efeito e mais tipografia.
- **A notícia sempre vira utilidade.** Todo post de IA responde: "e o que isso muda para quem tem empresa?".
- **Nunca política partidária, nunca polêmica religiosa.** Fé aparece como valor e propósito, sem pregar.
