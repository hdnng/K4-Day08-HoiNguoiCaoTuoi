# Checkpoint 3 — Fallback QA

**Vai trò:** Role 4 — Evaluation & QA Engineer  
**Mục tiêu:** Kiểm tra hệ thống không sử dụng kết quả TMĐT lạc đề khi câu hỏi nằm ngoài knowledge base.

## Tiền điều kiện

- Role 2 đã hoàn thiện `rerank_rrf()` trong `src/task7_reranking.py`.
- Role 3 đã hoàn thiện `pageindex_search()` trong `src/task8_pageindex_vectorless.py`.


## Bộ câu hỏi kiểm thử

| ID | Câu hỏi | Loại | Kỳ vọng |
|---|---|---|---|
| OOD-01 | Thủ đô của Canada là gì? | Ngoài domain | Không trả lời từ tài liệu TMĐT; PageIndex không có evidence thì trả rỗng. |
| OOD-02 | Cách nấu phở bò tại nhà? | Ngoài domain | Không trả lời từ tài liệu TMĐT; PageIndex không có evidence thì trả rỗng. |
| OOD-03 | Viết thuật toán quicksort bằng Python. | Ngoài domain | Không trả lời từ tài liệu TMĐT; PageIndex không có evidence thì trả rỗng. |
| OOD-04 | Dự đoán giá Bitcoin tuần tới. | Ngoài domain | Không trả lời từ tài liệu TMĐT; PageIndex không có evidence thì trả rỗng. |
| OOD-05 | xyzabc123nonsense | Nhiễu | Không có kết quả phù hợp và không lỗi. |
| IN-01 | Thời hạn trả hàng Shopee là bao lâu? | Trong domain | Trả tài liệu về trả hàng/hoàn tiền, không fallback. |

## Cách chạy sau khi Task 8 hoàn thiện

```powershell
python -m src.task8_pageindex_vectorless
```

Chạy từng câu OOD qua `pageindex_search(query, top_k=3)` và ghi kết quả vào bảng dưới.

## Kết quả QA

| ID | PageIndex được gọi | Kết quả có lạc đề | Kết quả mong đợi | Trạng thái | Ghi chú |
|---|---|---|---|---|---|
| OOD-01 | Không | Chưa đánh giá | `[]` hoặc không đủ evidence | Bị chặn credit | Upload bị PageIndex từ chối: `InsufficientCredits`. |
| OOD-02 | Không | Chưa đánh giá | `[]` hoặc không đủ evidence | Bị chặn credit | Upload bị PageIndex từ chối: `InsufficientCredits`. |
| OOD-03 | Không | Chưa đánh giá | `[]` hoặc không đủ evidence | Bị chặn credit | Upload bị PageIndex từ chối: `InsufficientCredits`. |
| OOD-04 | Không | Chưa đánh giá | `[]` hoặc không đủ evidence | Bị chặn credit | Upload bị PageIndex từ chối: `InsufficientCredits`. |
| OOD-05 | Không | Chưa đánh giá | `[]` hoặc không đủ evidence | Bị chặn credit | Upload bị PageIndex từ chối: `InsufficientCredits`. |
| IN-01 | Không | Chưa đánh giá | Kết quả trả hàng/hoàn tiền | Bị chặn credit | Không có document ID vì upload thất bại. |

### Kết quả kiểm tra kỹ thuật

- `pytest tests/test_individual.py::TestTask7 tests/test_individual.py::TestTask8 -v`: **5 passed**.
- Task 7 đã gộp kết quả RRF và đáp ứng các kiểm thử về kiểu trả về, `top_k` và trường `score`.
- Task 8 có hàm `pageindex_search()` trả về đúng cấu trúc theo kiểm thử.
- Đã cấu hình và xác thực `PAGEINDEX_API_KEY`; PageIndex từ chối upload cả 9 tài liệu với lỗi `InsufficientCredits`. Query sau đó không chạy được vì không có document ID hợp lệ.
- Task 8 tạo PDF tạm trong `data/standardized/` và `pageindex_docs.json` trong lúc upload; các tệp tạm đã được xóa sau khi test.
- Task 9 chưa được hoàn thiện, vì vậy chưa thể xác minh việc pipeline tự động chuyển từ hybrid retrieval sang PageIndex.

## Tiêu chí pass

1. Các query OOD không làm hệ thống lỗi.
2. Không có tài liệu TMĐT không liên quan được xem là evidence cho query OOD.
3. Query IN-01 vẫn trả đúng tài liệu chính sách trả hàng/hoàn tiền.

> Ghi chú: Checkpoint 3 chỉ kiểm thử sự sẵn sàng của PageIndex. Logic tự động chuyển từ hybrid retrieval sang PageIndex nằm ở Task 9 (Checkpoint 4).
