"""
Checkpoint 4 QA — Rà soát định dạng trích dẫn (citation format).

Vai trò: Role 4 — Evaluation & QA Engineer

Task 10 (src/task10_generation.py) yêu cầu LLM chèn citation dạng
"[Nguồn, Năm]" (ví dụ: [Returns Policy, 2026]) ngay sau mỗi khẳng định
(xem SYSTEM_PROMPT trong task10_generation.py). Test tự động trong
tests/test_individual.py chỉ kiểm tra structure (answer là string,
format_context có chứa source) — KHÔNG kiểm tra citation có đúng format
hay không. Script này lấp khoảng trống đó bằng cách chạy generate_with_citation()
trên golden dataset và audit citation pattern trong câu trả lời thật.

Cách chạy:
    python -m group_project.evaluation.check_citation_format
"""

import json
import re
from pathlib import Path

from src.task10_generation import generate_with_citation

GOLDEN_DATASET = Path(__file__).parent / "golden_dataset.json"
REPORT_PATH = Path(__file__).parent / "citation_format_report.md"

# Citation hợp lệ theo SYSTEM_PROMPT: [Tên nguồn, Năm]
# Ví dụ pass: [Returns Policy, 2026], [Payment Methods Overview, 2024]
# Ví dụ fail: (Returns Policy, 2026), [Returns Policy], [1], không có citation
CITATION_PATTERN = re.compile(r"\[[^\[\]]+,\s*\d{4}\]")

NO_EVIDENCE_PHRASE = "Tôi không thể xác minh thông tin này từ nguồn hiện có"


def audit_answer(answer: str) -> dict:
    """Kiểm tra 1 câu trả lời có tuân thủ định dạng citation không."""
    citations = CITATION_PATTERN.findall(answer)
    is_no_evidence = NO_EVIDENCE_PHRASE in answer

    # Câu trả lời "không đủ evidence" được miễn yêu cầu citation.
    has_valid_citation = bool(citations) or is_no_evidence

    return {
        "citations_found": citations,
        "citation_count": len(citations),
        "is_no_evidence_response": is_no_evidence,
        "pass": has_valid_citation,
    }


def run_audit():
    golden = json.loads(GOLDEN_DATASET.read_text(encoding="utf-8"))

    rows = []
    for item in golden:
        query = item["question"]
        result = generate_with_citation(query)
        audit = audit_answer(result["answer"])
        rows.append({"query": query, "answer": result["answer"], **audit})

    passed = sum(1 for r in rows if r["pass"])
    total = len(rows)

    lines = [
        "# Checkpoint 4 — Citation Format QA",
        "",
        "**Vai trò:** Role 4 — Evaluation & QA Engineer",
        "**Mục tiêu:** Rà soát định dạng trích dẫn nguồn (citation format) trong câu trả lời từ LLM (Task 10).",
        "",
        f"**Kết quả tổng quan: {passed}/{total} câu trả lời đúng định dạng citation.**",
        "",
        "## Quy tắc kiểm tra",
        "",
        "- Citation hợp lệ: `[Tên nguồn, Năm]`, ví dụ `[Returns Policy, 2026]`.",
        "- Câu trả lời dạng \"Tôi không thể xác minh thông tin này từ nguồn hiện có\" được miễn citation (không có evidence để trích).",
        "- Câu trả lời có nội dung nhưng KHÔNG có citation nào → FAIL.",
        "",
        "## Chi tiết từng câu hỏi",
        "",
        "| Query | Số citation | Citation tìm thấy | Không có evidence? | Kết quả |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        citations_display = ", ".join(r["citations_found"]) if r["citations_found"] else "—"
        status = "PASS" if r["pass"] else "FAIL"
        lines.append(
            f"| {r['query']} | {r['citation_count']} | {citations_display} | "
            f"{'Có' if r['is_no_evidence_response'] else 'Không'} | {status} |"
        )

    lines += [
        "",
        "## Câu trả lời đầy đủ (để đối chiếu thủ công)",
        "",
    ]
    for r in rows:
        lines.append(f"### {r['query']}")
        lines.append("")
        lines.append(f"> {r['answer']}")
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Audit xong: {passed}/{total} PASS. Xem chi tiết tại {REPORT_PATH}")


if __name__ == "__main__":
    run_audit()
