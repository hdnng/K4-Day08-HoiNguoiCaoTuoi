"""
Task 4 — Chunking & Indexing vào Vector Store.

Hướng dẫn:
    1. Đọc toàn bộ markdown files từ data/standardized/
    2. Chọn 1 chunking strategy (giải thích lý do)
    3. Chọn 1 embedding model (giải thích lý do)
    4. Index vào vector store (ChromaDB khuyến cáo — đơn giản, local, không cần Docker)

Chunking options (langchain-text-splitters):
    - RecursiveCharacterTextSplitter: an toàn, phổ biến
    - MarkdownHeaderTextSplitter: tốt cho file có heading
    - SemanticChunker: dùng embedding để tách (nâng cao)

Embedding model options:
    - sentence-transformers/all-MiniLM-L6-v2 (384 dim, nhẹ)
    - BAAI/bge-m3 (1024 dim, multilingual, tốt cho cả tiếng Việt lẫn tiếng Anh)
    - OpenAI text-embedding-3-small (1536 dim, API)

Vector store options:
    - ChromaDB (khuyến cáo: đơn giản, local persistent, không cần Docker)
    - Weaviate (hỗ trợ hybrid search built-in, cần Docker/Cloud)
    - FAISS (chỉ dense search)

Cài đặt:
    pip install langchain-text-splitters sentence-transformers chromadb

Lưu ý quan trọng: nếu sau này đổi corpus (đổi chủ đề, thêm/bớt tài liệu), phải XÓA
chroma_db/ cũ trước khi reindex — nếu không, chunk cũ và mới sẽ tồn tại lẫn lộn
trong cùng collection, retrieval sẽ trả về kết quả rác từ dữ liệu cũ.
"""

from pathlib import Path

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn của bạn trong comment
# =============================================================================

# Chunking: RecursiveCharacterTextSplitter — an toàn với markdown có heading
# không đều nhau giữa các nguồn (Shopee/Lazada/Decathlon/TGDD).
# CHUNK_SIZE=800: đủ lớn để giữ trọn 1 điều khoản/đoạn chính sách trong 1 chunk,
# tránh cắt giữa câu gây mất ngữ cảnh khi retrieve.
# CHUNK_OVERLAP=100 (12.5% size): đảm bảo câu nằm ở ranh giới 2 chunk vẫn xuất
# hiện trọn vẹn ở ít nhất 1 chunk.
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
CHUNKING_METHOD = "recursive"  # "recursive" | "markdown_header" | "semantic"

# Embedding: Gemini gemini-embedding-001 (API) — multilingual, không cần tải
# model về máy, phù hợp khi máy yếu hoặc muốn cả nhóm dùng chung 1 embedding
# nhất quán qua API thay vì local model.
# Cần GEMINI_API_KEY trong file .env (xem .env.example).
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 1024  # output_dimensionality truncate từ 3072 xuống 1024 để nhẹ hơn khi lưu ChromaDB

# TODO: Chọn vector store
VECTOR_STORE = "chromadb"  # "chromadb" | "weaviate" | "faiss"
COLLECTION_NAME = "ecommerce_support_docs"


# =============================================================================
# IMPLEMENTATION
# =============================================================================

def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/.

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str}}
    """
    documents = []
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        doc_type = "legal" if "legal" in str(md_file) else "news"
        documents.append({
            "content": content,
            "metadata": {"source": md_file.name, "type": doc_type}
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo strategy đã chọn.

    Returns:
        List of {'content': str, 'metadata': dict} — mỗi item là 1 chunk
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = []
    for doc in documents:
        splits = splitter.split_text(doc["content"])
        for i, chunk_text in enumerate(splits):
            chunks.append({
                "content": chunk_text,
                "metadata": {**doc["metadata"], "chunk_index": i}
            })
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng Gemini Embedding API.

    Cần GEMINI_API_KEY trong .env — điền key của bạn vào file .env
    (copy từ .env.example, dòng GEMINI_API_KEY=...).

    Returns:
        Mỗi chunk dict được thêm key 'embedding': list[float]
    """
    import os
    import time
    from dotenv import load_dotenv
    from google import genai
    from google.genai import types

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Thiếu GEMINI_API_KEY. Hãy điền key Gemini của bạn vào file .env "
            "(xem .env.example) trước khi chạy embed_chunks()."
        )

    client = genai.Client(api_key=api_key)

    for i, chunk in enumerate(chunks):
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=chunk["content"],
            config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
        )
        chunk["embedding"] = result.embeddings[0].values
        print(f"  Embedded {i + 1}/{len(chunks)}", end="\r")
        time.sleep(0.1)  # tránh rate limit của free tier

    print()
    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """
    Lưu chunks vào vector store đã chọn.
    """
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [f"{c['metadata']['source']}_chunk_{c['metadata']['chunk_index']}" for c in chunks]
    collection.upsert(
        ids=ids,
        documents=[c["content"] for c in chunks],
        embeddings=[c["embedding"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )


def run_pipeline():
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\n✓ Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"✓ Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"✓ Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("✓ Indexed to vector store")


if __name__ == "__main__":
    run_pipeline()
