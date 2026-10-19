"""Radar de IA: lê os feeds oficiais e a imprensa de tecnologia e grava as notícias das últimas 72h.

Roda todo dia de madrugada pelo GitHub (workflow "Radar de IA") e grava radar/AAAA-MM-DD.json.
O Pesquisador do squad lê esse arquivo primeiro e depois confirma e aprofunda na web.
Só usa a biblioteca padrão do Python.
"""
import datetime as dt
import email.utils
import html
import json
import pathlib
import re
import urllib.request
import xml.etree.ElementTree as ET

FONTES = {
    # oficiais (peso maior: é a fonte primária)
    "OpenAI": ("https://openai.com/news/rss.xml", 3),
    "Google": ("https://blog.google/technology/ai/rss/", 3),
    "Google DeepMind": ("https://deepmind.google/blog/rss.xml", 3),
    "Hugging Face": ("https://huggingface.co/blog/feed.xml", 2),
    "Microsoft": ("https://blogs.microsoft.com/ai/feed/", 2),
    "NVIDIA": ("https://blogs.nvidia.com/feed/", 2),
    # imprensa
    "The Verge": ("https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", 2),
    "TechCrunch": ("https://techcrunch.com/category/artificial-intelligence/feed/", 2),
    "MIT Technology Review": ("https://www.technologyreview.com/topic/artificial-intelligence/feed", 2),
    "Ars Technica": ("https://arstechnica.com/ai/feed/", 1),
    "Tecnoblog": ("https://tecnoblog.net/feed/", 1),
}

# Assuntos que interessam ao público do Lucas (empresário que quer aplicar IA)
QUENTES = ["agent", "agente", "claude", "anthropic", "gpt", "openai", "gemini", "llama", "whatsapp", "automat",
           "business", "empresa", "small business", "pequen", "produtiv", "launch", "lança", "release", "model",
           "voice", "voz", "video", "vídeo", "image", "imagem", "brasil", "brazil", "free", "grátis", "price", "preço"]
IA = re.compile(r"\b(ai|ia|a\.i\.|intelig[eê]ncia artificial|artificial intelligence|llm|chatgpt|gpt|claude|gemini|"
                r"copilot|agente?s?|machine learning|openai|anthropic|deepmind)\b", re.I)


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (radar lucasjesus.ia.br)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def limpar(txt):
    txt = re.sub(r"<[^>]+>", " ", html.unescape(txt or ""))
    return re.sub(r"\s+", " ", txt).strip()


def data(txt):
    if not txt:
        return None
    try:
        return email.utils.parsedate_to_datetime(txt).astimezone(dt.timezone.utc)
    except Exception:
        pass
    try:
        return dt.datetime.fromisoformat(txt.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
    except Exception:
        return None


def itens(xml_bytes):
    raiz = ET.fromstring(xml_bytes)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for it in raiz.iter("item"):  # RSS
        yield (it.findtext("title"), it.findtext("link"), it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date"),
               it.findtext("description"))
    for it in raiz.iter("{http://www.w3.org/2005/Atom}entry"):  # Atom
        link = it.find("a:link", ns)
        yield (it.findtext("a:title", namespaces=ns), link.get("href") if link is not None else "",
               it.findtext("a:published", namespaces=ns) or it.findtext("a:updated", namespaces=ns),
               it.findtext("a:summary", namespaces=ns) or it.findtext("a:content", namespaces=ns))


def main():
    agora = dt.datetime.now(dt.timezone.utc)
    limite = agora - dt.timedelta(hours=72)
    noticias, falhas = [], []
    for nome, (url, peso) in FONTES.items():
        try:
            for titulo, link, quando, resumo in itens(baixar(url)):
                d = data(quando)
                titulo, resumo = limpar(titulo), limpar(resumo)[:500]
                if not titulo or (d and d < limite):
                    continue
                if peso < 3 and not IA.search(f"{titulo} {resumo}"):
                    continue  # imprensa geral: só o que for de IA
                horas = (agora - d).total_seconds() / 3600 if d else 48
                quente = sum(k in f"{titulo} {resumo}".lower() for k in QUENTES)
                nota = round(peso * 2 + min(quente, 4) + max(0, 3 - horas / 24), 2)
                noticias.append({"fonte": nome, "titulo": titulo, "link": link, "data": d.isoformat() if d else "",
                                 "resumo": resumo, "nota": nota})
        except Exception as e:
            falhas.append(f"{nome}: {str(e)[:120]}")
    noticias.sort(key=lambda n: -n["nota"])
    vistos, unicas = set(), []
    for n in noticias:
        chave = re.sub(r"\W+", "", n["titulo"].lower())[:60]
        if chave not in vistos:
            vistos.add(chave)
            unicas.append(n)
    hoje = agora.astimezone(dt.timezone(dt.timedelta(hours=-3))).date().isoformat()
    destino = pathlib.Path(f"radar/{hoje}.json")
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(json.dumps({"gerado_em": agora.isoformat(timespec="seconds"), "falhas": falhas,
                                   "noticias": unicas[:40]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # guarda só os últimos 14 dias
    for velho in sorted(pathlib.Path("radar").glob("*.json"))[:-14]:
        velho.unlink()
    print(f"{len(unicas)} notícias; {len(falhas)} fontes com falha. Gravado em {destino}")
    for f in falhas:
        print("  falha:", f)


if __name__ == "__main__":
    main()
