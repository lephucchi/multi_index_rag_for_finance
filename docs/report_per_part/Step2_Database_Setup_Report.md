# BÁO CÁO CHI TIẾT BƯỚC 2: THIẾT LẬP CƠ SỞ DỮ LIỆU VECTOR (VECTOR DATABASE SETUP)
**Dự án**: A Semantic-Router Multi-Index Retrieval-Augmented Generation System for Vietnamese Financial Data and the Economic–Regulatory Framework  
**Ngày báo cáo**: 01/12/2025  
**Người thực hiện**: Antigravity (AI Assistant) & User

---

## 1. TỔNG QUAN (EXECUTIVE SUMMARY)

Bước 2 của dự án tập trung vào việc thiết kế và triển khai hạ tầng lưu trữ vector (Vector Storage Infrastructure) trên nền tảng Supabase. Đây là thành phần cốt lõi cho phép hệ thống RAG thực hiện tìm kiếm ngữ nghĩa (semantic search) với tốc độ cao và độ chính xác lớn.

Chúng tôi đã lựa chọn giải pháp **PostgreSQL + pgvector** thay vì các vector database chuyên dụng (như Pinecone hay Weaviate) để tận dụng khả năng quản lý dữ liệu quan hệ (relational data) mạnh mẽ kết hợp với khả năng tìm kiếm vector, phù hợp với đặc thù dữ liệu tài chính phức tạp.

---

## 2. KIẾN TRÚC CƠ SỞ DỮ LIỆU (DATABASE ARCHITECTURE)

Hệ thống được thiết kế theo mô hình **Multi-Index**, với 3 bảng độc lập phục vụ 3 miền dữ liệu khác nhau. Mỗi bảng được tối ưu hóa riêng biệt cho loại dữ liệu mà nó lưu trữ.

### 2.1. Bảng Chỉ số Tài chính (`finance_index`)
- **Mục đích**: Lưu trữ hồ sơ doanh nghiệp và chỉ số tài chính.
- **Schema**:
    - `id`: Khóa chính.
    - `ticker`: Mã chứng khoán (Primary Filter).
    - `content`: Văn bản mô tả doanh nghiệp (dùng cho embedding).
    - `metadata`: JSONB chứa các trường cấu trúc (`overview`, `financial_ratios`, `shareholders`).
    - `embedding`: Vector 1536 chiều (tương thích OpenAI `text-embedding-3-small`).
- **Chiến lược Index**:
    - **HNSW (Hierarchical Navigable Small World)**: Cho cột `embedding` để tối ưu tốc độ tìm kiếm vector (ANN search).
    - **GIN (Generalized Inverted Index)**: Cho cột `metadata` để tối ưu tốc độ lọc theo tiêu chí JSON (ví dụ: tìm công ty có P/E < 10).

### 2.2. Bảng Chỉ số Pháp lý (`legal_index`)
- **Mục đích**: Lưu trữ văn bản luật.
- **Schema**:
    - `law_id`: Tên luật (Primary Filter).
    - `article_id`: Điều khoản.
    - `content`: Nội dung điều luật.
    - `metadata`: JSONB chứa thông tin phân cấp (`chapter`, `section`).
- **Đặc điểm**: Thiết kế hỗ trợ truy vấn phân cấp (Hierarchical Querying), cho phép tìm kiếm trong phạm vi một bộ luật cụ thể.

### 2.3. Bảng Chỉ số Tin tức (`news_index`)
- **Mục đích**: Lưu trữ tin tức thị trường.
- **Schema**:
    - `publish_date`: Thời gian xuất bản.
    - `metadata`: JSONB chứa `year`, `month`, `day`.
- **Đặc điểm**: Tối ưu cho truy vấn theo thời gian (Temporal Querying). Việc tách `year`, `month` ra khỏi JSON giúp query planner của Postgres thực hiện partition pruning hiệu quả hơn (nếu áp dụng partitioning sau này).

---

## 3. CÔNG NGHỆ & THUẬT TOÁN (TECHNOLOGY & ALGORITHMS)

### 3.1. pgvector Extension
Sử dụng extension `vector` của PostgreSQL để biến cơ sở dữ liệu quan hệ thành vector database.
- **Distance Metric**: Cosine Similarity (`<=>` operator). Đây là thước đo phù hợp nhất cho các embedding văn bản chuẩn hóa (normalized embeddings) từ OpenAI.
- **Dimensions**: 1536 (chuẩn của model `text-embedding-3-small` và `text-embedding-3-large`).

### 3.2. Hybrid Search Implementation
Chúng tôi triển khai các hàm RPC (Remote Procedure Call) trong Postgres để thực hiện Hybrid Search ngay tại tầng database:
- **Cơ chế**: `Vector Similarity` + `Metadata Filtering`.
- **Lợi ích**: Giảm thiểu lượng dữ liệu phải truyền tải về backend, tận dụng sức mạnh tính toán của database server.
- **Ví dụ**: Hàm `match_finance_documents` cho phép tìm kiếm "doanh nghiệp bất động sản" (vector) NHƯNG chỉ trong nhóm "P/E < 15" (metadata filter).

---

## 4. LÝ DO LỰA CHỌN CÔNG NGHỆ (RATIONALE)

Tại sao chọn **Supabase (Postgres)** cho Fintech RAG?

1.  **ACID Compliance**: Dữ liệu tài chính yêu cầu tính toàn vẹn cao. Postgres đảm bảo giao dịch (transactions) an toàn tuyệt đối, điều mà nhiều NoSQL vector DB không cam kết.
2.  **Rich Metadata Filtering**: Khả năng query JSONB của Postgres là vô đối. Trong Fintech, người dùng thường hỏi các câu phức tạp như "Tìm công ty công nghệ (semantic) có ROE > 15% (structured)". Postgres xử lý điều này trong một câu query duy nhất cực kỳ hiệu quả.
3.  **Cost Efficiency**: Không cần duy trì 2 hệ thống riêng biệt (1 DB cho metadata, 1 DB cho vector). All-in-one solution giúp giảm chi phí vận hành và độ trễ mạng.

---

## 5. KẾT LUẬN (CONCLUSION)

Việc thiết lập thành công kiến trúc Multi-Index trên Supabase là bước đệm quan trọng. Hệ thống hiện đã sẵn sàng để tiếp nhận hàng triệu vector embeddings từ bước tiếp theo. Kiến trúc này đảm bảo khả năng mở rộng (scalability) và độ trễ thấp (low latency) cho ứng dụng cuối cùng.

---
*Báo cáo được lập bởi AI Assistant thuộc dự án Semantic-Router RAG.*

