"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

import re
from pathlib import Path

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"

# Corpus được nạp lười khi có truy vấn đầu tiên để module có thể được import
# trước khi Task 3 hoàn thành.
CORPUS: list[dict] = []  # List of {'content': str, 'metadata': dict}
_BM25_INDEX = None


# Một số query demo/test dùng tiếng Anh, còn bộ tài liệu của bài lab là tiếng
# Việt. Bổ sung các từ đồng nghĩa phổ biến trước khi chạy BM25 giúp lexical
# search vẫn tìm đúng từ khóa mà không cần embedding hoặc gọi API.
QUERY_ALIASES = {
    "payment": ("thanh", "toán"),
    "methods": ("phương", "thức"),
    "return": ("trả", "hàng"),
    "refund": ("hoàn", "tiền"),
    "evidence": ("bằng", "chứng"),
    "seller": ("người", "bán"),
    "listing": ("đăng", "bán"),
    "regulations": ("quy", "định"),
    "order": ("đơn", "hàng"),
    "tracking": ("theo", "dõi"),
    "guide": ("hướng", "dẫn"),
}


def tokenize(text: str, expand_query: bool = False) -> list[str]:
    """Tách từ, bỏ dấu câu và giữ được chữ tiếng Việt/tiếng Anh."""
    tokens = re.findall(r"[^\W_]+", text.lower(), flags=re.UNICODE)
    if not expand_query:
        return tokens

    expanded = list(tokens)
    for token in tokens:
        expanded.extend(QUERY_ALIASES.get(token, ()))
    return expanded


def load_corpus() -> list[dict]:
    """Đọc Markdown đã chuẩn hoá và gắn metadata nguồn cho từng tài liệu."""
    if not STANDARDIZED_DIR.exists():
        return []

    documents = []
    for filepath in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = filepath.read_text(encoding="utf-8").strip()
        if not content:
            continue

        relative_path = filepath.relative_to(STANDARDIZED_DIR)
        documents.append(
            {
                "content": content,
                "metadata": {
                    "source": str(relative_path).replace("\\", "/"),
                    "type": relative_path.parts[0] if len(relative_path.parts) > 1 else "unknown",
                },
            }
        )
    return documents


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}
    """
    if not corpus:
        return None

    from rank_bm25 import BM25Okapi

    tokenized_corpus = [tokenize(doc["content"]) for doc in corpus]
    return BM25Okapi(tokenized_corpus, k1=1.5, b=0.75)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    global CORPUS, _BM25_INDEX

    if not query or top_k <= 0:
        return []

    if not CORPUS:
        CORPUS = load_corpus()
        _BM25_INDEX = build_bm25_index(CORPUS)

    if _BM25_INDEX is None:
        return []

    query_tokens = tokenize(query, expand_query=True)
    if not query_tokens:
        return []

    scores = _BM25_INDEX.get_scores(query_tokens)
    ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)

    results = []
    for index, score in ranked:
        if score <= 0:
            break
        document = CORPUS[index]
        results.append(
            {
                "content": document["content"],
                "score": float(score),
                "metadata": document.get("metadata", {}),
            }
        )
        if len(results) >= top_k:
            break
    return results


if __name__ == "__main__":
    # Test
    results = lexical_search("phương thức thanh toán shopee", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
