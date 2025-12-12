"""
Prompts for Grounded Generation.

Provides system and user prompts for generating answers with citations.
"""

GROUNDED_GENERATION_SYSTEM = """Bạn là trợ lý AI chuyên về tài chính và pháp lý Việt Nam.

NHIỆM VỤ: Trả lời câu hỏi của người dùng DỰA TRÊN các tài liệu được cung cấp.

QUY TẮC BẮT BUỘC:
1. CHỈ sử dụng thông tin từ CONTEXT được cung cấp
2. PHẢI trích dẫn nguồn bằng [1], [2], ... sau mỗi khẳng định
3. Nếu không tìm thấy thông tin, nói rõ "Không tìm thấy trong tài liệu được cung cấp"
4. KHÔNG bịa đặt thông tin không có trong context
5. Trả lời bằng tiếng Việt, rõ ràng và chuyên nghiệp
6. Tổng hợp thông tin từ nhiều nguồn nếu cần

ĐỊNH DẠNG CITATION:
- Mỗi câu khẳng định cần có citation: "ROE là tỷ suất sinh lời trên vốn chủ sở hữu [1]."
- Có thể dùng nhiều citations: "VNM có ROE 25% [2], cao hơn trung bình ngành [3]."
- Citation phải đặt ngay sau khẳng định, trước dấu chấm câu

VÍ DỤ TRẢ LỜI TỐT:
"ROE (Return on Equity) là chỉ số đo lường khả năng sinh lời trên vốn chủ sở hữu của doanh nghiệp [1]. 
VNM hiện có ROE đạt 25.3% trong năm 2024 [2], cao hơn mức trung bình ngành sữa là 18% [3]."
"""

GROUNDED_GENERATION_USER = """CONTEXT (Tài liệu tham khảo):
{context}

---

CÂU HỎI: {query}

Hãy trả lời câu hỏi trên dựa trên context được cung cấp. Nhớ trích dẫn nguồn bằng [1], [2], ... sau mỗi khẳng định."""


# Few-shot examples for better grounding
GROUNDING_EXAMPLES = [
    {
        "query": "ROE là gì và VNM có ROE bao nhiêu?",
        "context": "[1] (GLOSSARY) ROE là viết tắt của Return on Equity, tức tỷ suất sinh lời trên vốn chủ sở hữu.\n[2] (FINANCIAL) VNM báo cáo ROE năm 2024 đạt 25.3%.",
        "answer": "ROE (Return on Equity) là tỷ suất sinh lời trên vốn chủ sở hữu, đo lường khả năng sinh lời của doanh nghiệp trên mỗi đồng vốn cổ đông đầu tư [1]. Theo báo cáo tài chính năm 2024, VNM có ROE đạt 25.3% [2]."
    },
    {
        "query": "Quy định về công bố thông tin của công ty đại chúng?",
        "context": "[1] (LEGAL) Theo Thông tư 96/2020/TT-BTC, công ty đại chúng phải công bố báo cáo tài chính quý trong vòng 20 ngày.\n[2] (LEGAL) Nghị định 155/2020/NĐ-CP quy định xử phạt vi phạm công bố thông tin từ 50-100 triệu đồng.",
        "answer": "Theo quy định tại Thông tư 96/2020/TT-BTC, công ty đại chúng có nghĩa vụ công bố báo cáo tài chính hàng quý trong thời hạn 20 ngày kể từ ngày kết thúc quý [1]. Việc vi phạm nghĩa vụ công bố thông tin có thể bị xử phạt từ 50 đến 100 triệu đồng theo Nghị định 155/2020/NĐ-CP [2]."
    }
]


def build_generation_prompt(query: str, context: str) -> str:
    """Build the full generation prompt."""
    return f"{GROUNDED_GENERATION_SYSTEM}\n\n{GROUNDED_GENERATION_USER.format(context=context, query=query)}"
