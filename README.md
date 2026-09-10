# ProjectGroup_4

An interactive, browser-based PageRank search engine model.

## Run it

Open `pagerank-search.html` in any modern browser. No build step or dependencies are required.

## What it demonstrates

- PageRank authority calculated over a small directed web graph
- Search ranking that combines keyword relevance and link authority
- Interactive SVG graph showing links and node authority
- Adjustable damping factor and iteration count
- Explainable result factors for every ranked page

## Model

Each page starts with equal authority. On every iteration, a page distributes its authority across its outgoing links:

```text
PR(A) = (1 - d) / N + d * sum(PR(B) / L(B))
```

The search score combines 68% textual relevance with 32% normalized PageRank authority.

This is an educational model with a small manually-created corpus. It does not crawl the public web.
