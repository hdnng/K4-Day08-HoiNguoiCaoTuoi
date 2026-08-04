# Checkpoint 4 — Citation Format QA

**Vai trò:** Role 4 — Evaluation & QA Engineer
**Mục tiêu:** Rà soát định dạng trích dẫn nguồn (citation format) trong câu trả lời từ LLM (Task 10).

**Kết quả tổng quan: 2/3 câu trả lời đúng định dạng citation.**

## Quy tắc kiểm tra

- Citation hợp lệ: `[Tên nguồn, Năm]`, ví dụ `[Returns Policy, 2026]`.
- Câu trả lời dạng "Tôi không thể xác minh thông tin này từ nguồn hiện có" được miễn citation (không có evidence để trích).
- Câu trả lời có nội dung nhưng KHÔNG có citation nào → FAIL.

## Chi tiết từng câu hỏi

| Query | Số citation | Citation tìm thấy | Không có evidence? | Kết quả |
|---|---|---|---|---|
| Người mua có thể yêu cầu trả hàng/hoàn tiền trong thời hạn bao lâu sau khi nhận hàng? | 0 | — | Không | FAIL |
| Shopee hỗ trợ những phương thức thanh toán nào? | 1 | [Document 1, 2026] | Có | PASS |
| Người bán không được đăng bán những sản phẩm nào? | 0 | — | Có | PASS |

## Phát hiện & nguyên nhân gốc

**Lỗi:** LLM trích dẫn theo dạng `[Document 1, Document 5]` (số thứ tự document) thay vì
`[Tên nguồn, Năm]` như SYSTEM_PROMPT yêu cầu (ví dụ mẫu: `[Returns Policy, 2026]`).

**Nguyên nhân:** `format_context()` trong `src/task10_generation.py` (dòng 103-111) gắn
nhãn mỗi chunk là `[Document {i} | Source: {source} | Type: {doc_type}]`. LLM nhìn thấy
nhãn nổi bật nhất trong context là "Document N" nên bắt chước lại đúng pattern đó khi
trích dẫn, thay vì dùng "Source" (tên file) kèm năm như ví dụ trong SYSTEM_PROMPT.
Hai phần hướng dẫn (system prompt vs context label) đang không nhất quán với nhau.

**Đề xuất sửa (cho Role 3 — người phụ trách Task 10):**
- Đổi nhãn trong `format_context()` để nhấn mạnh "Source" thay vì "Document N", ví dụ:
  `[Source: {source} ({doc_type})]` — bỏ số thứ tự "Document N" để LLM không bám vào đó.
- Cân nhắc thêm field "year"/"document_version" từ metadata (đã có sẵn trong frontmatter
  YAML của các file .md, ví dụ `retrieved_at: 2026-08-03`) vào label, để LLM có năm thật
  để trích dẫn thay vì tự bịa "2026" hoặc ghi "not-stated".

## Câu trả lời đầy đủ (để đối chiếu thủ công)

### Người mua có thể yêu cầu trả hàng/hoàn tiền trong thời hạn bao lâu sau khi nhận hàng?

> Thời hạn người mua có thể yêu cầu trả hàng/hoàn tiền sau khi nhận hàng khác nhau tùy thuộc vào nền tảng và loại sản phẩm:

**Đối với Shopee:**
*   **Thực phẩm tươi sống/đông lạnh:** trong vòng 24 giờ kể từ khi đơn hàng ở trạng thái "Giao hàng thành công" (không áp dụng cho khiếu nại "Không nhận được hàng") [Document 1, Document 5].
*   **Đơn hàng do Người bán tự vận chuyển:** trong vòng 15 ngày kể từ khi người mua bấm "Đã nhận được hàng", hoặc 20 ngày kể từ "Lấy hàng thành công" nếu người mua chưa xác nhận đã nhận hàng [Document 1, Document 5].
*   **Các đơn hàng khác:** trong vòng 15 ngày kể từ khi đơn hàng ở trạng thái "Giao hàng thành công" [Document 1, Document 5].

**Đối với Lazada:**
*   Khách hàng có 30 ngày để khởi tạo yêu cầu trả hàng hoặc hoàn tiền cho đơn hàng LazMall sau khi hàng đã được giao, ngay cả sau khi xác nhận đơn hàng hoặc nhấp vào nút "Đã nhận hàng" [Document 2, Document 4].

### Shopee hỗ trợ những phương thức thanh toán nào?

> Tôi không thể xác minh thông tin này từ nguồn hiện có. Các tài liệu được cung cấp có đề cập đến việc Shopee có thể hoàn tiền qua phương thức thanh toán ban đầu hoặc áp dụng phương thức thay thế như phiếu mua hàng [Document 1, 2026], và việc hoàn trả tiền thanh toán cùng Shopee Xu khi đơn hàng đủ điều kiện hoàn tiền [Document 5, not-stated]. Tuy nhiên, không có tài liệu nào liệt kê cụ thể các phương thức thanh toán mà Shopee hỗ trợ.

### Người bán không được đăng bán những sản phẩm nào?

> Tôi không thể xác minh thông tin này từ nguồn hiện có. Context được cung cấp chủ yếu đề cập đến các sản phẩm không áp dụng đổi trả tại Decathlon hoặc các điều kiện vận chuyển của Shopee, chứ không liệt kê cụ thể những sản phẩm mà người bán không được phép đăng bán.
