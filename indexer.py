"""
indexer.py  --  PART 2: the Indexer.

Reads every crawled page from the database and builds the INVERTED INDEX:
    word -> {page: how important this word is on that page (TF-IDF)}
exactly like the index at the back of a textbook.

Run it (after crawling):
    python indexer.py
"""
import math
import re
from collections import Counter

from db import init_db, DB_PATH

# Common filler words that carry no meaning for searching.
STOP_WORDS = set("""
a about above after again all also am an and any are as at be because been before
being below between both but by can could did do does doing down during each few
for from further had has have having he her here hers him his how i if in into is
it its just me more most my no nor not now of off on once only or other our out
over own same she should so some such than that the their them then there these
they this those through to too under until up very was we were what when where
which while who whom why will with would you your
""".split())


def tokenize(text):
    """'The Web works!' -> ['web', 'works']  (lowercase, no punctuation, no stop words)"""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 1]


def build_index(db_path=DB_PATH):
    conn = init_db(db_path)
    pages = conn.execute("SELECT id, title, text FROM pages").fetchall()
    total_pages = len(pages)
    if total_pages == 0:
        print("No pages in the database - run the crawler first.")
        return

    # Step 1: count words on every page (title words count double -> titles matter more).
    counts_per_page = {}
    for p in pages:
        tokens = tokenize(p["title"] or "") * 2 + tokenize(p["text"] or "")
        counts_per_page[p["id"]] = (Counter(tokens), len(tokens))

    # Step 2: document frequency = how many pages contain each word.
    doc_freq = Counter()
    for counts, _ in counts_per_page.values():
        doc_freq.update(counts.keys())

    # Step 3: TF-IDF.  TF = word count / page length,  IDF = log((1+N)/(1+df)) + 1
    postings = []
    for page_id, (counts, length) in counts_per_page.items():
        for term, tf in counts.items():
            idf = math.log((1 + total_pages) / (1 + doc_freq[term])) + 1
            postings.append((term, page_id, tf, (tf / length) * idf))

    # Step 4: rebuild the index tables from scratch.
    conn.execute("DELETE FROM postings")
    conn.execute("DELETE FROM terms")
    conn.executemany("INSERT INTO terms (term, doc_freq) VALUES (?, ?)", doc_freq.items())
    conn.executemany("INSERT INTO postings (term, page_id, tf, tfidf) VALUES (?, ?, ?, ?)", postings)
    conn.commit()
    conn.close()
    print(f"Indexed {total_pages} pages, {len(doc_freq)} unique words, {len(postings)} postings.")


def keyword_scores(query, db_path=DB_PATH):
    """
    Look the query words up in the inverted index.
    Returns {"p12": 0..1, ...}  -- a relevance score for each matching page.
    This replaces the slow 'loop over every page and count words' code.
    """
    words = tokenize(query)
    if not words:
        return {}
    conn = init_db(db_path)
    marks = ",".join("?" * len(words))
    rows = conn.execute(
        f"SELECT page_id, SUM(tfidf) AS score FROM postings WHERE term IN ({marks}) GROUP BY page_id",
        words,
    ).fetchall()
    conn.close()
    if not rows:
        return {}
    best = max(r["score"] for r in rows)
    return {f"p{r['page_id']}": r["score"] / best for r in rows}   # normalised to 0..1


if __name__ == "__main__":
    build_index()
