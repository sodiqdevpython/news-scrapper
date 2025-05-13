import requests
import json
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup

KEYS = [
    "e9a55154f9e14d4ca50d805c931676af",
    "e3f8530d1bfb4dab87492fbc2b0cccc6"
]
print("Taxminan 2 minutlar kutasiz aka ...")
def api():
    now = datetime.now(timezone.utc).date()
    since = now - timedelta(days=7)
    params = {
        "sources":"cnn","language":"en",
        "from":since.isoformat(),
        "to": now.isoformat(),
        "sortBy":"publishedAt"
    }
    url = "https://newsapi.org/v2/everything"
    for i in KEYS:
        r = requests.get(url, params={**params, "apiKey": i}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "ok":
                return data["articles"]
    raise RuntimeError("API limitga kelib qoldi")

def text_olish(html):
    soup = BeautifulSoup(html, "html.parser")
    texts = []
    for i in soup.select("div.article__content"):
        t = i.get_text(strip=True)
        if t:
            texts.append(t)
    return "\n\n".join(texts)
arts = api()
result = {"source": "edition.cnn.com", "posts": []}
for art in arts:
    url = art["url"]
    print(url[:60])
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        content = text_olish(r.text)
    except:
        content = ""
    dt = datetime.fromisoformat(art["publishedAt"].replace("Z","+00:00"))
    post = {
        "title":art.get("title",""),"url":url,
        "published_at":dt.strftime("%Y-%m-%d %H:%M"),
        "content":content,"category":["world news"], 
        "image_url":[art["urlToImage"]] if art.get("urlToImage") else []
    }
    result["posts"].append(post)
with open("cnn.json","w",encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

