# Enterprise AI Product Portfolio

A public exploration of enterprise AI product management practice: architecture decisions,
evaluation discipline, and operating models for production AI.

This repository works through the full lifecycle of an AI product portfolio end to end.
It covers how a portfolio of AI products is governed from intake to retirement, how one
product (a retrieval-augmented agent) is specified, built, and evaluated, and how the
frameworks that hold the portfolio together are designed. A fictional TV studios business
is used as the worked example throughout, because the domain is concrete enough to make
the decisions feel real. The patterns themselves apply to any enterprise running multiple
AI products in parallel.

## What you will find here

- **Strategy and operating model:** a six-gate lifecycle from intake to retirement,
  multi-team coordination, vendor strategy, and a three-year roadmap.
- **Working build:** a retrieval-augmented agent with hybrid retrieval over self-hosted Qdrant, mandatory citation enforcement, a planner-synthesiser-reviewer pattern, and an offline eval pipeline.
- **Evaluation frameworks:** how to set thresholds before building, run golden-set evals,
  and detect drift in production.
- **Governance and unit economics:** EU AI Act classification, HITL patterns, kill-switch
  design, cost-floor FinOps, and the model for retiring products that do not pay for themselves.

## How to read this repository

If you care about **architecture decisions**, start with the
[RAG agent specification](./02-rag-agent/architecture.md) and the build notes alongside it.

If you care about **evaluation discipline**, start with the
[portfolio eval framework](./03-frameworks/evals.md) and the eval sections of the agent spec.

If you care about **responsible AI in regulated industries**, start with the
[governance and risk framework](./03-frameworks/governance.md).

If you care about **unit economics**, start with the
[FinOps and value tracking model](./03-frameworks/finops.md) and section 7 of the
[operating model](./01-strategy/operating-model.md).

## Repository structure
/01-strategy          AI strategy and operating model
/02-rag-agent         Agent specification, working build, and build retrospective
/03-frameworks        Governance, eval framework, RACI, and FinOps model
/04-trend-analyser    Second use case slice demonstrating platform reuse

## A note on the approach

The decisions here are deliberately conservative. Where the fashionable answer is a fully
autonomous agent, a pure-RAG architecture, or a single-vendor model strategy, this repository goes the other way: constrained loops, hybrid retrieval, self-hosted and vendor-neutral infrastructure.
The reasons are documented in each artefact.

This is not the only way to build enterprise AI products. It is one defensible way, written
down in enough detail that the trade-offs are visible.

## Status

Active. New artefacts and code are added regularly.

## Licence

MIT. See [LICENSE](./LICENSE).