"""
A tiny "search engine" built with Streamlit.

It does two things:
1. PageRank  -> scores each page by how many important pages link to it
2. Search    -> matches your search words against page text, then mixes
                that match score with the PageRank score to rank results

This is a simplified, heavily-commented version of the original code.
The logic is the same -- it's just written in a more step-by-step way,
so it's easier to follow as a beginner.
"""

import re
import streamlit as st


# ---------------------------------------------------------------------------
# 1. OUR "DATABASE"
# ---------------------------------------------------------------------------
# Normally a search engine would read from a real database. Here, we just
# use a Python list of dictionaries. Each dictionary is one "page", and it
# has an id, a title, a domain name, some text, and a list of pages it
# links to.
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


# ---------------------------------------------------------------------------
# 2. PAGERANK -- score every page by how many pages link to it
# ---------------------------------------------------------------------------
# @st.cache_data tells Streamlit: "if this function is called again with the
# same arguments, don't re-run it -- just reuse the answer from last time."
# This makes the app feel faster, since PageRank math doesn't need to be
# redone every single time the page reruns.
@st.cache_data
def calculate_pagerank(damping, iterations):
    """
    Give every page a score based on how many *important* pages link to it.
    A link from a well-linked page counts for more than a link from an
    obscure one. This is a simplified version of Google's PageRank.
    """
    total_pages = len(PAGES)

    # Step 1: everyone starts out equal.
    scores = {}
    for page in PAGES:
        scores[page["id"]] = 1 / total_pages

    # Step 2: repeat the scoring process several times. Each round, scores
    # flow along links, and after enough rounds they settle down (stop
    # changing much).
    for _ in range(iterations):
        # Start each round with a small "base score" for every page.
        next_scores = {}
        for page in PAGES:
            next_scores[page["id"]] = (1 - damping) / total_pages

        # Now spread each page's current score out along its links.
        for page in PAGES:
            num_links = len(page["links"])
            if num_links == 0:
                num_links = 1  # avoid dividing by zero

            share_per_link = scores[page["id"]] / num_links

            for target_id in page["links"]:
                next_scores[target_id] += damping * share_per_link

        scores = next_scores  # this round's result becomes next round's start

    return scores


# ---------------------------------------------------------------------------
# 3. TEXT MATCHING -- turn text into a list of lowercase words
# ---------------------------------------------------------------------------
def tokenize(text):
    """Split text into a list of lowercase words/numbers, ignoring punctuation."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return words


# ---------------------------------------------------------------------------
# 4. SEARCH -- combine keyword matching with PageRank authority
# ---------------------------------------------------------------------------
def search_pages(query, damping, iterations):
    ranks = calculate_pagerank(damping, iterations)
    highest_rank = max(ranks.values())
    query_words = tokenize(query)

    results = []
    for page in PAGES:
        page_words = tokenize(page["title"] + " " + page["text"] + " " + page["domain"])

        # Count how many times each query word appears in this page.
        match_count = 0
        for word in query_words:
            match_count += page_words.count(word)

        if query_words:
            relevance = min(match_count / len(query_words), 1)
        else:
            relevance = 0

        authority = ranks[page["id"]] / highest_rank
        score = relevance * 0.68 + authority * 0.32

        # Only keep this page if it matched something (or if there was no
        # search text at all, in which case we show everything).
        if relevance or not query_words:
            page_with_scores = dict(page)  # copy the page dict
            page_with_scores["relevance"] = relevance
            page_with_scores["authority"] = authority
            page_with_scores["score"] = score
            results.append(page_with_scores)

    # Sort so the highest-scoring pages come first.
    results.sort(key=lambda page: page["score"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# 5. BUILD A DIAGRAM (Graphviz "DOT" text) OF THE PAGE LINKS
# ---------------------------------------------------------------------------
def graph_text(ranks, highlighted_ids):
    highest_rank = max(ranks.values())

    lines = [
        "digraph web {",
        '  graph [rankdir=LR, bgcolor="transparent"];',
        '  node [shape=circle, style=filled, fontname="Arial"];',
        '  edge [color="#9aa6a0"];',
    ]

    for page in PAGES:
        size = 0.45 + 0.65 * ranks[page["id"]] / highest_rank
        if page["id"] in highlighted_ids:
            color = "#f47d68"
        else:
            color = "#c8f169"
        lines.append(
            f'  {page["id"]} [label="{page["id"]}", width={size:.2f}, '
            f'height={size:.2f}, fillcolor="{color}"];'
        )

    for page in PAGES:
        for target_id in page["links"]:
            lines.append(f'  {page["id"]} -> {target_id};')

    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 6. THE ACTUAL PAGE (this part runs every time Streamlit re-draws the app)
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Python PageRank Search", page_icon="i", layout="wide")

st.caption("PROJECTGROUP_4 / PYTHON-ONLY SEARCH ENGINE")
st.title("Find the pages that matter.")
st.write("PageRank, search ranking, graph data, and this interface are all implemented in Python.")

with st.sidebar:
    st.markdown("### Ranking controls")
    damping = st.slider("Damping factor", 0.50, 0.99, 0.85, 0.01)
    iterations = st.slider("Iterations", 1, 50, 20)
    st.caption("85% of authority follows links; the rest is distributed evenly across the graph.")
    st.metric("Indexed pages", len(PAGES))

    total_links = 0
    for page in PAGES:
        total_links += len(page["links"])
    st.metric("Known links", total_links)

query = st.text_input("Search the local web graph", "how does the web work")

results = search_pages(query, damping, iterations)
ranks = calculate_pagerank(damping, iterations)

top_four_ids = set()
for result in results[:4]:
    top_four_ids.add(result["id"])

results_column, graph_column = st.columns([1.5, 1], gap="large")

with results_column:
    st.subheader("Ranked pages")
    st.caption(f'Showing matches for "{query}" - {len(results)} pages')

    if not results:
        st.info("No pages matched that query. Try a broader phrase.")

    index = 1
    for page in results:
        with st.container(border=True):
            st.caption(f"{index:02d} / {page['domain']}")
            st.subheader(page["title"])
            st.write(page["text"])
            st.write(
                f"Match: {page['relevance']:.0%} - "
                f"Authority: {page['authority']:.0%} - "
                f"Links: {len(page['links'])}"
            )
        index += 1

with graph_column:
    st.subheader("The web graph")
    st.caption("Node size represents authority; highlighted nodes match the query.")
    st.graphviz_chart(graph_text(ranks, top_four_ids), use_container_width=True)

    st.subheader("PageRank scores")
    sorted_pages = sorted(PAGES, key=lambda page: ranks[page["id"]], reverse=True)
    scores_table = []
    for page in sorted_pages:
        scores_table.append({"page": page["title"], "authority": round(ranks[page["id"]], 4)})
    st.dataframe(scores_table, hide_index=True, use_container_width=True)

st.caption(
    "Search score = 68% keyword relevance + 32% normalized PageRank authority. "
    "This is an educational corpus and does not crawl the public web."
)
