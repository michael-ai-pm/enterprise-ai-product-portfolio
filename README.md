# Enterprise AI Product Portfolio

A public exploration of how enterprise AI products are designed, governed, evaluated, and scaled across a portfolio of use cases.

This repository documents an end-to-end view of an enterprise AI platform supporting a global TV studios business: from the operating model that governs the portfolio, through the working build of one product (a Sales Market Intelligence Agent), to the evaluation, governance, and FinOps frameworks that hold the whole thing together.

It is written from the perspective of a senior product manager responsible for taking an AI capability from intake through to retirement, across multiple teams, vendors, and risk tiers.

---

## Why this exists

Most public AI product writing focuses on individual features or model demos. Enterprise AI is a different problem: portfolios of products at different maturity stages, multi-team coordination, regulatory exposure, vendor diversity, and unit economics that have to work at scale.

This repository tries to fill that gap by working through one realistic scenario end to end, in public.

The fictional company is MetroStudios, a global TV studios business with twelve in-flight AI use cases across the production lifecycle. The work is fictional in setting but the artefacts, frameworks, and decisions are written to be directly applicable to any enterprise running multiple AI products in parallel.

---

## What's inside

### Strategy and operating model

- [AI Strategy and Operating Model](./01-strategy/operating-model.md) - the portfolio view, the six-gate lifecycle from intake to retirement, multi-team RACI, and the three-year roadmap.

### The build: Sales Market Intelligence Agent

- [Architecture and specification](./02-sales-agent/architecture.md) - a senior PM's specification of an agent that compresses pre-pitch market research from 1.5 days to under 20 minutes, with full eval scaffolding.
- [Build notes](./02-sales-agent/BUILD_NOTES.md) - an honest retrospective comparing the specification to what actually shipped.
- [Working code](./02-sales-agent/src) - the agent itself, planner-retriever-synthesiser-reviewer pattern, hybrid retrieval, mandatory citation, eval pipeline.

### Cross-portfolio frameworks

- [Governance and risk framework](./03-frameworks/governance.md) - EU AI Act classification, HITL patterns, audit and kill-switch design.
- [Portfolio eval framework](./03-frameworks/evals.md) - one framework that adapts across heterogeneous AI products.
- [Multi-team RACI](./03-frameworks/raci.md) - decision rights across Product, Data, ML Engineering, Platform, Legal, Cyber, and Vendor Management.
- [FinOps and value tracking](./03-frameworks/finops.md) - unit economics, cost floors, and the model for retiring products that don't pay for themselves.

### Second use case slice

- [YouTube Trend Analyser](./04-trend-analyser) - a second product slice demonstrating platform reuse and second-product economics.

---

## How to read this repository

If you have 5 minutes: read [the strategy doc](./01-strategy/operating-model.md), section 4 (the operating model gates).

If you have 30 minutes: read the strategy doc end to end, then the [Sales Agent architecture](./02-sales-agent/architecture.md).

If you have a couple of hours: work through everything in order. The frameworks make more sense after seeing how they apply to the working build.

---

## A note on the approach

The choices made in these documents are deliberately conservative. Where the fashionable answer would be a fully autonomous agent, an everything-RAG architecture, or a single-vendor model strategy, this repository goes the other way: constrained loops, hybrid retrieval, multi-vendor by policy. The reasons are documented in each artefact.

This is not the only way to build enterprise AI products. It is one defensible way, written down in enough detail that the trade-offs are visible.

---

## Status

Active. This repository is being developed in public over a focused period, with new artefacts and code added regularly. Watch the repo or follow the commit history to track progress.

---

## License

MIT. See [LICENSE](./LICENSE).
