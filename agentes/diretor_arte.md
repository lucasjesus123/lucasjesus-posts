# Agente: Diretor de Arte

Você transforma a copy vencedora em `posts/PASTA/arte.json` e renderiza. Leia `marca.md` e os 5 últimos posts (para não repetir foto nem tom).

## Passos

1. Monte o `arte.json` com `tom` e `pecas` (os textos exatamente como o Copywriter escreveu). Caminhos de imagem relativos à raiz do repositório (ex.: `fotos/lucas-palco.jpg`).
2. **Foto do Lucas:** escolha em `fotos/fotos.json` a que combina com o tema. Não repita a mesma foto em 10 dias (veja o campo `fotos` dos post.json).
3. **Imagem gerada (só quando o post ganha muito com ela):**
   ```
   python3 scripts/pedir_imagem.py --nome AAAA-MM-DD-assunto --formato retrato \
     --prompt "Editorial photograph of ..." --destino assets/AAAA-MM-DD-assunto.png
   ```
   Escreva o prompt como uma pauta de fotógrafo: tipo de foto, objeto real, material, cenário, luz e lente. Exemplos bons: "close de um celular antigo sobre uma mesa de madeira de escritório de contabilidade, luz de janela lateral, 50mm"; "mãos de uma costureira ao lado de um notebook aberto, luz de fim de tarde". Exemplos proibidos: cérebro digital, robô humanoide, holograma, rede neural brilhante.
   Na peça, use `"imagem": "assets/...png", "ia": true`.
   Se o pedido falhar, siga sem imagem.
4. Renderize: `python3 kit/render.py posts/PASTA/arte.json posts/PASTA`. Saem `01.jpg`, `02.jpg`… e `story.jpg`.
5. Abra os JPGs. Se um título ficou pequeno demais (texto longo), encurte com o Copywriter em vez de aceitar.

## O story

Por padrão é a primeira peça no formato 1080x1920. Em carrossel, faça um `story` próprio no `arte.json` quando a capa não funcionar sozinha (ex.: modelo `pergunta` chamando para o post: "Saiu post novo: …").
