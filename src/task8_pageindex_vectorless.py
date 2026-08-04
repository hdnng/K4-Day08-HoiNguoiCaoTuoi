"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Hướng dẫn:
    1. Đăng ký account tại pageindex.ai
    2. Lấy API key
    3. Upload documents
    4. Query sử dụng PageIndex API

Lưu ý: API `/retrieval` của PageIndex hiện đã deprecated (vẫn hoạt động, nhưng response
có field "deprecation" cảnh báo) và trả kết quả trong "retrieved_nodes" — mỗi node có
"relevant_contents": list[list[{section_title, relevant_content}]]. In response thật ra
(json.dumps(...)) trước khi viết logic parse, đừng đoán schema từ ví dụ code cũ.
"""

import os
import json
import time
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
DOC_IDS_FILE = Path(__file__).parent.parent / "pageindex_docs.json"
TEMP_PDF_DIR = Path(__file__).parent.parent / "data" / "_tmp_pdf"
PAGEINDEX_API_URL = "https://api.pageindex.ai"
REQUEST_TIMEOUT_SECONDS = 15


def upload_documents():
    """
    Upload toàn bộ markdown documents lên PageIndex.
    """
    from pageindex.client import PageIndexClient
    from fpdf import FPDF
    
    client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    documents = []
    TEMP_PDF_DIR.mkdir(parents=True, exist_ok=True)
    
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        # Convert markdown to PDF simply using fpdf2
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=12)
        # Avoid unicode issues by ignoring non-ascii chars for this simple conversion
        text = md_file.read_text(encoding="utf-8").encode("ascii", "ignore").decode("ascii")
        pdf.multi_cell(0, 10, text)
        
        pdf_path = TEMP_PDF_DIR / f"{md_file.stem}.pdf"
        pdf.output(str(pdf_path))
        
        try:
            resp = client.submit_document(str(pdf_path))
            doc_id = resp.get("doc_id") or resp.get("id")
            if doc_id:
                documents.append({"doc_id": doc_id, "source": md_file.name})
                print(f"  ✓ Uploaded: {md_file.name} -> {doc_id}")
        except Exception as e:
            print(f"  ❌ Error uploading {md_file.name}: {e}")
            
    # Save document IDs and sources for querying later.  The file is ignored by
    # Git because it is runtime state tied to one PageIndex workspace.
    DOC_IDS_FILE.write_text(json.dumps(documents, ensure_ascii=False), encoding="utf-8")


def _load_uploaded_documents() -> list[dict]:
    """Load both the current metadata format and the older list-of-ID format."""
    if not DOC_IDS_FILE.exists():
        return []

    saved = json.loads(DOC_IDS_FILE.read_text(encoding="utf-8"))
    if not isinstance(saved, list):
        return []
    markdown_files = sorted(STANDARDIZED_DIR.rglob("*.md"))
    documents = []
    for index, item in enumerate(saved):
        if isinstance(item, dict):
            doc_id = item.get("doc_id")
            if doc_id:
                documents.append(item)
        elif item:
            # Earlier uploads stored only a list of IDs.  They were uploaded in
            # the same order as rglob("*.md"), so restore a readable source label.
            source = markdown_files[index].name if index < len(markdown_files) else item
            documents.append({"doc_id": item, "source": source})
    return documents


def _parse_retrieval(retrieval: dict, document: dict, start_score: float) -> list[dict]:
    """Normalize the legacy retrieval response into the project result schema."""
    results = []
    score = start_score
    for node in retrieval.get("retrieved_nodes", []):
        contents = node.get("relevant_contents", [])
        # Legacy responses have existed in both list[dict] and list[list[dict]] forms.
        if contents and isinstance(contents[0], dict):
            contents = [contents]
        for group in contents:
            for item in group:
                content = item.get("relevant_content", "").strip()
                if not content:
                    continue
                results.append(
                    {
                        "content": content,
                        "score": round(score, 4),
                        "metadata": {
                            "section": item.get("section_title") or node.get("title", ""),
                            "doc_id": document["doc_id"],
                            "source": document.get("source", document["doc_id"]),
                        },
                        "source": "pageindex",
                    }
                )
                score = max(0.1, score - 0.1)
    return results


def _run_retrieval(doc_id: str, query: str) -> dict:
    """Submit and poll legacy retrieval with bounded network timeouts."""
    headers = {"api_key": PAGEINDEX_API_KEY}
    submitted = requests.post(
        f"{PAGEINDEX_API_URL}/retrieval/",
        headers=headers,
        json={"doc_id": doc_id, "query": query, "thinking": False},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    submitted.raise_for_status()
    retrieval_id = submitted.json().get("retrieval_id")
    if not retrieval_id:
        return {}

    for _ in range(12):
        response = requests.get(
            f"{PAGEINDEX_API_URL}/retrieval/{retrieval_id}/",
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        retrieval = response.json()
        if retrieval.get("status") == "completed":
            return retrieval
        time.sleep(1)
    return {}


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'   # Đánh dấu nguồn retrieval
        }
    """
    if not PAGEINDEX_API_KEY:
        print("PageIndex error: PAGEINDEX_API_KEY chưa được cấu hình.")
        return []

    documents = _load_uploaded_documents()
    if not documents:
        print("PageIndex error: Chưa có document ID. Hãy chạy upload_documents() trước.")
        return []

    from pageindex.client import PageIndexClient
    client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    results = []

    # Query every uploaded document.  The old implementation queried only the
    # first ID, which made return/refund questions fail when that document was
    # the Privacy Policy.
    for document in documents:
        if len(results) >= top_k:
            break
        doc_id = document["doc_id"]
        try:
            if not client.is_retrieval_ready(doc_id):
                continue

            retrieval = _run_retrieval(doc_id, query)
            if retrieval:
                results.extend(_parse_retrieval(retrieval, document, 1.0 - len(results) * 0.1))
        except Exception as error:
            print(f"PageIndex warning ({doc_id}): {error}")

    return results[:top_k]


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("⚠ Hãy set PAGEINDEX_API_KEY trong file .env")
        print("  Đăng ký tại: https://pageindex.ai/")
    else:
        print("Uploading documents...")
        upload_documents()

        print("\nTest query:")
        results = pageindex_search("danh sách sản phẩm cấm đăng bán", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")
