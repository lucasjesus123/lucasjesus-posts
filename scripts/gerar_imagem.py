"""Gera as ARTES dos posts com a API oficial da OpenAI (GPT Image). Roda no GitHub Actions.

Cada pedido é um arquivo gerar/pedidos/NOME.json, criado pelo scripts/pedir_arte.py:
  {
    "prompt": "prompt completo (o molde do estilo em estilos/estilos.json, já preenchido)",
    "referencias": ["fotos/camisa-preta-bracos-cruzados.jpg"],   # foto do Lucas (opcional)
    "status": "pendente"
  }
A arte sai em gerar/saida/NOME.png e o pedido vira "pronto" (ou "erro", com a mensagem da OpenAI).
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
# Instagram 4:5. Modelos novos aceitam múltiplos de 16; se recusar, cai para o retrato clássico.
TAMANHOS = ["1088x1360", "1024x1536"]


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
    ultimo = None
    for modelo in MODELOS:
        for tam in TAMANHOS:
            try:
                args = dict(model=modelo, prompt=pedido["prompt"], size=tam,
                            quality=pedido.get("qualidade", "high"), n=1)
                if imagens:
                    r = client.images.edit(image=[open(f, "rb") for f in imagens], **args)
                else:
                    r = client.images.generate(**args)
                return modelo, base64.b64decode(r.data[0].b64_json)
            except Exception as e:
                ultimo = e
                txt = str(e).lower()
                if "size" in txt and tam != TAMANHOS[-1]:
                    continue
                if "model" in txt and any(k in txt for k in ("not found", "does not exist", "invalid", "access")):
                    print(f"Modelo {modelo} indisponível: {str(e)[:200]}")
                    break
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
