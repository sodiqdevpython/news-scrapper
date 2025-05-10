import requests
import json
import html
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup

LIST_URL = "https://api.uza.uz/api/v1/posts"
DETAIL_URL = "https://api.uza.uz/api/v1/posts/{slug}"
LANG = "oz"
PER_PAGE = 28
PAGE_LIMIT = 5
DAYS_BACK = 7
OUT_FILE = "uza.json"


def clean_html(html_fragment: str) -> str:
    if not html_fragment:
        return ""

    html_fragment = html.unescape(html_fragment)

    soup = BeautifulSoup(html_fragment, "html5lib")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    clean_text = soup.get_text(" ", strip=True)

    return clean_text

def normalize_detail(resp_json: dict) -> dict:
    if isinstance(resp_json, dict) and "data" in resp_json and isinstance(resp_json["data"], dict):
        return resp_json["data"]
    return resp_json

def parse_detail(data: dict) -> dict:
    title = data.get("title", "").strip()
    slug  = data.get("slug", "").strip()
    url   = f"https://uza.uz/oz/posts/{slug}"

    pub_raw = data.get("publish_time", "")
    try:
        pub_dt = datetime.strptime(pub_raw, "%Y-%m-%d %H:%M:%S")
        published_at = pub_dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        published_at = ""

    html = data.get("content") or data.get("body") or ""
    content = clean_html(html)

    category = data.get("category", {}).get("title", "Noma'lum")

    image_url = (
        data.get("files", {})
            .get("thumbnails", {})
            .get("normal", {})
            .get("src")
    )

    return {
        "title": title,
        "url": url,
        "published_at": published_at,
        "content": content,
        "source": "uza.uz",
        "category": category,
        "image_url": image_url
    }

def get_list_page(page: int):
    params = {"page": page, "per_page": PER_PAGE, "_f": "json", "_l": LANG}
    r = requests.get(LIST_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data["data"] if isinstance(data, dict) and "data" in data else data

def get_detail(slug: str):
    url = DETAIL_URL.format(slug=slug)
    r = requests.get(url, params={"_f": "json", "_l": LANG}, timeout=10)
    r.raise_for_status()
    return normalize_detail(r.json())

def main():
    collected = []
    threshold = datetime.now() - timedelta(days=DAYS_BACK)
    page = 1

    while page <= PAGE_LIMIT:
        items = get_list_page(page)
        if not items:
            break

        for it in items:
            pub_dt = datetime.strptime(it["publish_time"], "%Y-%m-%d %H:%M:%S")
            if pub_dt < threshold:
                print("Tugadi...")
                page = PAGE_LIMIT + 1
                break

            slug = it.get("slug")
            if not slug:
                continue
            try:
                detail = get_detail(slug)
                collected.append(parse_detail(detail))
                print(f"✅  {slug}")
            except Exception as e:
                print(f"❌  {slug} → {e}")
        else:
            page += 1
            continue
        break

    Path(OUT_FILE).write_text(
        json.dumps(collected, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n{len(collected)} ta yangilik saqlandi {OUT_FILE} ga")

if __name__ == "__main__":
    main()
