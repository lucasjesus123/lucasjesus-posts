"""Renderiza as artes do @lucasjesus.oficial a partir de um JSON (HTML/CSS -> PNG/JPG com Chromium).

Uso:
  python3 kit/render.py posts/AAAA-MM-DD/arte.json posts/AAAA-MM-DD

arte.json:
{
  "tom": "claro" | "escuro",
  "pecas": [                       # 1 peça = post único; 2 a 10 = carrossel
    {"modelo": "manchete", ...},
    {"modelo": "slide", ...},
    {"modelo": "fecho", ...}
  ],
  "story": {"modelo": "manchete", ...}   # opcional; se faltar, usa a primeira peça
}

Saída na pasta: 01.jpg, 02.jpg... (1080x1350) e story.jpg (1080x1920).

Marcação de texto: "|" quebra a linha. Nada mais: o sistema não destaca palavra solta.

Identidade (não mude sem falar com o Lucas):
  papel #E6EAE8, tinta #0F1E3A, latão #C08A2B, grafite #26292E, giz #FBFCFB
  Bricolage Grotesque (títulos, estreita e pesada) + Newsreader (texto e frases)
"""
import base64
import html
import io
import json
import pathlib
import sys

from PIL import Image, ImageEnhance, ImageOps

KIT = pathlib.Path(__file__).resolve().parent
FONTES = KIT / "fonts"

COR = {"papel": "#E6EAE8", "tinta": "#0F1E3A", "latao": "#C08A2B", "grafite": "#26292E", "giz": "#FBFCFB",
       "tinta2": "#1A2B4D"}


def fonte_css():
    def src(arq):
        return "data:font/woff2;base64," + base64.b64encode((FONTES / arq).read_bytes()).decode()
    return f"""
@font-face{{font-family:Bric;src:url({src('bricolage.woff2')}) format('woff2');font-weight:200 800;font-stretch:75% 100%;}}
@font-face{{font-family:Bric;src:url({src('bricolage-ext.woff2')}) format('woff2');font-weight:200 800;font-stretch:75% 100%;unicode-range:U+0100-02BA,U+1E00-1EFF;}}
@font-face{{font-family:News;src:url({src('newsreader.woff2')}) format('woff2');font-weight:200 800;font-style:normal;}}
@font-face{{font-family:News;src:url({src('newsreader-ext.woff2')}) format('woff2');font-weight:200 800;font-style:normal;unicode-range:U+0100-02BA,U+1E00-1EFF;}}
@font-face{{font-family:News;src:url({src('newsreader-italic.woff2')}) format('woff2');font-weight:200 800;font-style:italic;}}
@font-face{{font-family:News;src:url({src('newsreader-italic-ext.woff2')}) format('woff2');font-weight:200 800;font-style:italic;unicode-range:U+0100-02BA,U+1E00-1EFF;}}
"""


# ---------- imagens ----------

def tratar(caminho, tratamento, largura=1080):
    """Devolve data URI da imagem tratada.
    natural: foto real, só um ajuste leve de contraste.
    pb: preto e branco com grão (padrão para fotos geradas por IA).
    duotone: sombras em tinta, luzes em giz (padrão para ingredientes gerados por IA)."""
    img = Image.open(caminho)
    img = ImageOps.exif_transpose(img).convert("RGB")
    if img.width > largura * 1.5:
        img = img.resize((int(largura * 1.5), int(img.height * largura * 1.5 / img.width)), Image.LANCZOS)
    if tratamento == "pb":
        img = ImageOps.grayscale(img)
        img = ImageOps.autocontrast(img, cutoff=1)
        img = ImageEnhance.Contrast(img).enhance(1.12).convert("RGB")
    elif tratamento == "duotone":
        g = ImageOps.autocontrast(ImageOps.grayscale(img), cutoff=1)
        img = ImageOps.colorize(g, black=COR["tinta"], white=COR["giz"], mid="#7E8A9E")
    else:
        img = ImageEnhance.Contrast(img).enhance(1.05)
        img = ImageEnhance.Color(img).enhance(0.92)
    if tratamento in ("pb", "duotone"):
        # grão fino: tira o acabamento "plástico" das imagens geradas
        import random
        ruido = Image.effect_noise(img.size, 18).convert("L")
        img = Image.blend(img, Image.merge("RGB", (ruido, ruido, ruido)), 0.06)
        random.seed(1)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def img_url(peca, base):
    caminho = peca.get("imagem")
    if not caminho:
        return None
    p = pathlib.Path(caminho)
    if not p.is_absolute():
        p = (base / p) if (base / p).exists() else pathlib.Path.cwd() / p
    trat = peca.get("tratamento") or ("duotone" if peca.get("ia") else "natural")
    return tratar(p, trat)


# ---------- texto ----------

def t(s):
    """Escapa e transforma | em quebra de linha."""
    return "<br>".join(html.escape(p.strip()) for p in str(s or "").split("|"))


def tam_titulo(texto, base, minimo):
    """Diminui o corpo conforme o comprimento do título."""
    n = len(str(texto).replace("|", ""))
    if n <= 18:
        return base
    return max(minimo, int(base * (18 / n) ** 0.55))


# ---------- modelos ----------
# Cada função devolve o miolo HTML; a moldura (fundo, assinatura) é comum.

def m_manchete(p, img, story):
    """Notícia de IA. Capa de carrossel ou post único."""
    titulo = p.get("titulo", "")
    corpo = tam_titulo(titulo, 150 if not story else 160, 76)
    foto = f'<div class="mfoto" style="background-image:url({img})"></div>' if img else ""
    return f"""
<div class="manchete {'com-foto' if img else 'sem-foto'}">
  {foto}
  <div class="mtopo"><span class="marca">{t(p.get('chapeu') or 'Radar de IA')}</span><span>{t(p.get('data', ''))}</span></div>
  <div class="mtexto">
    <h1 data-fit="{(560 if not img else 400) if story else (470 if not img else 330)}" data-max="230">{t(titulo)}</h1>
    <p class="linha-fina">{t(p.get('subtitulo', ''))}</p>
    <p class="fonte">{t(p.get('fonte', ''))}</p>
  </div>
</div>"""


def m_slide(p, img, story):
    """Miolo de carrossel: uma ideia por slide."""
    pos = f'<span class="pos">{p.get("slide", "")}/{p.get("total", "")}</span>' if p.get("slide") else ""
    foto = f'<div class="sfoto" style="background-image:url({img})"></div>' if img else ""
    corpo = tam_titulo(p.get("titulo", ""), 92, 58)
    return f"""
<div class="slide">
  <div class="stopo">{pos}</div>
  {foto}
  <h2 data-fit="{420 if not img else 220}" data-max="190">{t(p.get('titulo', ''))}</h2>
  <p class="stexto">{t(p.get('texto', ''))}</p>
</div>"""


def m_fecho(p, img, story):
    """Último slide: a opinião do Lucas + o que fazer agora."""
    avatar = f'<div class="avatar" style="background-image:url({img})"></div>' if img else ""
    return f"""
<div class="fecho">
  <p class="fopiniao">{t(p.get('opiniao', ''))}</p>
  <div class="fautor">{avatar}<div><b>Lucas Jesus</b><span>{t(p.get('cargo') or 'Desenvolvo ferramentas de IA para negócios')}</span></div></div>
  <p class="fcta">{t(p.get('cta') or 'Salva este post e manda para quem precisa ler.')}</p>
</div>"""


def m_frase(p, img, story):
    """Frase dele. Sem foto: a tipografia é a arte."""
    frase = p.get("frase", "")
    n = len(frase.replace("|", ""))
    corpo = 104 if n < 60 else 88 if n < 100 else 72 if n < 150 else 60
    if story:
        corpo = int(corpo * 1.08)
    return f"""
<div class="frase">
  <span class="aspas">“</span>
  <blockquote style="font-size:{corpo}px">{t(frase)}</blockquote>
  <p class="assin">Lucas Jesus{(' — ' + t(p.get('contexto'))) if p.get('contexto') else ''}</p>
</div>"""


def m_foto(p, img, story):
    """Foto real dele em tela cheia, com título curto."""
    corpo = tam_titulo(p.get("titulo", ""), 118, 64)
    return f"""
<div class="foto" style="background-image:url({img or ''})">
  <div class="fgrad"></div>
  <div class="ftexto">
    <h1 data-fit="{420 if story else 360}" data-max="170">{t(p.get('titulo', ''))}</h1>
    <p>{t(p.get('subtitulo', ''))}</p>
  </div>
</div>"""


def m_pergunta(p, img, story):
    """Pergunta para gerar comentário."""
    corpo = tam_titulo(p.get("pergunta", ""), 120, 70)
    return f"""
<div class="pergunta">
  <h1 data-fit="{640 if story else 520}" data-max="200">{t(p.get('pergunta', ''))}</h1>
  <p class="pcontexto">{t(p.get('contexto', ''))}</p>
  <p class="pcta">{t(p.get('cta') or 'Me responde nos comentários.')}</p>
</div>"""


def m_lista(p, img, story):
    """Passos ou itens (ferramenta, prompt, método). Numera só se for sequência."""
    itens = p.get("itens", [])
    seq = p.get("sequencia", True)
    lis = "".join(
        f'<li>{"<i>" + str(i + 1) + "</i>" if seq else "<i>–</i>"}<div><b>{t(a)}</b><span>{t(b)}</span></div></li>'
        for i, (a, b) in enumerate(itens))
    return f"""
<div class="lista">
  <h2>{t(p.get('titulo', ''))}</h2>
  <ul>{lis}</ul>
</div>"""


MODELOS = {"manchete": m_manchete, "slide": m_slide, "fecho": m_fecho, "frase": m_frase,
           "foto": m_foto, "pergunta": m_pergunta, "lista": m_lista}


CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:var(--h);overflow:hidden}
body{font-family:News,serif;-webkit-font-smoothing:antialiased;text-rendering:geometricPrecision}
.quadro{position:relative;width:1080px;height:var(--h);background:var(--fundo);color:var(--texto);overflow:hidden;
  padding:var(--topo) 84px var(--base) 84px;display:flex;flex-direction:column}
.claro{--fundo:#E6EAE8;--texto:#0F1E3A;--suave:#4B5568;--linha:#0F1E3A}
.escuro{--fundo:#0F1E3A;--texto:#FBFCFB;--suave:#AEB8C9;--linha:#FBFCFB}
.miolo{flex:1;display:flex;flex-direction:column;min-height:0}
h1,h2{font-family:Bric,sans-serif;font-stretch:75%;font-weight:700;line-height:.92;letter-spacing:-.015em;text-wrap:balance}
p{text-wrap:pretty}
/* assinatura: o nome dele é a marca */
.assinatura{position:absolute;left:84px;right:84px;bottom:calc(var(--base) - 70px);display:flex;justify-content:space-between;
  align-items:baseline;font-family:Bric,sans-serif;font-size:25px;font-weight:500;color:var(--suave)}
.assinatura b{font-weight:700;color:var(--texto);font-stretch:85%;font-size:28px;letter-spacing:.01em}
.assinatura .fio{flex:1;height:2px;background:#C08A2B;margin:0 22px;align-self:center;opacity:.9}

/* manchete */
.manchete{flex:1;display:flex;flex-direction:column}
.mtopo{display:flex;justify-content:space-between;font-family:Bric,sans-serif;font-size:28px;font-weight:500;color:var(--suave);
  padding-bottom:22px;border-bottom:3px solid #C08A2B}
.mtopo .marca{color:var(--texto);font-weight:700}
.mtexto{margin-top:auto;padding-bottom:40px}
.manchete h1{margin-bottom:34px;line-height:.9}
.linha-fina{font-size:42px;line-height:1.24;max-width:860px;color:var(--texto);font-weight:400}
.fonte{margin-top:30px;font-family:Bric,sans-serif;font-size:25px;color:var(--suave)}
.fonte:empty,.linha-fina:empty{display:none}
.manchete.com-foto .mfoto{position:absolute;left:0;right:0;top:0;height:48%;background-size:cover;background-position:center}
.manchete.com-foto .mfoto::after{content:'';position:absolute;inset:0;background:linear-gradient(to bottom,rgba(15,30,58,.78) 0,rgba(15,30,58,0) 22%,rgba(15,30,58,0) 70%,var(--fundo) 100%)}
.manchete.com-foto .mtopo{position:relative;z-index:2;color:#FBFCFB;border-color:#C08A2B;text-shadow:0 1px 14px rgba(15,30,58,.95)}
.manchete.com-foto .mtopo .marca{color:#FBFCFB}
.manchete.com-foto .mtexto{position:relative;z-index:2}

/* slide */
.slide{flex:1;display:flex;flex-direction:column}
.stopo{display:flex;justify-content:flex-end;font-family:Bric,sans-serif;font-size:30px;font-weight:600;color:#C08A2B;min-height:40px}
.sfoto{height:420px;margin:30px 0 50px;background-size:cover;background-position:center}
.slide h2{margin-top:auto;margin-bottom:36px}
.stexto{font-size:44px;line-height:1.3;max-width:880px;margin-bottom:60px}

/* fecho */
.fecho{flex:1;display:flex;flex-direction:column;justify-content:center}
.fopiniao{font-size:60px;line-height:1.16;font-style:italic;font-weight:400;max-width:900px;margin-bottom:64px}
.fautor{display:flex;align-items:center;gap:28px;padding:30px 0;border-top:3px solid #C08A2B;border-bottom:1px solid var(--suave)}
.avatar{width:120px;height:120px;border-radius:50%;background-size:cover;background-position:center 20%;flex:none}
.fautor b{display:block;font-family:Bric,sans-serif;font-stretch:80%;font-size:46px;font-weight:700;line-height:1}
.fautor span{display:block;font-size:30px;color:var(--suave);margin-top:8px}
.fcta{margin-top:56px;font-family:Bric,sans-serif;font-size:40px;font-weight:600;line-height:1.15}

/* frase */
.frase{flex:1;display:flex;flex-direction:column;justify-content:center}
.aspas{font-family:News,serif;font-size:300px;line-height:.6;color:#C08A2B;height:140px;font-weight:300}
.frase blockquote{font-weight:420;line-height:1.12;letter-spacing:-.01em;max-width:910px;text-wrap:balance}
.assin{margin-top:56px;font-family:Bric,sans-serif;font-size:32px;font-weight:600;color:var(--suave)}

/* foto */
.quadro.tem-foto{padding:0}
.foto{position:absolute;inset:0;background-size:cover;background-position:center top}
.fgrad{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(15,30,58,0) 38%,rgba(15,30,58,.86) 70%,#0F1E3A 100%)}
.ftexto{position:absolute;left:84px;right:84px;bottom:calc(var(--base) + 30px);color:#FBFCFB}
.ftexto h1{margin-bottom:26px}
.ftexto p{font-size:40px;line-height:1.25;max-width:860px}
.quadro.tem-foto .assinatura{color:#C9D0DC}.quadro.tem-foto .assinatura b{color:#FBFCFB}

/* pergunta */
.pergunta{flex:1;display:flex;flex-direction:column;justify-content:center}
.pergunta h1{margin-bottom:44px}
.pcontexto{font-size:42px;line-height:1.28;max-width:860px;color:var(--suave)}
.pcta{margin-top:60px;font-family:Bric,sans-serif;font-size:36px;font-weight:600;padding-top:26px;border-top:3px solid #C08A2B;align-self:flex-start}

/* lista */
.lista{flex:1;display:flex;flex-direction:column;justify-content:center}
.lista h2{font-size:96px;margin-bottom:50px}
.lista ul{list-style:none}
.lista li{display:flex;gap:30px;padding:28px 0;border-top:1px solid color-mix(in srgb,var(--texto) 30%,transparent)}
.lista li:last-child{border-bottom:1px solid color-mix(in srgb,var(--texto) 30%,transparent)}
.lista li i{font-style:normal;font-family:Bric,sans-serif;font-weight:700;font-size:48px;color:#C08A2B;width:44px;flex:none;line-height:1}
.lista li b{display:block;font-family:Bric,sans-serif;font-stretch:85%;font-size:44px;font-weight:700;line-height:1.05;margin-bottom:8px}
.lista li span{display:block;font-size:34px;line-height:1.28;color:var(--suave)}
"""


FIT_JS = """() => { for (const el of document.querySelectorAll('[data-fit]')) {
  const alt = +el.dataset.fit, max = +el.dataset.max || 200; let lo = 40, hi = max;
  while (hi - lo > 1) { const m = (lo + hi) >> 1; el.style.fontSize = m + 'px';
    if (el.scrollHeight <= alt && el.scrollWidth <= el.clientWidth + 1) lo = m; else hi = m; }
  el.style.fontSize = lo + 'px'; } }"""


def pagina(peca, tom, base, story):
    modelo = peca.get("modelo", "frase")
    if modelo not in MODELOS:
        raise SystemExit(f"Modelo desconhecido: {modelo}. Existem: {', '.join(MODELOS)}")
    img = img_url(peca, base)
    tom = peca.get("tom", tom)
    if modelo == "foto":
        tom = "escuro"
    h = 1920 if story else 1350
    # story: textos fora dos 14% do topo e 20% da base
    topo, baixo = (300, 420) if story else (84, 150)
    miolo = MODELOS[modelo](peca, img, story)
    assinatura = ('<div class="assinatura"><b>Lucas Jesus</b><span class="fio"></span>'
                  '<span>lucasjesus.ia.br</span></div>')
    extra = " tem-foto" if modelo == "foto" else ""
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{fonte_css()}
:root{{--h:{h}px;--topo:{topo}px;--base:{baixo}px}}{CSS}</style></head>
<body><div class="quadro {tom}{extra}"><div class="miolo">{miolo}</div>{assinatura}</div></body></html>"""


def renderizar(spec_path, saida):
    spec_path = pathlib.Path(spec_path)
    saida = pathlib.Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    base = spec_path.parent
    tom = spec.get("tom", "claro")
    pecas = spec["pecas"]
    if not 1 <= len(pecas) <= 10:
        raise SystemExit("O Instagram aceita de 1 a 10 imagens.")
    total = len(pecas)
    for i, p in enumerate(pecas):
        if p.get("modelo") == "slide" and "slide" not in p and total > 1:
            p["slide"], p["total"] = i + 1, total
    trabalhos = [(f"{i + 1:02d}", p, False) for i, p in enumerate(pecas)]
    trabalhos.append(("story", spec.get("story") or pecas[0], True))
    from playwright.sync_api import sync_playwright
    feitos = []
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        for nome, p, story in trabalhos:
            pg = nav.new_page(viewport={"width": 1080, "height": 1920 if story else 1350})
            pg.set_content(pagina(p, tom, base, story), wait_until="load")
            pg.evaluate("document.fonts.ready")
            pg.evaluate(FIT_JS)
            pg.wait_for_timeout(150)
            png = pg.screenshot(type="png")
            pg.close()
            img = Image.open(io.BytesIO(png)).convert("RGB")
            destino = saida / f"{nome}.jpg"
            img.save(destino, "JPEG", quality=90, optimize=True, progressive=True)
            feitos.append(destino)
        nav.close()
    for f in feitos:
        print(f)
    return feitos


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    renderizar(sys.argv[1], sys.argv[2])
