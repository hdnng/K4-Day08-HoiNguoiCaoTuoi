# RAG Evaluation Results

## Framework và phạm vi

- Framework: **RAGAS 0.1.21**
- Golden dataset: **20** câu hỏi bám theo 9 tài liệu trong corpus.
- Metrics: Faithfulness, Answer Relevance, Context Recall, Context Precision.

## Overall Scores

| Metric | Config A: Hybrid + rerank | Config B: Hybrid không rerank | Δ (A - B) |
|---|---:|---:|---:|
| Faithfulness | 0.9062 | 0.9750 | -0.0688 |
| Answer Relevance | 0.8553 | 0.8592 | -0.0039 |
| Context Recall | 1.0000 | 1.0000 | +0.0000 |
| Context Precision | 0.8683 | 0.8933 | -0.0250 |
| **Average** | **0.9074** | **0.9319** | **-0.0245** |

## A/B Comparison Analysis

- **Config A — Hybrid + RRF rerank:** Semantic retrieval và BM25 được gộp bằng RRF, sau đó rerank.
- **Config B — Hybrid không rerank:** Semantic retrieval và BM25 được gộp bằng RRF, không áp dụng bước rerank.
- **Kết luận:** Config B — Hybrid không rerank có điểm trung bình cao hơn trong lần chạy này. Chênh lệch cần được đọc cùng bottom-3 để xác định lỗi retrieval hay generation.

## Worst Performers (Bottom 3)

| # | Config | Question | Faithfulness | Relevance | Recall | Precision | Failure stage |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | Config A — Hybrid + RRF rerank | Khi nào người mua có thể hủy đơn Shopee? | 0.2500 | 0.8413 | 1.0000 | 1.0000 | generation |
| 2 | Config A — Hybrid + RRF rerank | Shopee thường phản hồi yêu cầu trả hàng/hoàn tiền trong bao lâu? | 1.0000 | 0.8611 | 1.0000 | 0.4500 | generation |
| 3 | Config B — Hybrid không rerank | Shopee thường phản hồi yêu cầu trả hàng/hoàn tiền trong bao lâu? | 1.0000 | 0.8611 | 1.0000 | 0.4500 | generation |

## Recommendations

1. **Calibrate retrieval threshold:** dùng các câu có Context Recall thấp để điều chỉnh `SCORE_THRESHOLD` và `top_k`.
2. **Cải thiện metadata/chunking:** tách rõ tiêu đề chính sách và điều khoản thời hạn để tăng Context Precision.
3. **Củng cố prompt citation:** kiểm tra các câu có Faithfulness thấp và yêu cầu LLM chỉ khẳng định thông tin hiện diện trong context.

## Reproduce

```powershell
python -m group_project.evaluation.eval_pipeline
```
