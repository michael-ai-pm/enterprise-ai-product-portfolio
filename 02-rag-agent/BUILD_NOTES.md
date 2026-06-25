# Build Notes: Sales Market Intelligence Agent

This is the honest record of the build. What the spec assumed, what the build actually did, and where the 2 pulled apart. I'm writing it as I go, while the friction is still fresh, because a retrospective reconstructed weeks later is a tidier story than the true one.

## The stack changed before I wrote a single line of agent code

The architecture document first specified a managed vector store and direct provider SDK calls. Before I built anything, I moved to self-hosted Qdrant and a LiteLLM gateway, and then I ran the whole build through OpenRouter's free tier instead of a paid provider. The honest driver here was cost, not architecture. I'm between roles and the build had to run on free infrastructure.

What's interesting is that the gateway I argued for on principle paid off immediately, and for a reason the spec didn't predict. The spec said a gateway keeps model choice as a config change rather than a rewrite. I didn't expect to test that claim on day 1. But the moment my constraint became budget, I switched the provider behind the gateway to a free one and changed nothing in the application code. The decision I'd justified on vendor neutrality turned out to earn its place on cost flexibility instead.

## The first retrieval scores were soft, and I knew why before I panicked

The first working retrieval returned the right document at the top, the ITV quiz show for a query about that quiz show. But the similarity score was around 0.448, not the 0.9 a clean match might suggest. For a moment that looks like a broken pipeline.

It isn't. I embedded each press release as 1 large chunk, where section 6.1 of the architecture document specifies 500-token chunks with a 50-token overlap. So the query was competing against a whole document of unrelated text packed into 1 vector. The retrieval logic is correct. The chunking isn't there yet. The score is telling me about chunk size, not about whether the system works. The next step is to build the chunking the spec already describes, then measure the scores again and see how much they sharpen.

## The library had moved on from what the spec assumed

2 small frictions the spec never mentioned, both in qdrant-client 1.18. The `recreate_collection` method is deprecated now, so I check whether the collection exists and create it instead. And `.search()` has been replaced by `.query_points()`, which returns the hits under a `.points` attribute. Neither is hard. But neither is visible until you actually build against the current library, which is exactly the kind of gap a spec written ahead of the build can't catch.

## Open items

- Build the spec-compliant chunking and re-measure retrieval quality.
- Close the retrieve-and-generate loop through the gateway, with citation enforcement at synthesis time.
- Swap the free embedding and generation path for the production model when I run the evals that actually count.

## Citation enforcement held on the weakest model, which I didn't expect

The architecture document treats citation enforcement as the single most important design decision, and the hardest to guarantee. So I expected the free model to be the place it broke first. It didn't. With the citation rule in the system prompt and the sources passed in the context, the free router returned a clean answer that cited the right file and pulled only from the retrieved text, not from its own training. 1 working result isn't proof it holds at scale, and I'll need the offline eval set to know the real citation rate. But the first signal is that enforcement through the prompt is doing more of the work than I assumed, even before any stronger model is involved. 
"## 25 June - checkpoint" 
"Ingestion and retrieve-generate working on the four-release corpus. Next session: chunking, 500-token chunks with 50-token overlap to sharpen retrieval scores. Paused build this week, picking back up from here." 
