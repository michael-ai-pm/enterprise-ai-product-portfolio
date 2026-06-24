import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import litellm

load_dotenv()

# Load the same embedding model used for ingestion
model = SentenceTransformer("all-MiniLM-L6-v2")

# Connect to the existing Qdrant store
client = QdrantClient(path="./qdrant_local")
COLLECTION = "commissions"

def retrieve(question, k=3):
    query_vector = model.encode(question).tolist()
    results = client.query_points(collection_name=COLLECTION, query=query_vector, limit=k)
    return results.points

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