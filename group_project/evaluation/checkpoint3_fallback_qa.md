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
| OOD-01 | Có | Không | `[]` hoặc không đủ evidence | Đạt | Query “Thủ đô của Canada là gì?” trả `[]`. |
| OOD-02 | Có | Không | `[]` hoặc không đủ evidence | Đạt | Query “Cách nấu phở bò tại nhà?” trả `[]`. |
| OOD-03 | Có | Không | `[]` hoặc không đủ evidence | Đạt | Query “Viết thuật toán quicksort bằng Python.” trả `[]`. |
| OOD-04 | Có | Không | `[]` hoặc không đủ evidence | Đạt | Query “Dự đoán giá Bitcoin tuần tới.” trả `[]`. |
| OOD-05 | Có | Không | `[]` hoặc không đủ evidence | Đạt | Query `xyzabc123nonsense` trả `[]`. |
| IN-01 | Có | Không | Kết quả trả hàng/hoàn tiền | Đạt | Trả các đoạn về thời hạn trả hàng/hoàn tiền từ tài liệu Return/Refund. |

### Kết quả kiểm tra kỹ thuật

- `pytest tests/test_individual.py::TestTask7 tests/test_individual.py::TestTask8 -v`: **5 passed**.
- Task 7 đã gộp kết quả RRF và đáp ứng các kiểm thử về kiểu trả về, `top_k` và trường `score`.
- Task 8 có hàm `pageindex_search()` trả về đúng cấu trúc theo kiểm thử.
- Đã cấu hình `PAGEINDEX_API_KEY`; tài khoản hiện có 9 document đã upload, xử lý xong và sẵn sàng retrieval.
- Kiểm thử PageIndex: câu hỏi về chính sách bảo mật trả nội dung phù hợp với `source: "pageindex"`; OOD-01 trả `[]`, không có evidence lạc đề.
- OOD-02 đến OOD-05 đều trả `[]`, xác nhận không có evidence TMĐT lạc đề cho các query ngoài domain đã thử.
- Đã sửa `pageindex_search()` để kiểm tra toàn bộ document ID đã upload. IN-01 trả đúng thời hạn trả hàng/hoàn tiền từ tài liệu Return/Refund.
- Task 8 tạo PDF tạm trong `data/_tmp_pdf/` và lưu ID document tại `pageindex_docs.json`; cả hai đều được Git bỏ qua vì là trạng thái chạy cục bộ.
- Task 9 chưa được hoàn thiện, vì vậy chưa thể xác minh việc pipeline tự động chuyển từ hybrid retrieval sang PageIndex.

## Tiêu chí pass

1. Các query OOD không làm hệ thống lỗi.
2. Không có tài liệu TMĐT không liên quan được xem là evidence cho query OOD.
3. Query IN-01 vẫn trả đúng tài liệu chính sách trả hàng/hoàn tiền.

> Ghi chú: Checkpoint 3 chỉ kiểm thử sự sẵn sàng của PageIndex. Logic tự động chuyển từ hybrid retrieval sang PageIndex nằm ở Task 9 (Checkpoint 4).
