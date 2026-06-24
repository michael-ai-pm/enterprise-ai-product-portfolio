import os
import glob
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# 1. Load the local embedding model (downloads once, then cached)
model = SentenceTransformer("all-MiniLM-L6-v2")
VECTOR_SIZE = 384  # this model outputs 384-dimension vectors

# 2. Connect to local Qdrant
client = QdrantClient(path="./qdrant_local")
COLLECTION = "commissions"

if client.collection_exists(COLLECTION):
    client.delete_collection(COLLECTION)
client.create_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
)

# 3. Read and chunk the documents
def chunk_text(text, size=500, overlap=50):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        chunk = words[start:start + size]
        chunks.append(" ".join(chunk))
        start += size - overlap
    return chunks

points = []
point_id = 0
for filepath in glob.glob("data/*.txt"):
    filename = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    for chunk in chunk_text(text):
        vector = model.encode(chunk).tolist()
        points.append(PointStruct(
            id=point_id,
            vector=vector,
            payload={"source": filename, "text": chunk},
        ))
        point_id += 1

client.upsert(collection_name=COLLECTION, points=points)
print(f"Ingested {len(points)} chunks from {len(glob.glob('data/*.txt'))} files.")

# 4. Run one retrieval query
query = "Which entertainment quiz show is hosted by Richard Osman?"
query_vector = model.encode(query).tolist()
results = client.query_points(collection_name=COLLECTION, query=query_vector, limit=3)

print(f"\nQuery: {query}\n")
for hit in results.points:
    print(f"[{round(hit.score, 3)}] {hit.payload['source']}")
    print(hit.payload['text'][:200], "...\n")