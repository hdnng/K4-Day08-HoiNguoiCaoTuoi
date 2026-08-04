# RAG Evaluation Results

## Trạng thái

**Sẵn sàng chạy — chưa có điểm RAGAS thực tế.**

Runner đã được chuẩn bị cho 20 câu golden dataset và hai cấu hình A/B. Lần chạy gần nhất đã xác nhận dataset hợp lệ nhưng dừng trước khi gọi mô hình do `.env` chưa có một trong các biến `GEMINI_API_KEY`, `OPENAI_API_KEY` hoặc `OPENROUTER_API_KEY`.

Không điền điểm thủ công vào báo cáo này. Sau khi cấu hình key, lệnh bên dưới sẽ chạy RAGAS và tự ghi đè file bằng bảng điểm thực tế, bottom-3 và đề xuất cải tiến.

```powershell
python -m group_project.evaluation.eval_pipeline
```

## Thiết kế đánh giá

- Framework: RAGAS 0.1.21.
- Golden dataset: 20 câu hỏi, bám theo 9 tài liệu chính sách đã chuẩn hóa.
- Config A: hybrid retrieval (semantic + BM25), RRF và reranking.
- Config B: hybrid retrieval (semantic + BM25), RRF, không reranking.
- Metrics: Faithfulness, Answer Relevance, Context Recall, Context Precision.

## Điều kiện trước khi chạy

1. Đặt API key LLM trong `.env` (Gemini, OpenAI hoặc OpenRouter).
2. Nếu dùng Gemini, cài adapter: `pip install langchain-google-genai`.
3. Đảm bảo Chroma index đã được tạo và Task 9/10 chạy được với API key đó.
