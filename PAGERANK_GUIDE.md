# PageRank Search Engine Guide

This project is a small, interactive search engine model. It uses PageRank to measure link authority, then combines that authority with keyword relevance to rank results.

## Run it

Create the environment and launch the Streamlit frontend:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run streamlit_app.py
```

Then open the local URL printed by Streamlit in your browser.

To stop the app, return to the terminal and press `Ctrl+C`.

## Project files

- `streamlit_app.py` contains the complete application, including the data, PageRank algorithm, search logic, interface, and graph.
- `requirements.txt` lists the Python packages needed to run the app.
- `README.md` contains the short project description.
- `.gitignore` keeps the virtual environment and Python cache files out of Git.

## What it demonstrates

- PageRank authority calculated over a small directed web graph
- Search ranking that combines keyword relevance and link authority
- Interactive graph showing links and node authority
- Adjustable damping factor and iteration count
- Explainable result factors for every ranked page

Try searches such as `algorithms ranking`, `how does the web work`, or `building software`.

## Model

Each page starts with equal authority. On every iteration, a page distributes its authority across its outgoing links:

```text
PR(A) = (1 - d) / N + d * sum(PR(B) / L(B))
```

The search score combines 68% textual relevance with 32% normalized PageRank authority:

```text
search score = 0.68 * relevance + 0.32 * authority
```

Relevance is based on matching words in a page's title, description, or domain. Authority is the page's PageRank score normalized against the highest-ranked page.

## Controls

- **Damping factor** controls how much authority follows links. The default value is `0.85`.
- **Iterations** controls how many times authority flows through the graph. More iterations allow the scores to settle.
- **Search box** filters and ranks pages for the entered words.

The graph uses larger nodes for pages with higher authority and highlights pages that match the search.

The entire application is written in Python using Streamlit. This is an educational model with a small manually-created corpus; it does not crawl the public web or use an external search index.
