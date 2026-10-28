"""
crawler.py  --  PART 1: the Web Crawler.

Starts at one or more seed URLs, downloads each page, saves its title + text,
records every link it finds, and then follows those links (breadth-first).

Run it:
    python crawler.py https://quotes.toscrape.com --max-pages 40
"""
import argparse
import time
from collections import deque
from urllib.parse import urljoin, urldefrag, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from db import init_db, DB_PATH

USER_AGENT = "ProjectGroup4-Crawler/1.0 (college project)"
SKIP_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".zip",
                   ".mp4", ".mp3", ".css", ".js", ".ico", ".xml")


def normalize_url(url):
    """Make equal URLs look identical: drop #fragments, lowercase host."""
    url, _ = urldefrag(url)
    p = urlparse(url)
    return p._replace(scheme=p.scheme.lower(), netloc=p.netloc.lower()).geturl()


class RobotsCache:
    """Respect robots.txt (the site's 'please don't crawl this' rules)."""
    def __init__(self):
        self.parsers = {}

    def allowed(self, url):
        p = urlparse(url)
        base = f"{p.scheme}://{p.netloc}"
        if base not in self.parsers:
            rp = RobotFileParser(base + "/robots.txt")
            try:
                rp.read()
            except Exception:
                pass                       # no robots.txt reachable -> allow
            self.parsers[base] = rp
        return self.parsers[base].can_fetch(USER_AGENT, url)


def fetch_and_parse(url):
    """Download one page. Returns (title, text, [links]) or None on failure."""
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
    except requests.RequestException as e:
        print(f"   ! failed: {e}")
        return None
    if resp.status_code != 200 or "text/html" not in resp.headers.get("Content-Type", ""):
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()                    # remove code, keep readable text

    title = soup.title.get_text(strip=True) if soup.title else ""
    text = " ".join(soup.get_text(" ", strip=True).split())[:50000]

    links = []
    for a in soup.find_all("a", href=True):
        link = normalize_url(urljoin(url, a["href"]))
        if urlparse(link).scheme in ("http", "https") and not link.lower().endswith(SKIP_EXTENSIONS):
            links.append(link)
    return title, text, list(dict.fromkeys(links))   # dedupe, keep order


def save_page(conn, url, title, text, links):
    """Insert/update the page, then replace its outgoing links."""
    conn.execute(
        """INSERT INTO pages (url, domain, title, text) VALUES (?, ?, ?, ?)
           ON CONFLICT(url) DO UPDATE SET title=excluded.title, text=excluded.text,
                                          crawled_at=CURRENT_TIMESTAMP""",
        (url, urlparse(url).netloc, title, text),
    )
    page_id = conn.execute("SELECT id FROM pages WHERE url = ?", (url,)).fetchone()["id"]
    conn.execute("DELETE FROM links WHERE src_id = ?", (page_id,))
    conn.executemany(
        "INSERT OR IGNORE INTO links (src_id, dst_url) VALUES (?, ?)",
        [(page_id, l) for l in links if l != url],
    )
    conn.commit()


def crawl(seeds, max_pages=30, delay=0.5, same_domain_only=True, db_path=DB_PATH):
    conn = init_db(db_path)
    robots = RobotsCache()
    allowed_domains = {urlparse(s).netloc.lower() for s in seeds}

    # Resume support: pages already in the DB are not downloaded again.
    visited = {r["url"] for r in conn.execute("SELECT url FROM pages")}
    queue = deque(normalize_url(s) for s in seeds)
    crawled = 0

    while queue and crawled < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        if same_domain_only and urlparse(url).netloc.lower() not in allowed_domains:
            continue
        if not robots.allowed(url):
            print(f"-- blocked by robots.txt: {url}")
            continue

        print(f"[{crawled + 1}/{max_pages}] {url}")
        result = fetch_and_parse(url)
        if result is None:
            continue
        title, text, links = result
        save_page(conn, url, title, text, links)
        crawled += 1

        queue.extend(l for l in links if l not in visited)
        time.sleep(delay)                  # be polite: don't hammer the server

    conn.close()
    print(f"\nDone. Crawled {crawled} new pages into {db_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Simple breadth-first web crawler")
    ap.add_argument("seeds", nargs="+", help="starting URL(s)")
    ap.add_argument("--max-pages", type=int, default=30)
    ap.add_argument("--delay", type=float, default=0.5, help="seconds between requests")
    ap.add_argument("--any-domain", action="store_true", help="also follow links to other sites")
    ap.add_argument("--db", default=DB_PATH)
    args = ap.parse_args()
    crawl(args.seeds, args.max_pages, args.delay, not args.any_domain, args.db)
