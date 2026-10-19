"""Monta o story (1080x1920) a partir da arte do feed, sem gastar outra geração no GPT.

A arte 4:5 fica no centro (dentro da área segura: fora dos 14% do topo e dos 20% da base),
sobre um fundo feito da própria arte, ampliada, desfocada e escurecida.

Uso: python3 scripts/story.py posts/2026-10-20/01.jpg posts/2026-10-20/story.jpg
"""
import sys

from PIL import Image, ImageEnhance, ImageFilter


def montar(origem, destino):
    arte = Image.open(origem).convert("RGB")
    W, H = 1080, 1920
    fundo = arte.resize((round(arte.width * H / arte.height), H), Image.LANCZOS)
    x = (fundo.width - W) // 2
    fundo = fundo.crop((x, 0, x + W, H)).filter(ImageFilter.GaussianBlur(40))
    fundo = ImageEnhance.Brightness(fundo).enhance(0.45)
    # a arte ocupa a faixa segura: de 14% a 80% da altura
    alto = int(H * 0.80) - int(H * 0.14) - 40
    larg = min(W - 80, int(alto * arte.width / arte.height))
    alto = int(larg * arte.height / arte.width)
    peca = arte.resize((larg, alto), Image.LANCZOS)
    y = int(H * 0.14) + (int(H * 0.80) - int(H * 0.14) - alto) // 2
    sombra = Image.new("RGBA", (larg + 60, alto + 60), (0, 0, 0, 0))
    sombra.paste((0, 0, 0, 140), (30, 30, larg + 30, alto + 30))
    sombra = sombra.filter(ImageFilter.GaussianBlur(24))
    fundo = fundo.convert("RGBA")
    fundo.alpha_composite(sombra, ((W - larg) // 2 - 30, y - 10))
    fundo.paste(peca, ((W - larg) // 2, y))
    fundo.convert("RGB").save(destino, "JPEG", quality=90, optimize=True)


if __name__ == "__main__":
    montar(sys.argv[1], sys.argv[2])
