from __future__ import annotations

import re

import streamlit as st


PAGES = [
    {
        "id": "atlas",
        "title": "The Atlas of the Open Web",
        "domain": "atlas.example",
        "text": "A field guide to hyperlinks, browsers, protocols, and the people who keep the web open and connected.",
        "links": ["protocols", "commons", "ranking", "libraries"],
    },
    {
        "id": "ranking",
        "title": "Ranking Pages by Importance",
        "domain": "research.example",
        "text": "A plain-language tour of PageRank, authority, damping, and why a link can be a vote with context.",
        "links": ["atlas", "algorithms", "search", "commons"],
    },
    {
        "id": "algorithms",
        "title": "Algorithms for Curious People",
        "domain": "patterns.example",
        "text": "A visual introduction to algorithms: sort, traverse, score, and use feedback to improve a system.",
        "links": ["ranking", "search", "code"],
    },
    {
        "id": "protocols",
        "title": "How the Web Works",
        "domain": "fieldnotes.example",
        "text": "URLs, DNS, HTTP requests, servers, and the quiet sequence of events behind every page you open.",
        "links": ["atlas", "code", "libraries"],
    },
    {
        "id": "commons",
        "title": "The Knowledge Commons",
        "domain": "commons.example",
        "text": "How communities document what they know, share it freely, and build durable public infrastructure.",
        "links": ["atlas", "libraries", "search"],
    },
    {
        "id": "libraries",
        "title": "A Library of Small Tools",
        "domain": "workbench.example",
        "text": "Thoughtful software tools for reading, making, searching, and turning scattered notes into useful knowledge.",
        "links": ["code", "commons", "algorithms"],
    },
    {
        "id": "search",
        "title": "Inside a Search Engine",
        "domain": "research.example",
        "text": "Crawling, indexing, matching, and ranking: the pipeline that turns a question into a useful set of pages.",
        "links": ["ranking", "algorithms", "code"],
    },
    {
        "id": "code",
        "title": "Notes on Building Software",
        "domain": "workbench.example",
        "text": "Practical notes on debugging, interfaces, data structures, and making complex software feel simple.",
        "links": ["algorithms", "libraries", "protocols"],
    },
]


@st.cache_data
def calculate_pagerank(damping: float, iterations: int) -> dict[str, float]:
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
        words = tokenize(f'{page["title"]} {page["text"]} {page["domain"]}')
        hits = sum(words.count(term) for term in terms)
        relevance = min(hits / len(terms), 1) if terms else 0
        authority = ranks[page["id"]] / maximum_rank
        if relevance or not terms:
            results.append({
                **page,
                "relevance": relevance,
                "authority": authority,
                "score": relevance * 0.68 + authority * 0.32,
            })

    return sorted(results, key=lambda page: page["score"], reverse=True)


def graph_text(ranks: dict[str, float], highlighted: set[str]) -> str:
    lines = ["digraph web {", "  graph [rankdir=LR, bgcolor=\"transparent\"];",
             "  node [shape=circle, style=filled, fontname=\"Arial\"];", "  edge [color=\"#9aa6a0\"];"]
    maximum_rank = max(ranks.values())
    for page in PAGES:
        size = 0.45 + 0.65 * ranks[page["id"]] / maximum_rank
        color = "#f47d68" if page["id"] in highlighted else "#c8f169"
        lines.append(
            f'  {page["id"]} [label="{page["id"]}", width={size:.2f}, height={size:.2f}, fillcolor="{color}"];')
    for page in PAGES:
        for target in page["links"]:
            lines.append(f'  {page["id"]} -> {target};')
    lines.append("}")
    return "\n".join(lines)


st.set_page_config(page_title="Python PageRank Search",
                   page_icon="i", layout="wide")
st.markdown(
    """
    <style>
    .stApp { background: #f5f6f0; color: #192126; }
    [data-testid="stHeader"] { background: transparent; }
    .hero { padding: 2rem 0 1.5rem; }
    .eyebrow { color: #6f7a7c; font: 700 0.72rem Arial, sans-serif; letter-spacing: .16em; text-transform: uppercase; }
    h1 { font-family: Georgia, serif !important; font-weight: 500 !important; letter-spacing: -.04em; }
    .result { background: white; border: 1px solid #dfe4df; padding: 1.1rem 1.25rem; margin: .75rem 0; }
    .result h3 { font-family: Georgia, serif; font-weight: 500; margin: 0 0 .35rem; }
    .meta, .description { color: #6f7a7c; font: .88rem/1.45 Arial, sans-serif; }
    .tag { background: #eef1ec; color: #53605c; display: inline-block; font: .72rem Arial, sans-serif; margin: .7rem .35rem 0 0; padding: .3rem .45rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="hero"><div class="eyebrow">ProjectGroup_4 / Python-only search engine</div><h1>Find the pages that matter.</h1><p class="description">PageRank, search ranking, graph data, and this interface are all implemented in Python.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Ranking controls")
    damping = st.slider("Damping factor", 0.50, 0.99, 0.85, 0.01)
    iterations = st.slider("Iterations", 1, 50, 20)
    st.caption(
        "85% of authority follows links; the rest is distributed evenly across the graph.")
    st.metric("Indexed pages", len(PAGES))
    st.metric("Known links", sum(len(page["links"]) for page in PAGES))

query = st.text_input("Search the local web graph", "how does the web work")
search_button = st.button("Search index", type="primary")
if search_button:
    st.session_state["query"] = query
active_query = st.session_state.get("query", query)

results = search_pages(active_query, damping, iterations)
ranks = calculate_pagerank(damping, iterations)
highlighted = {result["id"] for result in results[:4]}

results_column, graph_column = st.columns([1.5, 1], gap="large")
with results_column:
    st.subheader("Ranked pages")
    st.caption(f'Showing matches for "{active_query}" · {len(results)} pages')
    if not results:
        st.info("No pages matched that query. Try a broader phrase.")
    for index, page in enumerate(results, 1):
        st.markdown(
            f'''<article class="result"><div class="meta">{index:02d} / {page["domain"]}</div><h3>{page["title"]}</h3><div class="description">{page["text"]}</div><span class="tag">match {page["relevance"]:.0%}</span><span class="tag">authority {page["authority"]:.0%}</span><span class="tag">{len(page["links"])} outbound links</span></article>''',
            unsafe_allow_html=True,
        )

with graph_column:
    st.subheader("The web graph")
    st.caption(
        "Node size represents PageRank authority; coral nodes match the query.")
    st.graphviz_chart(graph_text(ranks, highlighted), use_container_width=True)
    st.subheader("PageRank scores")
    st.dataframe(
        [{"page": page["title"], "authority": round(ranks[page["id"]], 4)} for page in sorted(
            PAGES, key=lambda item: ranks[item["id"]], reverse=True)],
        hide_index=True,
        use_container_width=True,
    )

st.caption("Search score = 68% keyword relevance + 32% normalized PageRank authority. This is an educational corpus and does not crawl the public web.")
