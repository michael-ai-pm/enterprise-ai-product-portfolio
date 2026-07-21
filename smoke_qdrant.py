from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = QdrantClient(path="./qdrant_local")

if client.collection_exists("test"):
    client.delete_collection("test")

client.create_collection(
    collection_name="test",
    vectors_config=VectorParams(size=4, distance=Distance.COSINE),
)

points = [
    PointStruct(id=i, vector=[0.1 * i, 0.2 * i, 0.3 * i, 0.4 * i], payload={"label": f"doc {i}"})
    for i in range(1, 6)
]
client.upsert(collection_name="test", points=points)

result = client.query_points(collection_name="test", query=[0.2, 0.4, 0.6, 0.8], limit=3)
for h in result.points:
    print(h.payload["label"], round(h.score, 3))

print("qdrant works")