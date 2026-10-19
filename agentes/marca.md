# Sistema visual (kit/render.py)

A arte é feita em código, não por gerador de imagem. É isso que tira a "cara de IA": tipografia de verdade, grid fixo, paleta própria e fotos reais.

## Paleta (só estas cores)

| Nome | Hex | Uso |
|---|---|---|
| Papel | #E6EAE8 | fundo claro |
| Tinta | #0F1E3A | fundo escuro e texto no claro |
| Latão | #C08A2B | o fio da assinatura e marcas estruturais (cor do sax) |
| Grafite | #26292E | apoio |
| Giz | #FBFCFB | texto no escuro |

Nada de neon, roxo, ciano brilhante, gradiente colorido, brilho ou "glow".

## Tipografia

- **Bricolage Grotesque** estreita e pesada: títulos (o tamanho se ajusta sozinho para preencher o espaço).
- **Newsreader**: textos, frases e citações.

## Modelos e campos

| modelo | uso | campos |
|---|---|---|
| manchete | notícia (post único ou capa) | chapeu (padrão "Radar de IA"), data ("20 de outubro de 2026"), titulo, subtitulo, fonte ("Fonte: OpenAI, 17/10/2026"), imagem (opcional, ocupa a metade de cima) |
| slide | miolo de carrossel | titulo, texto, imagem (opcional) |
| lista | passos ou itens | titulo, itens [[título, explicação]...] (3 a 5), sequencia (true se for passo a passo) |
| fecho | último slide | opiniao, cta (opcional), imagem (foto do Lucas, vira o avatar) |
| frase | frase dele | frase, contexto (opcional, ex.: "na palestra em Lajeado") |
| foto | foto real em tela cheia | imagem, titulo, subtitulo |
| pergunta | gerar comentário | pergunta, contexto, cta (opcional) |

Toda peça aceita `"tom": "claro" | "escuro"` (o padrão vem do `arte.json`). O modelo `foto` é sempre escuro.

`arte.json` de exemplo: veja `kit/exemplo_arte.json`.

## Imagens

- **Foto do Lucas: sempre real**, de `fotos/fotos.json`. `"tratamento": "natural"` (padrão) ou `"pb"`.
- **Imagem gerada (GPT):** só como ingrediente (objeto, mesa de trabalho, cenário, textura). Marque `"ia": true` na peça: o render aplica duotone em tinta e giz e um grão fino, e a imagem passa a parecer foto de revista, não arte de IA. Nunca gere o rosto do Lucas.
- Sem imagem também funciona: a tipografia é a arte. Prefira sem imagem a uma imagem genérica.
