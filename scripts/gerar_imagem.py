"""Gera INGREDIENTES de imagem com a API oficial da OpenAI (GPT Image), sem texto nenhum.

Regra da marca: a IA nunca faz a peça inteira. Ela gera um objeto, uma textura ou um cenário;
o texto e a composição são feitos pelo kit/render.py, e a imagem recebe tratamento (duotone ou P&B).

Cada pedido é um arquivo gerar/pedidos/NOME.json:
  {
    "prompt": "foto editorial de ... (sem texto)",
    "referencias": ["fotos/lucas_palco.jpg"],   # opcional: caminhos do repositório ou URLs
    "formato": "retrato",                         # retrato (1024x1536), paisagem (1536x1024) ou quadrado
    "status": "pendente"
  }
A imagem sai em gerar/saida/NOME.png e o pedido vira "pronto" (ou "erro", com a mensagem da OpenAI).
Segredo: OPENAI_API_KEY. Modelo: variável OPENAI_IMAGE_MODEL ou o primeiro da lista que a conta aceitar.
"""
import base64
import json
import os
import pathlib
import sys
import urllib.request

from openai import OpenAI

MODELOS = [m for m in [os.environ.get("OPENAI_IMAGE_MODEL", "").strip()] if m] + [
    "gpt-image-2", "gpt-image-1.5", "gpt-image-1",
]
SAIDA = pathlib.Path("gerar/saida")
CACHE = pathlib.Path("gerar/cache")
TAMANHOS = {"retrato": "1024x1536", "paisagem": "1536x1024", "quadrado": "1024x1024"}

# Vai no fim de todo prompt: é o que separa uma foto crível de "arte de IA".
ANTI_IA = (" Shot as a real editorial photograph: natural imperfect light, real materials, subtle film grain, "
           "true-to-life colors, shallow depth of field where it makes sense. "
           "Absolutely no text, letters, numbers, logos, watermarks or UI. "
           "Avoid: glowing brains, neon purple or cyan glow, holograms, circuit-board patterns, generic humanoid robots, "
           "floating particles, lens-flare spam, plastic skin, extra fingers, symmetrical stock-photo poses, sci-fi clichés.")


def baixar(ref):
    if not str(ref).startswith("http"):
        return pathlib.Path(ref)
    destino = CACHE / ref.rsplit("/", 1)[-1].split("?")[0]
    if not destino.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(ref, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            destino.write_bytes(r.read())
    return destino


def gerar(client, pedido):
    imagens = [baixar(r) for r in pedido.get("referencias", [])][:8]
    tam = TAMANHOS.get(pedido.get("formato", "retrato"), "1024x1536")
    prompt = pedido["prompt"].strip() + ANTI_IA
    ultimo = None
    for modelo in MODELOS:
        try:
            args = dict(model=modelo, prompt=prompt, size=tam, quality=pedido.get("qualidade", "high"), n=1)
            if imagens:
                r = client.images.edit(image=[open(f, "rb") for f in imagens], **args)
            else:
                r = client.images.generate(**args)
            return modelo, base64.b64decode(r.data[0].b64_json)
        except Exception as e:
            ultimo = e
            txt = str(e).lower()
            if "model" in txt and any(k in txt for k in ("not found", "does not exist", "invalid", "access")):
                print(f"Modelo {modelo} indisponível: {str(e)[:200]}")
                continue
            raise
    raise ultimo


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("Falta o segredo OPENAI_API_KEY no repositório.")
    client = OpenAI()
    SAIDA.mkdir(parents=True, exist_ok=True)
    erros = 0
    for pj in sorted(pathlib.Path("gerar/pedidos").glob("*.json")):
        pedido = json.loads(pj.read_text(encoding="utf-8"))
        if pedido.get("status") != "pendente":
            continue
        try:
            modelo, png = gerar(client, pedido)
            (SAIDA / f"{pj.stem}.png").write_bytes(png)
            pedido.update(status="pronto", modelo=modelo, saida=f"gerar/saida/{pj.stem}.png")
            pedido.pop("erro", None)
            print(f"{pj.stem}: pronto com {modelo}")
        except Exception as e:
            erros += 1
            pedido.update(status="erro", erro=str(e)[:1500])
            print(f"{pj.stem}: ERRO {e}")
        pj.write_text(json.dumps(pedido, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()
