import requests
import json
from datetime import datetime, timedelta

API_KEY1 = "e9a55154f9e14d4ca50d805c931676af"
API_KEY2 = "e3f8530d1bfb4dab87492fbc2b0cccc6"
def api(api_key):
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    url = "https://newsapi.org/v2/everything"
    params = {
        "sources":  "cnn",
        "language": "en",
        "from":     week_ago.isoformat(),
        "to":       today.isoformat(),
        "sortBy":   "publishedAt",
        "apiKey":   api_key
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    return data["articles"]
try:
    articles = api(API_KEY1)
except Exception:
    articles = api(API_KEY2)
output = {
    "source": "edition.cnn.com",
    "posts": []
}

for i in articles:
    dt = datetime.fromisoformat(i["publishedAt"].replace("Z", "+00:00"))
    published_at = dt.strftime("%Y-%m-%d %H:%M")
    post = {
        "title":i.get("title", ""),
        "url":i.get("url", ""),
        "published_at":published_at,
        "content":i.get("content") or i.get("description", ""),
        "category":["world news"], 
        "image_url":[i["urlToImage"]] if i.get("urlToImage") else []
    }
    output["posts"].append(post)

with open("cnn.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("Tugadi")
