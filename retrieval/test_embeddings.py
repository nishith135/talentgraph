from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
# Load a small, fast embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Try embedding a few sentences
sentences = [
    "Python developer with backend experience",
    "Backend engineer skilled in server-side development",
    "Sales manager with client relationship experience"
]

embeddings = model.encode(sentences)

print("Shape of embeddings:", embeddings.shape)
print("First embedding (first 10 numbers):", embeddings[0][:10])

similarity_1_2 = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
similarity_1_3 = cosine_similarity([embeddings[0]], [embeddings[2]])[0][0]

print(f"Similarity between Python dev and Backend engineer: {similarity_1_2:.4f}")
print(f"Similarity between Python dev and Sales manager: {similarity_1_3:.4f}")