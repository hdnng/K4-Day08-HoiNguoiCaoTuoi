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
| OOD-01 | Chờ Task 8 | Chờ Task 8 | `[]` hoặc không đủ evidence | Chưa chạy | |
| OOD-02 | Chờ Task 8 | Chờ Task 8 | `[]` hoặc không đủ evidence | Chưa chạy | |
| OOD-03 | Chờ Task 8 | Chờ Task 8 | `[]` hoặc không đủ evidence | Chưa chạy | |
| OOD-04 | Chờ Task 8 | Chờ Task 8 | `[]` hoặc không đủ evidence | Chưa chạy | |
| OOD-05 | Chờ Task 8 | Chờ Task 8 | `[]` hoặc không đủ evidence | Chưa chạy | |
| IN-01 | Chờ Task 8 | Không | Kết quả trả hàng/hoàn tiền | Chưa chạy | |

## Tiêu chí pass

1. Các query OOD không làm hệ thống lỗi.
2. Không có tài liệu TMĐT không liên quan được xem là evidence cho query OOD.
3. Query IN-01 vẫn trả đúng tài liệu chính sách trả hàng/hoàn tiền.

> Ghi chú: Checkpoint 3 chỉ kiểm thử sự sẵn sàng của PageIndex. Logic tự động chuyển từ hybrid retrieval sang PageIndex nằm ở Task 9 (Checkpoint 4).
