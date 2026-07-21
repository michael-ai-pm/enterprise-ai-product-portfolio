# Build Notes: Sales Market Intelligence Agent

This is the honest record of the build. What the spec assumed, what the build actually did, and where the two pulled apart. I'm writing it as I go, while the friction is still fresh, because a retrospective reconstructed weeks later is a tidier story than the true one.

## The stack changed before I wrote a single line of agent code

The architecture document first specified a managed vector store and direct provider SDK calls. Before I built anything, I moved to self-hosted Qdrant and a LiteLLM gateway, and then I ran the whole build through OpenRouter's free tier instead of a paid provider. The honest driver here was cost, not architecture. I'm between roles and the build had to run on free infrastructure.

What's interesting is that the gateway I argued for on principle paid off immediately, and for a reason the spec didn't predict. The spec said a gateway keeps model choice as a config change rather than a rewrite. I didn't expect to test that claim on day one. But the moment my constraint became budget, I switched the provider behind the gateway to a free one and changed nothing in the application code. The decision I'd justified on vendor neutrality turned out to earn its place on cost flexibility instead.

## The first retrieval scores were soft, and I knew why before I panicked

The first working retrieval returned the right document at the top, the ITV quiz show for a query about that quiz show. But the similarity score was around 0.448, not the 0.9 a clean match might suggest. For a moment that looks like a broken pipeline.

It isn't. I embedded each press release as one large chunk, where section 6.1 of the architecture document specifies 500-token chunks with a 50-token overlap. So the query was competing against a whole document of unrelated text packed into one vector. The retrieval logic is correct. The chunking isn't there yet. The score is telling me about chunk size, not about whether the system works. The next step is to build the chunking the spec already describes, then measure the scores again and see how much they sharpen.

## The library had moved on from what the spec assumed

Two small frictions the spec never mentioned, both in qdrant-client 1.18. The `recreate_collection` method is deprecated now, so I check whether the collection exists and create it instead. And `.search()` has been replaced by `.query_points()`, which returns the hits under a `.points` attribute. Neither is hard. But neither is visible until you actually build against the current library, which is exactly the kind of gap a spec written ahead of the build can't catch.

## Citation enforcement held on the weakest model, which I didn't expect

The architecture document treats citation enforcement as the single most important design decision, and the hardest to guarantee. So I expected the free model to be the place it broke first. It didn't. With the citation rule in the system prompt and the sources passed in the context, the free router returned a clean answer that cited the right file and pulled only from the retrieved text, not from its own training. One working result isn't proof it holds at scale, and I'll need the offline eval set to know the real citation rate. But the first signal is that enforcement through the prompt is doing more of the work than I assumed, even before any stronger model is involved.

## 25 June - checkpoint

Ingestion and retrieve-generate working on the four-release corpus. Next session: chunking, 500-token chunks with 50-token overlap to sharpen retrieval scores. Paused build this week, picking back up from here.

## 30 June - the chunking was already done, and I almost rebuilt it

I came back to this after a pause believing chunking was still the next task, because that's what my own checkpoint said and what my kanban implied. Before writing anything, I read the ingestion script instead of trusting the note. The 500-token chunking with 50-token overlap was already there, matching section 6.1. I'd built it in an earlier session and then lost track of it across the gap.

The lesson is uncomfortable but useful. On a good-energy day, the guilt pushes me to write fresh code on top of code I haven't read. If I'd trusted the note over the file, I'd have spent my best hour of the week rebuilding something that already worked. Reading first isn't the slow option. It's the one that stops you wasting the fast option.

One honest caveat on the chunking. It splits on words, not true tokens, and the chunk metadata is lighter than the architecture document describes. It stores source and text, but not date, territory, genre, or broadcaster. That metadata is what section 6.1 calls part of the ingestion contract, and it's what makes the structured filtering in hybrid retrieval possible later. So the chunking is done in shape, not yet in full. The enrichment is a refinement for a later pass, not a blocker now.

## 30 June - hybrid retrieval shipped, and the merge is deliberately naive

The spec says route structured questions to structured data and semantic questions to the vector store. I added the keyword half today using BM25 over the same chunks, so a literal query, a show title or a host name, now has a path that scores on exact words rather than only on meaning. Both paths run, and I merge their candidates and deduplicate by id.

I want to be honest that the merge is the simplest thing that works. A chunk that surfaces in either path becomes a candidate, and that's it. There's no relevance-weighted ordering yet. That's the reranking step, a cross-encoder over the combined candidates, and it's the next real task. I shipped the naive merge on purpose rather than waiting to build the clever version, because a working hybrid path I can measure beats a perfect one I'm still designing.

## 1 July - reranking

The naive merge from 30 June returned candidates in dict-insertion order, semantic first then keyword appended. That order meant nothing. A chunk was not ranked by relevance, it was ranked by which path happened to find it first.

I added a cross-encoder reranker (cross-encoder/ms-marco-MiniLM-L-6-v2) over the merged set. The bi-encoder embeds the question and each chunk separately then compares vectors. The cross-encoder reads the question and a candidate together in one pass and scores the pair directly. It is more accurate and slower, so I never run it over the whole corpus. I widened both retrieval paths to pull 10 candidates each, merged and deduplicated them, then let the cross-encoder reorder that small set and keep the top 3.

Same MiniLM family as the embedding model, runs local on CPU, no API cost. Fits the free-tier discipline. Tested on the Richard Osman query, answer came back clean and cited.

## 20 July - the venv blocker, and how a fortnight of being stuck cleared in one session

The honest gap in this log is the one between 1 July and now. The build stalled, and it did not stall on anything intellectually hard. It stalled on a corrupted virtual environment. Pip installs kept breaking the environment on the Windows setup, and every attempt to build on top of it inherited the corruption. I lost real time to it, and the frustration of being blocked by plumbing rather than by the actual problem is its own kind of tax. It is worth recording plainly, because a retrospective that skips the dead weeks tells a cleaner story than the true one.

The fix was not clever. The working environment already existed on my laptop, which was the original source machine. The Windows setup was the copy, and it was the copy that had corrupted. Rather than keep trying to rebuild the broken one, I went back to the machine where the venv already worked. Confirming it was clean took one command, `python query.py`, and a clean cited answer came back. The lesson I want to hold onto is that a blocker can feel enormous for a fortnight and take one session to clear once you stop trying to repair the broken path and switch to the one that already works.

## 20 July - unit tests for the retrieval layer

This was the task carried from 2 July and never done until now. I wrote eight unit tests over the retrieval functions: keyword retrieval returning results for a known term, the zero-score filter dropping nonsense queries, the k and top_k caps being respected, the merge deduplicating by id, the reranker handling an empty candidate set without erroring, the end-to-end retrieve returning source-attributed hits, and build_context wrapping every chunk with its source marker.

They run against the real Qdrant store rather than mocks. That was a deliberate choice. At this stage I would rather the tests confirm the pipeline behaves on the actual indexed corpus than confirm it behaves against a fake I built to pass. All eight passed. The one I cared about most was the deduplication test, because the naive merge from 30 June is exactly the kind of code that looks right and quietly returns duplicates.

## 20 July - the corpus was too small to prove anything, so I grew it

The integration test the plan calls for assumes 20 sample documents. I had four. Four documents is not enough for a retrieval test to mean much, because the system barely has to discriminate to look good. So before the integration test I wrote 16 more sample commission releases, matched to the exact format of the real four, spread across seven broadcasters and six genre families.

One deliberate decision here, tied to the whole point of this portfolio. The documents are fictional. Invented show titles, invented production companies,

## Open items

- Enrich chunk metadata (date, territory, genre, broadcaster) to enable structured filtering. Still the main gap between the chunking as built and the ingestion contract in section 6.1.
- Grow the corpus with documents long enough to exercise the 500-token chunking. The current 20 are all single-chunk, so splitting is built but unproven.
- Move the root scripts into the rag-agent folder and fix the relative paths.
- Build the Planner stage: the structured plan of sub-queries, one per briefing section. This is the next real build task.
- Build the Reviewer stage. Only the retrieve-and-synthesise core plus reranking exists so far.
- Stand up the offline eval set, so citation rate and hallucination rate become measured numbers rather than single-example impressions.
- Swap the free embedding and generation path for the production model when I run the evals that actually count.
