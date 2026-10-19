"""Lê o desempenho dos posts dos últimos 30 dias pela API oficial da Meta e grava em metricas/.

Precisa dos segredos META_TOKEN e IG_USER_ID e da permissão instagram_manage_insights
(ou instagram_business_manage_insights no login com Instagram). Só usa a biblioteca padrão.
"""
import datetime as dt
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from publicar import IG, TOKEN, api  # noqa: E402

METRICAS = ["reach", "saved", "shares", "total_interactions", "views"]


def insights(mid):
    pedidas = list(METRICAS)
    while pedidas:
        try:
            r = api("GET", f"{mid}/insights", metric=",".join(pedidas))
            return {d["name"]: (d.get("values") or [{}])[0].get("value", d.get("total_value", {}).get("value"))
                    for d in r.get("data", [])}
        except RuntimeError as e:
            # métrica não suportada para esse tipo de mídia: tira a última e tenta de novo
            if "metric" in str(e).lower() and len(pedidas) > 1:
                pedidas.pop()
                continue
            return {"erro": str(e)[:200]}
    return {}


def main():
    if not TOKEN or not IG:
        sys.exit("Faltam os segredos META_TOKEN e IG_USER_ID.")
    agora = dt.datetime.now(dt.timezone.utc)
    conta = api("GET", IG, fields="username,followers_count,media_count")
    midias = api("GET", f"{IG}/media", fields="id,caption,timestamp,media_type,permalink,like_count,comments_count",
                 limit=50).get("data", [])
    posts = []
    for m in midias:
        quando = dt.datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00"))
        if agora - quando > dt.timedelta(days=30):
            continue
        posts.append({"data": m["timestamp"][:10], "tipo": m.get("media_type"), "link": m.get("permalink"),
                      "inicio_legenda": (m.get("caption") or "")[:90], "curtidas": m.get("like_count"),
                      "comentarios": m.get("comments_count"), **insights(m["id"])})
    pasta = pathlib.Path("metricas")
    pasta.mkdir(exist_ok=True)
    (pasta / "ultimas.json").write_text(json.dumps({"gerado_em": agora.isoformat(timespec="seconds"),
                                                    "seguidores": conta.get("followers_count"), "posts": posts},
                                                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    hist_arq = pasta / "seguidores.json"
    hist = json.loads(hist_arq.read_text(encoding="utf-8")) if hist_arq.exists() else []
    hist.append({"data": agora.date().isoformat(), "seguidores": conta.get("followers_count")})
    hist_arq.write_text(json.dumps(hist[-104:], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"@{conta.get('username')}: {conta.get('followers_count')} seguidores; {len(posts)} posts lidos.")


if __name__ == "__main__":
    main()
