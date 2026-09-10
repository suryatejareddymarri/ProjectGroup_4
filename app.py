from __future__ import annotations

import re
from http import HTTPStatus
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

PAGES = [
    {
        "id": "atlas",
        "title": "The Atlas of the Open Web",
        "text": "A field guide to hyperlinks, browsers, protocols, and the people who keep the web open and connected.",
        "links": ["protocols", "commons", "ranking", "libraries"],
    },
    {
        "id": "ranking",
        "title": "Ranking Pages by Importance",
        "text": "A plain-language tour of PageRank, authority, damping, and why a link can be a vote with context.",
        "links": ["atlas", "algorithms", "search", "commons"],
    },
    {
        "id": "algorithms",
        "title": "Algorithms for Curious People",
        "text": "A visual introduction to algorithms: sort, traverse, score, and use feedback to improve a system.",
        "links": ["ranking", "search", "code"],
    },
    {
        "id": "protocols",
        "title": "How the Web Works",
        "text": "URLs, DNS, HTTP requests, servers, and the quiet sequence of events behind every page you open.",
        "links": ["atlas", "code", "libraries"],
    },
    {
        "id": "commons",
        "title": "The Knowledge Commons",
        "text": "How communities document what they know, share it freely, and build durable public infrastructure.",
        "links": ["atlas", "libraries", "search"],
    },
    {
        "id": "libraries",
        "title": "A Library of Small Tools",
        "text": "Thoughtful software tools for reading, making, searching, and turning scattered notes into useful knowledge.",
        "links": ["code", "commons", "algorithms"],
    },
    {
        "id": "search",
        "title": "Inside a Search Engine",
        "text": "Crawling, indexing, matching, and ranking: the pipeline that turns a question into a useful set of pages.",
        "links": ["ranking", "algorithms", "code"],
    },
    {
        "id": "code",
        "title": "Notes on Building Software",
        "text": "Practical notes on debugging, interfaces, data structures, and making complex software feel simple.",
        "links": ["algorithms", "libraries", "protocols"],
    },
]


def calculate_pagerank(damping: float = 0.85, iterations: int = 20) -> dict[str, float]:
    """Calculate authority scores using the iterative PageRank formula."""
    total_pages = len(PAGES)
    scores = {page["id"]: 1 / total_pages for page in PAGES}

    for _ in range(iterations):
        next_scores = {
            page["id"]: (1 - damping) / total_pages for page in PAGES
        }
        for page in PAGES:
            share = scores[page["id"]] / max(len(page["links"]), 1)
            for target in page["links"]:
                next_scores[target] += damping * share
        scores = next_scores

    return scores


def tokenize(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.lower())


def search_pages(query: str, damping: float, iterations: int) -> list[dict]:
    ranks = calculate_pagerank(damping, iterations)
    maximum_rank = max(ranks.values())
    terms = tokenize(query)
    results = []

    for page in PAGES:
        words = tokenize(f'{page["title"]} {page["text"]} {page["id"]}')
        hits = sum(words.count(term) for term in terms)
        relevance = min(hits / len(terms), 1) if terms else 0
        authority = ranks[page["id"]] / maximum_rank
        if relevance or not terms:
            results.append({
                **page,
                "relevance": round(relevance, 4),
                "authority": round(authority, 4),
                "score": round(relevance * 0.68 + authority * 0.32, 4),
            })

    return sorted(results, key=lambda page: page["score"], reverse=True)


@app.get("/api/search")
def api_search():
    query = request.args.get("q", "")
    try:
        damping = min(max(float(request.args.get("damping", 0.85)), 0.5), 0.99)
        iterations = min(max(int(request.args.get("iterations", 20)), 1), 50)
    except ValueError:
        return jsonify({"error": "damping must be a number and iterations must be an integer"}), HTTPStatus.BAD_REQUEST

    return jsonify({
        "query": query,
        "damping": damping,
        "iterations": iterations,
        "results": search_pages(query, damping, iterations),
    })


@app.get("/api/graph")
def api_graph():
    ranks = calculate_pagerank()
    return jsonify({"nodes": [{"id": page["id"], "rank": ranks[page["id"]]} for page in PAGES], "pages": PAGES})


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Python PageRank Search</title>
  <style>
    :root{font-family:Georgia,serif;color:#192126;background:#f5f6f0}*{box-sizing:border-box}body{max-width:960px;margin:0 auto;padding:48px 22px}h1{font-size:clamp(42px,8vw,78px);line-height:.95;font-weight:500;max-width:700px;margin:14px 0}p{font:15px/1.5 Arial,sans-serif;color:#687376}.eyebrow{font:700 11px Arial,sans-serif;letter-spacing:.15em;text-transform:uppercase;color:#687376}.search{display:flex;border:1px solid #192126;background:#fff;margin:28px 0 22px}.search input{flex:1;border:0;padding:17px;font:17px Arial,sans-serif;min-width:0}.search button{border:0;padding:0 22px;background:#c8f169;font-weight:700}.controls{display:flex;gap:22px;flex-wrap:wrap;font:12px Arial,sans-serif;color:#687376}.controls label{display:flex;align-items:center;gap:8px}.results{margin-top:28px;background:#fff;border:1px solid #dfe4df}.result{padding:18px 20px;border-bottom:1px solid #dfe4df}.result:last-child{border:0}.result h2{font-size:24px;font-weight:500;margin:0 0 6px}.result h2 a{color:#192126}.meta{font:11px Arial,sans-serif;color:#687376}.badge{display:inline-block;background:#eef1ec;padding:5px 7px;margin:10px 6px 0 0;font:11px Arial,sans-serif}.empty{text-align:center;padding:48px;font:14px Arial,sans-serif;color:#687376}.note{margin-top:24px;font-size:12px}
  </style>
</head>
<body>
  <div class="eyebrow">ProjectGroup_4 / Python backend</div>
  <h1>Find the pages that matter.</h1>
  <p>PageRank and search ranking are calculated on the server by Python.</p>
  <form class="search" id="form"><input id="query" value="how does the web work" placeholder="Search the local web graph"><button>Search</button></form>
  <div class="controls"><label>Damping <input id="damping" type="range" min=".5" max=".99" step=".01" value=".85"><output id="dampingOutput">0.85</output></label><label>Iterations <input id="iterations" type="range" min="1" max="50" value="20"><output id="iterationsOutput">20</output></label></div>
  <section class="results" id="results"></section>
  <p class="note">The backend combines 68% keyword relevance with 32% normalized PageRank authority. Try changing the controls and searching again.</p>
  <script>
    const query = document.getElementById('query');
    const damping = document.getElementById('damping');
    const iterations = document.getElementById('iterations');
    const results = document.getElementById('results');
    async function runSearch() {
      document.getElementById('dampingOutput').value = Number(damping.value).toFixed(2);
      document.getElementById('iterationsOutput').value = iterations.value;
      const params = new URLSearchParams({q: query.value, damping: damping.value, iterations: iterations.value});
      const response = await fetch('/api/search?' + params);
      const data = await response.json();
      results.innerHTML = data.results.length ? data.results.map((page, index) => `<article class="result"><div class="meta">0${index + 1} / ${page.id}</div><h2><a href="#">${page.title}</a></h2><p>${page.text}</p><span class="badge">match ${Math.round(page.relevance * 100)}%</span><span class="badge">authority ${Math.round(page.authority * 100)}%</span></article>`).join('') : '<div class="empty">No pages matched that query.</div>';
    }
    document.getElementById('form').addEventListener('submit', event => { event.preventDefault(); runSearch(); });
    damping.addEventListener('input', runSearch); iterations.addEventListener('input', runSearch); runSearch();
  </script>
</body>
</html>"""


@app.get("/")
def index():
    return render_template_string(PAGE_TEMPLATE)


if __name__ == "__main__":
    app.run(debug=True)
