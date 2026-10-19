# Sistema visual

**Caminho principal:** a arte inteira é criada pelo GPT Image (API da OpenAI) nos estilos aprovados de `estilos/estilos.json` (ver `diretor_arte.md`).

**Plano B** (se o GPT falhar duas vezes): os modelos em código do `kit/render.py`, descritos abaixo.

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
| frase | frase dele em serifa, com aspas | frase, contexto (opcional, ex.: "pai do Kaleo") |
| manifesto | frase curta gigante, tipografia pesada | frase (até 12 palavras; use | para escolher a quebra) |
| nota | anotação do caderno dele | titulo (padrão "Anotações"), data, frase, complemento (uma linha) |
| versus | contraste em dois blocos (o de cima riscado) | rotulo_a, a, rotulo_b, b (cada lado até 10 palavras) |
| foto | foto real em tela cheia | imagem, titulo, subtitulo |
| pergunta | gerar comentário | pergunta, contexto, cta (opcional) |

### Com a foto do Lucas (a foto real dele é a estrela)

| modelo | uso | campos |
|---|---|---|
| capa | capa de revista: título enorme e ele recortado logo abaixo, com o cabelo encostando nas letras. Autoridade, capa de carrossel, opinião forte | chapeu, data, titulo (até 4 palavras por linha, no máximo 2 linhas), subtitulo, imagem |
| retrato | retrato em tela cheia (P&B por padrão) com uma frase dele embaixo | frase, contexto, imagem, lado ("direita" ou "esquerda": onde fica o rosto), tratamento ("pb" ou "natural") |
| dividido | foto em cima, ideia embaixo. Capa de "Na prática", post de autoridade | chapeu, titulo, subtitulo, imagem |
| moldura | bastidor: a foto como cópia impressa sobre o papel, com legenda de editor | titulo, legenda, imagem |
| foto | foto em tela cheia com título curto | titulo, subtitulo, imagem |
| fecho | último slide do carrossel, com o rosto dele no avatar | opiniao, cta, imagem |

Ajustes finos (qualquer modelo com foto): `zoom` (tamanho do rosto em relação ao quadro, ex.: 0.22), `alvo_y` (altura do rosto, 0 a 1), `alvo_x` (posição horizontal, 0 a 1).

Toda peça aceita `"tom": "claro" | "escuro"` (o padrão vem do `arte.json`). O modelo `foto` é sempre escuro.

`arte.json` de exemplo: veja `kit/exemplo_arte.json`.

## Imagens

- **Foto do Lucas: só as do catálogo `fotos/fotos.json`** (aprovadas por ele), e passa sozinha pelo tratamento de estúdio do `kit/foto.py`:
  correção suave de luz e balanço de branco, nitidez fina, recorte do fundo e **detecção do rosto**. O enquadramento é feito pelo rosto: ele nunca sai cortado e nenhum texto cai em cima dele.
- Só use fotos com `"qualidade": "ótima"` ou `"boa"` no catálogo. Foto `"fraca"` (pequena ou tremida) não entra em arte.
- **Imagem gerada (GPT):** só como ingrediente (objeto, mesa de trabalho, cenário, textura). Marque `"ia": true` na peça: o render aplica duotone em tinta e giz e um grão fino, e a imagem passa a parecer foto de revista, não arte de IA. Nunca gere o rosto do Lucas.
- Sem imagem também funciona: a tipografia é a arte. Prefira sem imagem a uma imagem genérica.
