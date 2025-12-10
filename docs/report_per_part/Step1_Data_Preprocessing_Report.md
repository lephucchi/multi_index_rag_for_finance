# BÁO CÁO CHI TIẾT BƯỚC 1: TIỀN XỬ LÝ DỮ LIỆU (DATA PREPROCESSING)
**Dự án**: A Semantic-Router Multi-Index Retrieval-Augmented Generation System for Vietnamese Financial Data and the Economic–Regulatory Framework  
**Ngày báo cáo**: 01/12/2025  
**Người thực hiện**: Antigravity (AI Assistant) & User

---

## 1. TỔNG QUAN (EXECUTIVE SUMMARY)

Bước 1 của dự án tập trung vào việc xây dựng nền tảng dữ liệu chất lượng cao cho hệ thống RAG (Retrieval-Augmented Generation). Mục tiêu cốt lõi là chuyển đổi dữ liệu thô (raw data) từ ba nguồn thông tin không đồng nhất – **Tài chính (Finance)**, **Pháp lý (Legal)**, và **Tin tức (News)** – thành các vector documents được chuẩn hóa, phân mảnh thông minh (smart chunking) và giàu ngữ nghĩa (semantically rich).

Quá trình này đóng vai trò quyết định đến độ chính xác của việc truy xuất thông tin (retrieval accuracy) và khả năng sinh lời giải (generation capability) của các mô hình ngôn ngữ lớn (LLMs) trong các bước tiếp theo.

---

## 2. MÔ TẢ DỮ LIỆU ĐẦU VÀO (INPUT DATA)

Hệ thống xử lý ba tập dữ liệu chính với đặc thù riêng biệt:

### 2.1. Dữ liệu Tài chính (`finance_index.csv`)
- **Đặc điểm**: Dữ liệu có cấu trúc cao (structured data), chứa thông tin chi tiết về các công ty niêm yết.
- **Kích thước**: ~1,720 công ty.
- **Thách thức**: Số lượng trường thông tin lớn (27 trường), bao gồm cả dữ liệu định lượng (chỉ số tài chính) và định tính (mô tả công ty).
- **Các trường chính**: `ticker`, `company_name`, `overview`, `profile`, `shareholders`, `financial_ratios` (P/E, EPS, ROA, ROE...).

### 2.2. Dữ liệu Pháp lý (`laws_index.csv`)
- **Đặc điểm**: Dữ liệu văn bản quy phạm pháp luật, có cấu trúc phân cấp chặt chẽ (Luật -> Chương -> Điều -> Khoản).
- **Kích thước**: 5,012 điều luật từ nhiều bộ luật (Luật Doanh nghiệp, Luật Chứng khoán, Luật Đầu tư...).
- **Thách thức**: Độ dài văn bản biến thiên lớn (từ vài dòng đến hàng chục trang), ngôn ngữ pháp lý phức tạp, yêu cầu độ chính xác tuyệt đối về trích dẫn.

### 2.3. Dữ liệu Tin tức (`news_index.csv`)
- **Đặc điểm**: Dữ liệu phi cấu trúc (unstructured), biến động theo thời gian (time-series nature).
- **Kích thước**: 12,685 bài báo.
- **Thách thức**: Nhiễu thông tin cao, cần trích xuất yếu tố thời gian để phục vụ truy vấn theo thời điểm (temporal queries).

---

## 3. PHƯƠNG PHÁP LUẬN & CÔNG NGHỆ (METHODOLOGY & TECHNOLOGY)

### 3.1. Công nghệ sử dụng
- **Ngôn ngữ lập trình**: Python 3.x
- **Thư viện xử lý dữ liệu**: Pandas (thao tác DataFrame hiệu năng cao), JSON (xử lý metadata).
- **Xử lý văn bản**: Regular Expressions (Regex) cho việc làm sạch và tách câu.
- **Định dạng lưu trữ**: CSV (UTF-8 with BOM) cho khả năng tương thích rộng, JSON cho metadata phức tạp.

### 3.2. Quy trình xử lý (Processing Pipeline)

Quy trình được thiết kế theo mô hình ETL (Extract - Transform - Load) tùy biến cho RAG:

#### **Giai đoạn 1: Làm sạch & Chuẩn hóa (Cleaning & Normalization)**
- **Unicode Normalization**: Chuyển đổi toàn bộ văn bản về chuẩn Unicode NFC để đảm bảo tính nhất quán trong hiển thị và tìm kiếm tiếng Việt.
- **Noise Removal**: Loại bỏ các ký tự thừa, khoảng trắng dư, và các thẻ HTML/format lỗi từ quá trình cào dữ liệu.
- **Data Imputation**: Xử lý các giá trị thiếu (NULL/NaN) bằng các placeholder ngữ nghĩa (ví dụ: "Chưa có thông tin") thay vì loại bỏ, giúp giữ nguyên ngữ cảnh.

#### **Giai đoạn 2: Kỹ thuật Phân mảnh Thông minh (Smart Chunking Algorithm)**
Đây là trái tim của bước tiền xử lý. Thay vì cắt văn bản theo độ dài cố định (fixed-size chunking) gây mất ngữ nghĩa, chúng tôi áp dụng thuật toán **Semantic-Aware Chunking**:

1.  **Mục tiêu**: Tạo ra các đoạn văn bản (chunks) có độ dài từ 500 đến 1000 tokens.
2.  **Cơ chế hoạt động**:
    *   **Ưu tiên 1 - Ngắt đoạn (Paragraph Split)**: Tách văn bản tại các dấu xuống dòng kép (`\n\n`). Đây là ranh giới ngữ nghĩa tự nhiên nhất.
    *   **Ưu tiên 2 - Ngắt câu (Sentence Split)**: Nếu đoạn văn vẫn quá dài (>1000 tokens), thuật toán sẽ tìm điểm ngắt câu (`.`, `!`, `?`, `:`) gần nhất để chia nhỏ.
    *   **Cơ chế chồng lấp (Overlap Mechanism)**: Áp dụng overlap từ 50-80 tokens giữa các chunks liền kề. Điều này đảm bảo ngữ cảnh không bị đứt gãy ở điểm cắt, giúp mô hình hiểu được mối liên hệ giữa các đoạn.

#### **Giai đoạn 3: Làm giàu dữ liệu (Data Enrichment & Formatting)**
Để tối ưu cho LLM, dữ liệu không chỉ là văn bản thô mà được định dạng lại (Prompt Engineering at Data Level):
- **Cấu trúc Hybrid**: Sử dụng tiêu đề trường bằng tiếng Anh (English Headers) kết hợp với nội dung tiếng Việt. Ví dụ: `Title: ...`, `Content: ...`. Lý do: Các LLM hiện đại (như GPT-4, Gemini) xử lý cấu trúc chỉ dẫn tiếng Anh tốt hơn.
- **Metadata Generation**: Mỗi chunk đi kèm với một JSON metadata chứa đầy đủ thông tin gốc (ID, nguồn, ngày tháng, phân loại). Điều này cho phép thực hiện **Hybrid Search** (kết hợp tìm kiếm vector và lọc theo metadata) sau này.

---

## 4. KẾT QUẢ ĐẠT ĐƯỢC (RESULTS)

### 4.1. Dữ liệu Tài chính (`finance_index_clean.csv`)
- **Đầu ra**: 2,815 chunks từ 1,720 công ty.
- **Đặc điểm**: Mỗi chunk chứa thông tin tổng hợp của một công ty, bao gồm cả mô tả và chỉ số tài chính quan trọng.
- **Ứng dụng**: Cho phép tra cứu nhanh hồ sơ năng lực, so sánh chỉ số tài chính giữa các doanh nghiệp.

### 4.2. Dữ liệu Pháp lý (`legal_index_clean.csv`)
- **Đầu ra**: 2,698 chunks từ 5,012 điều luật.
- **Đặc điểm**: Giữ nguyên cấu trúc phân cấp. Các điều luật ngắn được giữ nguyên, điều luật dài được chia nhỏ nhưng vẫn giữ tiêu đề và ngữ cảnh.
- **Ứng dụng**: Hỗ trợ tra cứu luật chính xác, trích dẫn điều khoản cụ thể cho các câu hỏi về tuân thủ (compliance).

### 4.3. Dữ liệu Tin tức (`news_index_clean.csv`)
- **Đầu ra**: ~1,470,000 chunks từ 12,685 bài báo.
- **Đặc điểm**: Tích hợp thông tin thời gian (Năm, Tháng, Ngày) vào metadata.
- **Ứng dụng**: Phân tích xu hướng thị trường (Market Sentiment Analysis), theo dõi sự kiện theo dòng thời gian (Timeline Tracking).

---

## 5. Ý NGHĨA ĐỐI VỚI FINTECH (FINTECH IMPLICATIONS)

Việc hoàn thành bước tiền xử lý này đặt nền móng vững chắc cho hệ thống Fintech RAG:

1.  **Độ chính xác cao (High Fidelity)**: Dữ liệu sạch và có cấu trúc giúp giảm thiểu ảo giác (hallucination) của AI khi tư vấn tài chính.
2.  **Khả năng giải thích (Explainability)**: Việc lưu trữ metadata nguồn (Source Attribution) cho phép hệ thống luôn trích dẫn được nguồn gốc thông tin (ví dụ: "Theo Điều 5, Luật Chứng khoán..."), yếu tố bắt buộc trong lĩnh vực tài chính - pháp lý.
3.  **Tính thời gian thực (Temporal Awareness)**: Xử lý dữ liệu tin tức với nhãn thời gian cho phép hệ thống phân biệt thông tin cũ/mới, tránh đưa ra lời khuyên dựa trên dữ liệu lỗi thời.

---
*Báo cáo được lập bởi AI Assistant thuộc dự án Semantic-Router RAG.*

