"""
db.py  --  the SQLite database that replaces the PAGES list.

One file (search_engine.db) holds everything:
    pages     -> one row per crawled web page
    links     -> which page links to which URL (used later by PageRank)
    terms     -> every word in the index + how many pages contain it
    postings  -> the INVERTED INDEX: (word, page, how often, TF-IDF score)
"""
import sqlite3

DB_PATH = "search_engine.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS pages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    url        TEXT UNIQUE NOT NULL,
    domain     TEXT,
    title      TEXT,
    text       TEXT,
    crawled_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- We store the target as a URL (not an id) because the crawler often
-- sees a link before it has visited the page it points to.
CREATE TABLE IF NOT EXISTS links (
    src_id  INTEGER NOT NULL REFERENCES pages(id),
    dst_url TEXT    NOT NULL,
    PRIMARY KEY (src_id, dst_url)
);

CREATE TABLE IF NOT EXISTS terms (
    term      TEXT PRIMARY KEY,
    doc_freq  INTEGER NOT NULL          -- number of pages containing this word
);

CREATE TABLE IF NOT EXISTS postings (
    term     TEXT    NOT NULL,
    page_id  INTEGER NOT NULL REFERENCES pages(id),
    tf       INTEGER NOT NULL,          -- times the word appears on the page
    tfidf    REAL    NOT NULL,
    PRIMARY KEY (term, page_id)
);
CREATE INDEX IF NOT EXISTS idx_postings_page ON postings(page_id);
"""


def get_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row      # lets us use row["title"] instead of row[2]
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=DB_PATH):
    """Create the tables if they don't exist yet (safe to call many times)."""
    conn = get_connection(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def load_pages(db_path=DB_PATH):
    """
    Read the database and return a list shaped EXACTLY like the old PAGES
    list in app_simplified.py:
        {"id", "title", "domain", "text", "links": [ids of other pages]}
    Links to pages we never crawled are dropped, because PageRank can only
    score pages that exist in our graph.
    """
    conn = get_connection(db_path)
    rows = conn.execute("SELECT id, url, domain, title, text FROM pages").fetchall()
    url_to_id = {r["url"]: f"p{r['id']}" for r in rows}

    links_by_page = {f"p{r['id']}": [] for r in rows}
    for src_id, dst_url in conn.execute("SELECT src_id, dst_url FROM links"):
        src, dst = f"p{src_id}", url_to_id.get(dst_url)
        if dst and dst != src:                      # skip uncrawled + self-links
            links_by_page[src].append(dst)
    conn.close()

    return [
        {
            "id": f"p{r['id']}",
            "title": r["title"] or r["url"],
            "domain": r["domain"],
            "text": r["text"] or "",
            "url": r["url"],
            "links": links_by_page[f"p{r['id']}"],
        }
        for r in rows
    ]
