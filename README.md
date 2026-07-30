# Enterprise AI Product Portfolio

A public exploration of enterprise AI product management practice: architecture decisions,
evaluation discipline, and operating models for production AI.

This repository works through the full lifecycle of an AI product portfolio end to end.
It covers how a portfolio of AI products is governed from intake to retirement, how one
product (a retrieval-augmented agent) is specified, built, and evaluated, and how the
frameworks that hold the portfolio together are designed. It also records what happened
when the specification met a real environment, because the gap between the two is where
most enterprise AI stalls. A fictional TV studios business is used as the worked example
throughout, because the domain is concrete enough to make the decisions feel real. The
patterns themselves apply to any enterprise running multiple AI products in parallel.

## What you will find here

- **Strategy and operating model:** a six-gate lifecycle from intake to retirement,
  multi-team coordination, vendor strategy, and a three-year roadmap.
- **Working build:** a retrieval-augmented agent with hybrid retrieval over self-hosted
  Qdrant, cross-encoder reranking, a planner stage producing structured output, and a
  synthesiser that refuses to answer sections where the evidence is not there.
- **Governance:** EU AI Act classification, HITL patterns, kill-switch design, vendor
  risk, and tier-driven data handling.
- **Deployment reality:** what the specification assumed, what the environment actually
  allowed, and which design targets survived contact with it.

## How to read this repository

If you care about **architecture decisions**, start with the
[RAG agent specification](./02-rag-agent/architecture.md) and the build notes alongside it.

If you care about **responsible AI in regulated industries**, start with the
[governance and risk framework](./03-frameworks/governance.md).

If you care about **operating models and unit economics**, start with the
[strategy and operating model](./01-strategy/operating-model.md). Section 4 covers the
six-gate lifecycle, section 7 the cost-floor FinOps model.

If you care about **what happens between the specification and production**, start with the
[build notes](./02-rag-agent/BUILD_NOTES.md). They record the constraints the environment
imposed, the design targets that were not met and why, and where a claim made early in the
build was later corrected by measurement.

## The build

The agent follows a plan, retrieve, synthesise, review pattern, with each stage as a
separate call so that a failure can be attributed to one component rather than to the
whole loop.

| Stage | Status |
|---|---|
| Retrieval: hybrid semantic and BM25, cross-encoder reranking | Built, unit and integration tested |
| Planner: structured output, one sub-query set per briefing section | Built, tested |
| Synthesiser: per-section synthesis with citation enforcement and evidence-gated refusal | Built, tested |
| Reviewer: rejects any section marked answered that carries no citation | Not built |
| Offline eval pipeline: golden set, citation rate, refusal accuracy | Not built |

The eval framework, multi-team RACI, and FinOps model are specified within the strategy
and architecture documents. They are not yet broken out as standalone artefacts.

## Repository structure

```
/01-strategy          AI strategy and operating model
/02-rag-agent         Agent specification, working build, and build retrospective
/03-frameworks        Governance and risk framework
```

Agent code, the sample corpus, and the test suites sit at the repository root.

## A note on the approach

The decisions here are deliberately conservative. Where the fashionable answer is a fully
autonomous agent, a pure-RAG architecture, or a single-vendor model strategy, this
repository goes the other way: constrained loops, hybrid retrieval, self-hosted and
vendor-neutral infrastructure. The reasons are documented in each artefact.

Thresholds and targets are written as targets. Where a number was measured, the build notes
say so. Where it was not, they say that too. Where an early claim turned out to be wrong,
the correction is written into the log rather than quietly replacing what came before.

This is not the only way to build enterprise AI products. It is one defensible way, written
down in enough detail that the trade-offs are visible.

## Status

Active. New artefacts and code are added regularly.

## Licence

MIT. See [LICENSE](./LICENSE).
