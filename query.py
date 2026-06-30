import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from rank_bm25 import BM25Okapi
import litellm

load_dotenv()

# Load the same embedding model used for ingestion
model = SentenceTransformer("all-MiniLM-L6-v2")

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

def retrieve_semantic(question, k=5):
    query_vector = model.encode(question).tolist()
    results = client.query_points(
        collection_name=COLLECTION, query=query_vector, limit=k
    )
    return results.points


def retrieve_keyword(question, k=5):
    tokenised_query = question.lower().split()
    scores = _bm25.get_scores(tokenised_query)
    # Pair each chunk with its BM25 score, sort high to low, take top k
    ranked = sorted(zip(_chunks, scores), key=lambda pair: pair[1], reverse=True)
    return [chunk for chunk, score in ranked[:k] if score > 0]


def retrieve(question, k=3):
    """Hybrid retrieval: semantic + keyword, merged and deduplicated.

    We gather candidates from both paths, drop duplicates by point id,
    then return the top k. The merge is deliberately simple for v1:
    a chunk that surfaces in either path is a candidate. Reranking with
    a cross-encoder is the next build step and will replace this naive
    merge with a proper relevance ordering.
    """
    semantic_hits = retrieve_semantic(question, k=k)
    keyword_hits = retrieve_keyword(question, k=k)

    merged = {}
    for hit in semantic_hits:
        merged[hit.id] = hit
    for hit in keyword_hits:
        merged.setdefault(hit.id, hit)

    return list(merged.values())[: k * 2]


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
