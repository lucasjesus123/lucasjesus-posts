"""Tratamento das fotos reais do Lucas: a foto dele precisa sair perfeita em toda arte.

O que faz (uma vez por foto; o resultado fica em cache em assets/cache/):
  1. recorte: tira o fundo com rembg (modelo isnet-general-use) e limpa a borda;
  2. cabeça: acha a cabeça pela silhueta (o topo da pessoa), para enquadrar sem cortar o rosto
     e nunca colocar texto em cima dele;
  3. tratamento de estúdio: exposição e balanço de branco corrigidos com suavidade, contraste local
     leve, nitidez fina; nada de filtro "de aplicativo", a pele continua pele;
  4. qualidade: mede resolução e nitidez do rosto e dá a nota ótima / boa / fraca.

Uso direto (o squad usa ao catalogar uma foto nova):
  python3 kit/foto.py fotos/lucas-palco.jpg     -> imprime a ficha (cabeça, qualidade) em JSON
"""
import hashlib
import json
import pathlib
import sys

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CACHE = RAIZ / "assets" / "cache"
_SESSAO = None


def _sessao():
    global _SESSAO
    if _SESSAO is None:
        from rembg import new_session
        _SESSAO = new_session("isnet-general-use")
    return _SESSAO


def _chave(caminho):
    p = pathlib.Path(caminho)
    return f"{p.stem}-{hashlib.md5(p.read_bytes()).hexdigest()[:8]}"


def estudio(img):
    """Correção de estúdio: sutil de propósito."""
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    # balanço de branco: puxa 35% em direção ao cinza médio (corrige dominante sem matar a cor de pele)
    medias = a.reshape(-1, 3).mean(0)
    ganho = 1 + 0.35 * (medias.mean() / np.maximum(medias, 1) - 1)
    a = a * ganho
    # exposição: leva o meio-tom da imagem para perto de 118 (de 255), sem estourar
    lum = a.mean(2)
    p50 = np.percentile(lum, 50)
    gama = np.clip(np.log(118 / 255) / np.log(max(p50, 1) / 255), 0.8, 1.25)
    a = 255 * (np.clip(a, 0, 255) / 255) ** gama
    # pontos de preto e branco suaves
    lo, hi = np.percentile(a, 0.4), np.percentile(a, 99.6)
    a = (a - lo) * (255 / max(hi - lo, 1))
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    # contraste local leve (clareza) + nitidez fina
    img = img.filter(ImageFilter.UnsharpMask(radius=24, percent=18, threshold=2))
    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=55, threshold=3))
    return img


def _cabeca(alfa):
    """Caixa da cabeça a partir da máscara: topo da silhueta até ~13% da altura da pessoa."""
    m = np.asarray(alfa) > 128
    linhas = np.where(m.any(1))[0]
    colunas = np.where(m.any(0))[0]
    if len(linhas) == 0:
        return None, None
    topo, base = linhas[0], linhas[-1]
    pessoa = [int(colunas[0]), int(topo), int(colunas[-1]), int(base)]
    alt = base - topo
    fim = topo + max(int(alt * 0.16), 20)
    faixa = m[topo:fim]
    xs = np.where(faixa.any(0))[0]
    # a cabeça é o bloco contínuo mais largo perto do centro de massa da faixa
    cx = int(np.average(np.arange(m.shape[1]), weights=faixa.sum(0) + 1e-6))
    larg = xs[-1] - xs[0] if len(xs) else alt * 0.2
    larg = min(larg, alt * 0.32)
    cab = [int(cx - larg / 2), int(topo), int(cx + larg / 2), int(fim)]
    return cab, pessoa


def _rosto(img, alfa):
    """Detecta o rosto (frontal ou de perfil) dentro da silhueta. Devolve a caixa da cabeça
    (rosto + cabelo) ou None."""
    try:
        import cv2
    except ImportError:
        return None
    modelos = pathlib.Path(__file__).resolve().parent / "modelos"
    f = 900 / max(img.size)
    peq = img.resize((round(img.width * f), round(img.height * f)))
    g = cv2.equalizeHist(np.asarray(ImageOps.grayscale(peq)))
    m = np.asarray(alfa.resize(peq.size)) > 128
    achados = []
    for nome, espelhar in (("haarcascade_frontalface_alt2.xml", False), ("haarcascade_profileface.xml", False),
                           ("haarcascade_profileface.xml", True)):
        cc = cv2.CascadeClassifier(str(modelos / nome))
        if cc.empty():
            continue
        alvo = g[:, ::-1].copy() if espelhar else g
        for (x, y, w, h) in cc.detectMultiScale(alvo, scaleFactor=1.08, minNeighbors=6, minSize=(40, 40)):
            if espelhar:
                x = g.shape[1] - x - w
            cx, cy = x + w // 2, y + h // 2
            if m[min(cy, m.shape[0] - 1), min(cx, m.shape[1] - 1)]:
                achados.append((w * h, x, y, w, h))
    if not achados:
        return None
    _, x, y, w, h = max(achados)
    # rosto -> cabeça: sobe para pegar o cabelo, alarga um pouco
    x0, y0, x1, y1 = x - w * .12, y - h * .38, x + w * 1.12, y + h * 1.08
    return [int(v / f) for v in (x0, max(y0, 0), x1, y1)]


def _nitidez(img, caixa):
    g = np.asarray(ImageOps.grayscale(img.crop(caixa)).resize((256, 256))).astype(np.float32)
    lap = g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    return float(lap.var())


def preparar(caminho):
    """Devolve a ficha da foto com os caminhos do tratamento (gera na primeira vez)."""
    caminho = pathlib.Path(caminho)
    if not caminho.is_absolute():
        caminho = (pathlib.Path.cwd() / caminho) if (pathlib.Path.cwd() / caminho).exists() else RAIZ / caminho
    chave = _chave(caminho)
    pasta = CACHE / chave
    ficha_arq = pasta / "ficha.json"
    if ficha_arq.exists():
        return json.loads(ficha_arq.read_text(encoding="utf-8"))
    pasta.mkdir(parents=True, exist_ok=True)
    img = ImageOps.exif_transpose(Image.open(caminho)).convert("RGB")
    # trabalha em no máximo 2400 px no lado maior
    if max(img.size) > 2400:
        f = 2400 / max(img.size)
        img = img.resize((round(img.width * f), round(img.height * f)), Image.LANCZOS)
    tratada = estudio(img)
    tratada.save(pasta / "tratada.jpg", quality=94)

    from rembg import remove
    rec = remove(tratada, session=_sessao(), post_process_mask=True)
    alfa = rec.split()[-1]
    # borda: fecha furos pequenos e suaviza 1 px (sem halo)
    alfa = alfa.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    rec.putalpha(alfa)
    rec.save(pasta / "recorte.png")

    cab, pessoa = _cabeca(alfa)
    rosto = _rosto(tratada, alfa)
    deteccao = "rosto" if rosto else "silhueta"
    if rosto:
        cab = rosto
    nit = _nitidez(tratada, cab) if cab else 0
    menor = min(img.size)
    altura_cabeca = (cab[3] - cab[1]) if cab else 0
    if menor >= 1400 and nit > 60:
        qualidade = "ótima"
    elif menor >= 1000 and nit > 25:
        qualidade = "boa"
    else:
        qualidade = "fraca"
    ficha = {
        "origem": str(caminho.relative_to(RAIZ)) if caminho.is_relative_to(RAIZ) else str(caminho),
        "tamanho": list(img.size), "cabeca": cab, "pessoa": pessoa,
        "altura_cabeca_px": altura_cabeca, "deteccao": deteccao, "nitidez_rosto": round(nit, 1), "qualidade": qualidade,
        "tratada": str((pasta / "tratada.jpg").relative_to(RAIZ)),
        "recorte": str((pasta / "recorte.png").relative_to(RAIZ)),
    }
    ficha_arq.write_text(json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
    return ficha


def enquadrar(ficha, w, h, alvo_y=0.30, cabeca_frac=0.20, pb=False, alvo_x=0.5):
    """Corta a foto tratada no tamanho exato w x h com a cabeça no lugar certo:
    centralizada na horizontal e com o meio da cabeça em alvo_y da altura.
    cabeca_frac = altura da cabeça em relação à altura do quadro (define o zoom)."""
    img = Image.open(RAIZ / ficha["tratada"]).convert("RGB")
    cab = ficha.get("cabeca") or [img.width * .4, img.height * .1, img.width * .6, img.height * .3]
    ch = max(cab[3] - cab[1], 1)
    esc = max(cabeca_frac * h / ch, w / img.width, h / img.height)
    img = img.resize((round(img.width * esc), round(img.height * esc)), Image.LANCZOS)
    cx = (cab[0] + cab[2]) / 2 * esc
    cy = (cab[1] + cab[3]) / 2 * esc
    x = int(np.clip(cx - alvo_x * w, 0, img.width - w))
    y = int(np.clip(cy - alvo_y * h, 0, img.height - h))
    out = img.crop((x, y, x + w, y + h))
    if pb:
        out = ImageOps.grayscale(out)
        out = ImageOps.autocontrast(out, cutoff=0.5)
        out = ImageEnhance.Contrast(out).enhance(1.08).convert("RGB")
    return out


def recorte_posicionado(ficha, w, h, cabeca_y=0.30, cabeca_frac=0.17, cx=0.5):
    """Recorte (PNG com transparência) num quadro w x h, com a cabeça centrada em (cx, cabeca_y)."""
    rec = Image.open(RAIZ / ficha["recorte"]).convert("RGBA")
    cab = ficha.get("cabeca")
    ch = max(cab[3] - cab[1], 1)
    esc = cabeca_frac * h / ch
    rec = rec.resize((round(rec.width * esc), round(rec.height * esc)), Image.LANCZOS)
    hx = (cab[0] + cab[2]) / 2 * esc
    hy = (cab[1] + cab[3]) / 2 * esc
    quadro = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    quadro.paste(rec, (int(cx * w - hx), int(cabeca_y * h - hy)), rec)
    return quadro


if __name__ == "__main__":
    for arq in sys.argv[1:]:
        print(json.dumps(preparar(arq), ensure_ascii=False, indent=2))
