# ProjectGroup_4

An interactive, Python-only PageRank search engine model.

## Run it

Create the environment and launch the Streamlit frontend:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run streamlit_app.py
```

Then open the local URL printed by Streamlit in your browser.

## What it demonstrates

- PageRank authority calculated over a small directed web graph
- Search ranking that combines keyword relevance and link authority
- Interactive graph showing links and node authority
- Adjustable damping factor and iteration count
- Explainable result factors for every ranked page

## Model

Each page starts with equal authority. On every iteration, a page distributes its authority across its outgoing links:

```text
PR(A) = (1 - d) / N + d * sum(PR(B) / L(B))
```

The search score combines 68% textual relevance with 32% normalized PageRank authority.

The entire application is written in Python using Streamlit. This is an educational model with a small manually-created corpus; it does not crawl the public web.
