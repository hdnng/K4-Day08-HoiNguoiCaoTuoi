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
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents():
    """
    Upload toàn bộ markdown documents lên PageIndex.
    """
    from pageindex.client import PageIndexClient
    import json
    from fpdf import FPDF
    
    client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    doc_ids = []
    
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        # Convert markdown to PDF simply using fpdf2
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=12)
        # Avoid unicode issues by ignoring non-ascii chars for this simple conversion
        text = md_file.read_text(encoding="utf-8").encode("ascii", "ignore").decode("ascii")
        pdf.multi_cell(0, 10, text)
        
        pdf_path = md_file.with_suffix(".pdf")
        pdf.output(str(pdf_path))
        
        try:
            resp = client.submit_document(str(pdf_path))
            doc_id = resp.get("doc_id") or resp.get("id")
            if doc_id:
                doc_ids.append(doc_id)
                print(f"  ✓ Uploaded: {md_file.name} -> {doc_id}")
        except Exception as e:
            print(f"  ❌ Error uploading {md_file.name}: {e}")
            
    # Save doc_ids for querying later
    with open("pageindex_docs.json", "w") as f:
        json.dump(doc_ids, f)


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
    from pageindex.client import PageIndexClient
    import time
    import json
    
    # Check if we have uploaded documents
    doc_id = "test_doc_id"
    if Path("pageindex_docs.json").exists():
        doc_ids = json.loads(Path("pageindex_docs.json").read_text())
        if doc_ids:
            doc_id = doc_ids[0] # querying the first document as a fallback
            
    client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    
    try:
        resp = client.submit_query(doc_id=doc_id, query=query)
        retrieval_id = resp.get("retrieval_id") or resp.get("id")
        
        # Poll cho đến khi status == "completed"
        retrieval = {}
        for _ in range(15):
            retrieval = client.get_retrieval(retrieval_id)
            if retrieval.get("status") == "completed":
                break
            time.sleep(1)
            
        # Parse retrieval["retrieved_nodes"]
        results = []
        score = 1.0 # Base score for first result
        
        for node in retrieval.get("retrieved_nodes", [])[:2]:
            for group in node.get("relevant_contents", []):
                for item in group:
                    results.append({
                        "content": item.get("relevant_content", ""),
                        "score": round(score, 4),
                        "metadata": {"section": item.get("section_title", "")},
                        "source": "pageindex",
                    })
                    score = max(0.1, score - 0.1) # Decrease score slightly for subsequent items
                    
        return results[:top_k]
    except Exception as e:
        print(f"PageIndex error: {e}")
        return []


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
