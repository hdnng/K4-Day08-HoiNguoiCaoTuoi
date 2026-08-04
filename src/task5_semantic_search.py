"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""

import os
from pathlib import Path
import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
# Phải khớp với EMBEDDING_MODEL/EMBEDDING_DIM trong task4_chunking_indexing.py —
# query và chunk đã lưu trong ChromaDB phải cùng không gian vector thì so sánh
# cosine similarity mới có ý nghĩa.
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 1024
COLLECTION_NAME = "ecommerce_support_docs"

_client = None
_collection = None

def get_genai_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Thiếu GEMINI_API_KEY. Hãy điền key Gemini vào file .env "
                "(xem .env.example) trước khi chạy semantic_search()."
            )
        _client = genai.Client(api_key=api_key)
    return _client

def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score
            'metadata': dict     # source, doc_type, chunk_index
        }
        Sorted by score descending.
    """
    client = get_genai_client()
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=query,
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
    )
    query_vector = result.embeddings[0].values

    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    
    output = []
    if results["documents"] and len(results["documents"]) > 0:
        for doc, meta, dist in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            score = max(0.0, 1.0 - dist)  # cosine distance → similarity
            output.append({"content": doc, "score": round(score, 4), "metadata": meta})
    
    output.sort(key=lambda x: x["score"], reverse=True)
    return output[:top_k]


if __name__ == "__main__":
    # Test
    results = semantic_search("quy định trả hàng hoàn tiền shopee", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
