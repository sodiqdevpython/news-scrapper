import requests, json, re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from bs4 import BeautifulSoup

LIST_TPL = "https://meduza.io/api/w5/new_search?chrono=news&page={page}&per_page=70&locale=ru"
DAYS_BACK = 7
PAGE_MAX = 10
OUT_FILE = "meduza.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MeduzaScraper/1.0)"}
UTC = timezone.utc
THRESHOLD = datetime.now(UTC) - timedelta(days=DAYS_BACK)

def slug_date(slug: str) -> datetime | None:
    m = re.match(r"^[^/]+/(\d{4})/(\d{2})/(\d{2})/", slug)
    if m:
        y, mth, d = map(int, m.groups())
        return datetime(y, mth, d, tzinfo=UTC)
    return None

def fetch_slug_list(page: int) -> list[str]:
    r = requests.get(LIST_TPL.format(page=page), timeout=10)
    r.raise_for_status()
    return r.json().get("collection", [])

def scrape_page(slug: str) -> dict | None:
    url = f"https://meduza.io/{slug}"
    r = requests.get(url, headers=HEADERS, timeout=10)
    if r.status_code != 200:
        print("Status", r.status_code, url)
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    title = (
        (soup.find("meta", property="og:title") or {}).get("content")
        or (soup.title.string if soup.title else "")
    ).strip()

    published_at = ""
    meta_iso = (soup.find("meta", property="article:published_time") or {}).get("content")
    if meta_iso:
        try:
            dt = datetime.fromisoformat(meta_iso.replace("Z", "+00:00"))
            published_at = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass

    if not published_at:
        t_tag = soup.select_one(".GeneralMaterialHeadline-meta time[datetime]")
        if t_tag and t_tag.has_attr("datetime"):
            try:
                dt = datetime.fromisoformat(t_tag["datetime"].replace("Z", "+00:00"))
                published_at = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass

    if not published_at:
        script_tag = soup.find("script", id="__NEXT_DATA__") or soup.find("script", id="__STATE__")
        if script_tag and script_tag.string:
            m = re.search(r'"datetime"\s*:\s*(\d{10,})', script_tag.string)
            if m:
                try:
                    dt = datetime.fromtimestamp(int(m.group(1)), tz=UTC)
                    published_at = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass

    if not published_at:
        s_date = slug_date(slug)
        if s_date:
            published_at = s_date.strftime("%Y-%m-%d 00:00")

    article_blocks = soup.select(".GeneralMaterial-module-article")
    content = " ".join(b.get_text(" ", strip=True) for b in article_blocks).strip()
    image_url = (soup.find("meta", property="og:image") or {}).get("content")

    post = {
        "title": title,
        "url": url,
        "published_at": published_at,
        "content": content,
        "category": [slug.split("/")[0].capitalize()],
        "image_url": [image_url] if image_url else [],
        "type": "gazeta"
    }

    return post

def main():
    posts = []
    page = 0

    while page < PAGE_MAX:
        slugs = fetch_slug_list(page)
        if not slugs:
            break

        for slug in slugs:
            s_date = slug_date(slug)
            if s_date and s_date < THRESHOLD:
                page = PAGE_MAX
                break

            data = scrape_page(slug)
            if data:
                posts.append(data)
                print("✅", slug)
        else:
            page += 1
            continue
        break

    result = {
        "source": "meduza.io",
        "posts": posts
    }

    Path(OUT_FILE).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(posts)} ta yangilik saqlandi → {OUT_FILE}")

if __name__ == "__main__":
    main()
