import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, CrossEncoder
from qdrant_client import QdrantClient
from rank_bm25 import BM25Okapi
import litellm

load_dotenv()

# Load the same embedding model used for ingestion
model = SentenceTransformer("all-MiniLM-L6-v2")

# Cross-encoder reranker. Unlike the bi-encoder above (which embeds the
# question and each chunk separately, then compares vectors), the cross-encoder
# reads the question and a candidate chunk together in one pass and scores how
# relevant that chunk is to that question. It is slower, so we never run it over
# the whole corpus. We run it only over the small merged candidate set from
# hybrid retrieval, to reorder those candidates by true relevance.
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

# Connect to the existing Qdrant store
client = QdrantClient(path="./qdrant_local")
COLLECTION = "commissions"


# ---------------------------------------------------------------------------
# Keyword index setup
# We pull every chunk out of Qdrant once at startup and build a BM25 index
# over them. BM25 is classic keyword search: it scores chunks on the exact
# words they share with the question, which is the half pure-semantic search
# is blind to (names, show titles, slot times, anything literal).
# ---------------------------------------------------------------------------

def load_all_chunks():
    all_points = []
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        all_points.extend(points)
        if offset is None:
            break
    return all_points


# Build the keyword index once at import time
_chunks = load_all_chunks()
_corpus = [p.payload["text"] for p in _chunks]
_tokenised_corpus = [text.lower().split() for text in _corpus]
_bm25 = BM25Okapi(_tokenised_corpus)


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def retrieve_semantic(question, k=10):
    query_vector = model.encode(question).tolist()
    results = client.query_points(
        collection_name=COLLECTION, query=query_vector, limit=k
    )
    return results.points


def retrieve_keyword(question, k=10):
    tokenised_query = question.lower().split()
    scores = _bm25.get_scores(tokenised_query)
    # Pair each chunk with its BM25 score, sort high to low, take top k
    ranked = sorted(zip(_chunks, scores), key=lambda pair: pair[1], reverse=True)
    return [chunk for chunk, score in ranked[:k] if score > 0]


def merge_candidates(question, candidate_k=10):
    """Gather candidates from both retrieval paths and deduplicate by point id.

    This is the wide net. We pull more candidates than we ultimately want,
    because the reranker below is what narrows the set down to the best few.
    Order here is not meaningful yet; the cross-encoder decides the final order.
    """
    semantic_hits = retrieve_semantic(question, k=candidate_k)
    keyword_hits = retrieve_keyword(question, k=candidate_k)

    merged = {}
    for hit in semantic_hits:
        merged[hit.id] = hit
    for hit in keyword_hits:
        merged.setdefault(hit.id, hit)

    return list(merged.values())


def rerank(question, candidates, top_k=3, with_scores=False):
    """Reorder merged candidates by true relevance using the cross-encoder.

    We build (question, chunk_text) pairs, score them all in one batch, then
    sort high to low and keep the top_k. This replaces the old naive
    dict-insertion order with a real relevance ordering.

    with_scores returns (hit, score) pairs instead of bare hits. The
    Synthesiser needs the raw relevance score to decide whether a section
    has anything worth writing about, and that decision has to happen
    before any generation call. Kept as an opt-in flag so the default
    return shape, and everything already calling it, stays unchanged.
    """
    if not candidates:
        return []

    pairs = [(question, hit.payload["text"]) for hit in candidates]
    scores = reranker.predict(pairs)

    ranked = sorted(zip(candidates, scores), key=lambda pair: pair[1], reverse=True)
    top = ranked[:top_k]

    if with_scores:
        return [(hit, float(score)) for hit, score in top]
    return [hit for hit, score in top]


def retrieve(question, k=3, candidate_k=10, with_scores=False):
    """Hybrid retrieval with reranking.

    1. Gather a wide candidate set from semantic + keyword paths (candidate_k each).
    2. Deduplicate by point id.
    3. Rerank the merged set with a cross-encoder and keep the top k.
    """
    candidates = merge_candidates(question, candidate_k=candidate_k)
    return rerank(question, candidates, top_k=k, with_scores=with_scores)


def build_context(hits):
    blocks = []
    for hit in hits:
        source = hit.payload["source"]
        text = hit.payload["text"]
        blocks.append(f"[Source: {source}]\n{text}")
    return "\n\n".join(blocks)


def answer(question):
    hits = retrieve(question)
    context = build_context(hits)
    system_prompt = (
        "You are a research assistant for a TV sales team. "
        "Answer the question using ONLY the sources provided below. "
        "Every factual claim in your answer must cite its source in the form [source: filename]. "
        "If the sources do not contain the answer, say so plainly. Do not invent anything."
    )
    user_prompt = f"Sources:\n\n{context}\n\nQuestion: {question}"
    response = litellm.completion(
        model="openrouter/openrouter/free",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    question = "Which entertainment quiz show is hosted by Richard Osman, and who produces it?"
    print(f"Question: {question}\n")
    print(answer(question))
