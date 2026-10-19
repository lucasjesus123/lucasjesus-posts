"""Pede ao GPT (via GitHub) um ingrediente de imagem e espera o resultado.

Uso (o Diretor de Arte roda isto):
  python3 scripts/pedir_imagem.py --nome 2026-10-20-chip --prompt "close de um chip sobre uma mesa de madeira..." \
      [--ref fotos/lucas_palco.jpg] [--formato retrato|paisagem|quadrado] [--destino assets/chip.png]

Cria gerar/pedidos/NOME.json, faz push, o workflow "Gerar imagem (GPT)" gera com OPENAI_API_KEY,
e o script puxa gerar/saida/NOME.png (até 10 min). Sai com código 1 se der erro.
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import time


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nome", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--ref", action="append", default=[])
    ap.add_argument("--formato", default="retrato", choices=["retrato", "paisagem", "quadrado"])
    ap.add_argument("--destino", default="")
    ap.add_argument("--espera", type=int, default=600)
    a = ap.parse_args()

    pj = pathlib.Path(f"gerar/pedidos/{a.nome}.json")
    pj.parent.mkdir(parents=True, exist_ok=True)
    pj.write_text(json.dumps({"prompt": a.prompt, "referencias": a.ref, "formato": a.formato, "status": "pendente"},
                             ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    git("add", str(pj))
    git("commit", "-q", "-m", f"Pedido de imagem: {a.nome}")
    for _ in range(5):
        git("pull", "--rebase", "-q", "origin", "main")
        if git("push", "-q", "origin", "HEAD:main").returncode == 0:
            break
        time.sleep(5)
    else:
        sys.exit("Não consegui enviar o pedido ao GitHub.")
    print("Pedido enviado. Esperando o GPT…")
    fim = time.time() + a.espera
    while time.time() < fim:
        time.sleep(30)
        git("pull", "--rebase", "-q", "origin", "main")
        p = json.loads(pj.read_text(encoding="utf-8"))
        if p["status"] == "erro":
            sys.exit(f"ERRO: {p.get('erro', '')[:600]}")
        if p["status"] == "pronto":
            saida = pathlib.Path(p["saida"])
            if a.destino:
                pathlib.Path(a.destino).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(saida, a.destino)
                saida = pathlib.Path(a.destino)
            print(f"Pronto: {saida} ({p.get('modelo')})")
            return
    sys.exit("O GPT não respondeu a tempo.")


if __name__ == "__main__":
    main()
