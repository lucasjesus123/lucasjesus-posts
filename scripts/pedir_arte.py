"""Pede ao GPT (via GitHub + API da OpenAI) a arte de um slide e já coloca o JPG na pasta do post.

Uso (o Diretor de Arte roda isto, um slide por vez):
  python3 scripts/pedir_arte.py --post posts/2026-10-20 --slide 01 \
      --prompt-arquivo /tmp/prompt-01.txt [--foto fotos/camisa-preta-bracos-cruzados.jpg]

O prompt é o MOLDE do estilo (estilos/estilos.json) já preenchido com textos, foto e cena.
O script cria gerar/pedidos/<post>-<slide>.json, faz push, espera o workflow "Gerar arte (GPT)"
(até 10 min), e salva <post>/<slide>.jpg em 1080x1350. Sai com código 1 se der erro.
Para refazer um slide, rode de novo: o pedido anterior é substituído.
"""
import argparse
import io
import json
import pathlib
import subprocess
import sys
import time

from PIL import Image


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True)


def ajustar(png_path, destino):
    """Corta pelo centro e redimensiona para 1080x1350 (4:5)."""
    im = Image.open(png_path).convert("RGB")
    w, h = 1080, 1350
    esc = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * esc), round(im.height * esc)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    im.crop((x, y, x + w, y + h)).save(destino, "JPEG", quality=93, optimize=True, progressive=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", required=True)
    ap.add_argument("--slide", default="01")
    ap.add_argument("--prompt-arquivo", required=True)
    ap.add_argument("--foto", action="append", default=[])
    ap.add_argument("--qualidade", default="high", choices=["low", "medium", "high"])
    ap.add_argument("--espera", type=int, default=600)
    a = ap.parse_args()

    post = pathlib.Path(a.post)
    post.mkdir(parents=True, exist_ok=True)
    prompt = pathlib.Path(a.prompt_arquivo).read_text(encoding="utf-8").strip()
    nome = f"{post.name}-{a.slide}"
    pj = pathlib.Path(f"gerar/pedidos/{nome}.json")
    pj.parent.mkdir(parents=True, exist_ok=True)
    pj.write_text(json.dumps({"prompt": prompt, "referencias": a.foto, "qualidade": a.qualidade,
                              "post": post.as_posix(), "slide": a.slide, "status": "pendente"},
                             ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    git("add", str(pj))
    git("commit", "-q", "-m", f"Pedido de arte: {nome}")
    for _ in range(5):
        git("pull", "--rebase", "-q", "origin", "main")
        if git("push", "-q", "origin", "HEAD:main").returncode == 0:
            break
        time.sleep(5)
    else:
        sys.exit("Não consegui enviar o pedido ao GitHub.")
    print(f"Pedido {nome} enviado. Esperando o GPT…")
    fim = time.time() + a.espera
    while time.time() < fim:
        time.sleep(30)
        git("pull", "--rebase", "-q", "origin", "main")
        p = json.loads(pj.read_text(encoding="utf-8"))
        if p["status"] == "erro":
            sys.exit(f"ERRO: {p.get('erro', '')[:600]}")
        if p["status"] == "pronto":
            destino = post / f"{a.slide}.jpg"
            ajustar(p["saida"], destino)
            print(f"Pronto: {destino} ({p.get('modelo')})")
            return
    sys.exit("O GPT não respondeu a tempo.")


if __name__ == "__main__":
    main()
