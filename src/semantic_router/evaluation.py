"""
Evaluation module for Semantic Router.

Provides:
- Test dataset with labeled queries
- Evaluation metrics (accuracy, F1, confusion matrix)
- Threshold tuning utilities
"""
import json
import numpy as np
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict


# =============================================================================
# Test Dataset - Labeled Queries
# =============================================================================

EVALUATION_DATASET = [
    # =========================================================================
    # GLOSSARY QUERIES (~40 samples)
    # =========================================================================
    {"query": "ROE là gì", "label": "glossary"},
    {"query": "EPS là gì", "label": "glossary"},
    {"query": "P/E ratio là gì", "label": "glossary"},
    {"query": "EBITDA là gì", "label": "glossary"},
    {"query": "NAV là gì", "label": "glossary"},
    {"query": "margin là gì", "label": "glossary"},
    {"query": "leverage là gì", "label": "glossary"},
    {"query": "thanh khoản là gì", "label": "glossary"},
    {"query": "dividend yield là gì", "label": "glossary"},
    {"query": "blue chip là gì", "label": "glossary"},
    {"query": "định nghĩa vốn điều lệ", "label": "glossary"},
    {"query": "định nghĩa công ty đại chúng", "label": "glossary"},
    {"query": "định nghĩa cổ phiếu ưu đãi", "label": "glossary"},
    {"query": "định nghĩa trái phiếu doanh nghiệp", "label": "glossary"},
    {"query": "khái niệm dòng tiền tự do", "label": "glossary"},
    {"query": "khái niệm rủi ro hệ thống", "label": "glossary"},
    {"query": "giải thích thuật ngữ hedging", "label": "glossary"},
    {"query": "ý nghĩa của chỉ số P/B", "label": "glossary"},
    {"query": "ROA có nghĩa là gì", "label": "glossary"},
    {"query": "beta trong chứng khoán là gì", "label": "glossary"},
    {"query": "thế nào là vốn chủ sở hữu", "label": "glossary"},
    {"query": "market cap nghĩa là gì", "label": "glossary"},
    {"query": "free float là gì", "label": "glossary"},
    {"query": "book value là gì", "label": "glossary"},
    {"query": "PE forward là gì", "label": "glossary"},
    {"query": "giải thích khái niệm biên lợi nhuận", "label": "glossary"},
    {"query": "tỷ suất sinh lời là gì", "label": "glossary"},
    {"query": "định nghĩa về lợi nhuận ròng", "label": "glossary"},
    {"query": "vốn lưu động là gì", "label": "glossary"},
    {"query": "nợ phải trả là gì", "label": "glossary"},
    
    # =========================================================================
    # LEGAL QUERIES (~40 samples)
    # =========================================================================
    {"query": "Điều 10 Luật Doanh nghiệp 2020", "label": "legal"},
    {"query": "Điều 5 Luật Chứng khoán 2019", "label": "legal"},
    {"query": "Luật Đầu tư quy định gì về vốn nước ngoài", "label": "legal"},
    {"query": "quy định về thành lập công ty cổ phần", "label": "legal"},
    {"query": "quy định về phát hành cổ phiếu", "label": "legal"},
    {"query": "quy định về công bố thông tin", "label": "legal"},
    {"query": "quy định về niêm yết chứng khoán", "label": "legal"},
    {"query": "điều kiện niêm yết sàn HOSE", "label": "legal"},
    {"query": "điều kiện IPO theo quy định", "label": "legal"},
    {"query": "thủ tục đăng ký kinh doanh", "label": "legal"},
    {"query": "thủ tục tăng vốn điều lệ", "label": "legal"},
    {"query": "nghị định 155 về chứng khoán", "label": "legal"},
    {"query": "thông tư hướng dẫn IPO", "label": "legal"},
    {"query": "nghĩa vụ công bố báo cáo tài chính", "label": "legal"},
    {"query": "pháp luật về M&A tại Việt Nam", "label": "legal"},
    {"query": "quy định về giao dịch nội bộ", "label": "legal"},
    {"query": "yêu cầu pháp lý khi phát hành trái phiếu", "label": "legal"},
    {"query": "Luật Chứng khoán nói gì về cổ đông", "label": "legal"},
    {"query": "quyền và nghĩa vụ của cổ đông", "label": "legal"},
    {"query": "quy định về chia cổ tức", "label": "legal"},
    {"query": "điều kiện làm đại chúng", "label": "legal"},
    {"query": "nghị định về thuế doanh nghiệp", "label": "legal"},
    {"query": "văn bản pháp luật về chứng khoán", "label": "legal"},
    {"query": "thủ tục mua bán cổ phiếu quỹ", "label": "legal"},
    {"query": "quy định về kiểm toán báo cáo tài chính", "label": "legal"},
    {"query": "Luật Doanh nghiệp 2020 có hiệu lực khi nào", "label": "legal"},
    {"query": "nghị quyết ĐHCĐ cần tỷ lệ bao nhiêu", "label": "legal"},
    {"query": "điều lệ công ty quy định những gì", "label": "legal"},
    {"query": "quy định về người đại diện pháp luật", "label": "legal"},
    {"query": "thủ tục giải thể doanh nghiệp", "label": "legal"},
    
    # =========================================================================
    # FINANCIAL QUERIES (~40 samples)
    # =========================================================================
    {"query": "P/E của VNM", "label": "financial"},
    {"query": "EPS của FPT năm 2024", "label": "financial"},
    {"query": "ROE của VCB", "label": "financial"},
    {"query": "ROA của TCB quý 3", "label": "financial"},
    {"query": "lợi nhuận ròng của HPG", "label": "financial"},
    {"query": "doanh thu VIC năm 2023", "label": "financial"},
    {"query": "báo cáo tài chính FPT Q3/2024", "label": "financial"},
    {"query": "kết quả kinh doanh VNM quý 4", "label": "financial"},
    {"query": "biên lợi nhuận của MWG", "label": "financial"},
    {"query": "so sánh P/E của VNM và MSN", "label": "financial"},
    {"query": "công ty nào có ROE cao nhất", "label": "financial"},
    {"query": "cổ tức VNM năm 2024", "label": "financial"},
    {"query": "vốn hóa thị trường của VIC", "label": "financial"},
    {"query": "tỷ lệ nợ trên vốn của HPG", "label": "financial"},
    {"query": "Vinamilk có EPS bao nhiêu", "label": "financial"},
    {"query": "FPT có tỷ lệ nợ như thế nào", "label": "financial"},
    {"query": "Hòa Phát báo lãi bao nhiêu", "label": "financial"},
    {"query": "ngân hàng nào lợi nhuận cao nhất", "label": "financial"},
    {"query": "tổng tài sản của Vietcombank", "label": "financial"},
    {"query": "doanh thu thuần của Masan", "label": "financial"},
    {"query": "chi phí hoạt động của VNM", "label": "financial"},
    {"query": "tăng trưởng doanh thu FPT", "label": "financial"},
    {"query": "chỉ số PEG của VNM", "label": "financial"},
    {"query": "tỷ suất cổ tức của VCB", "label": "financial"},
    {"query": "giá trị sổ sách của Vingroup", "label": "financial"},
    {"query": "số lượng cổ phiếu lưu hành FPT", "label": "financial"},
    {"query": "báo cáo tài chính hợp nhất VIC", "label": "financial"},
    {"query": "lợi nhuận gộp HPG 2024", "label": "financial"},
    {"query": "chi phí tài chính TCB", "label": "financial"},
    {"query": "thu nhập lãi thuần VCB", "label": "financial"},
    
    # =========================================================================
    # NEWS QUERIES (~40 samples)
    # =========================================================================
    {"query": "tin tức chứng khoán hôm nay", "label": "news"},
    {"query": "VN-Index hôm nay thế nào", "label": "news"},
    {"query": "thị trường tuần này", "label": "news"},
    {"query": "diễn biến giao dịch sáng nay", "label": "news"},
    {"query": "FPT vừa công bố gì", "label": "news"},
    {"query": "tin mới nhất về Vingroup", "label": "news"},
    {"query": "động thái của NHNN", "label": "news"},
    {"query": "ngành nào đang tăng trưởng", "label": "news"},
    {"query": "cổ phiếu nào đáng chú ý", "label": "news"},
    {"query": "tâm lý thị trường hiện tại", "label": "news"},
    {"query": "lạm phát tháng này", "label": "news"},
    {"query": "tỷ giá USD/VND mới nhất", "label": "news"},
    {"query": "FED tăng lãi suất ảnh hưởng gì", "label": "news"},
    {"query": "GDP Việt Nam quý này", "label": "news"},
    {"query": "tin về lãi suất ngân hàng", "label": "news"},
    {"query": "thị trường phiên chiều", "label": "news"},
    {"query": "xu hướng thị trường", "label": "news"},
    {"query": "dòng tiền đang chảy vào đâu", "label": "news"},
    {"query": "tin bất động sản hôm nay", "label": "news"},
    {"query": "cập nhật thị trường chứng khoán", "label": "news"},
    {"query": "khối ngoại mua bán thế nào hôm nay", "label": "news"},
    {"query": "VN30 diễn biến ra sao", "label": "news"},
    {"query": "cổ phiếu tăng mạnh nhất hôm nay", "label": "news"},
    {"query": "tin ngành ngân hàng tuần này", "label": "news"},
    {"query": "giá vàng hôm nay", "label": "news"},
    {"query": "giá dầu thế giới mới nhất", "label": "news"},
    {"query": "lãi suất liên ngân hàng", "label": "news"},
    {"query": "thống kê xuất nhập khẩu tháng này", "label": "news"},
    {"query": "nhận định thị trường ngày mai", "label": "news"},
    {"query": "phiên giao dịch cuối tuần", "label": "news"},
    
    # =========================================================================
    # MULTI-LABEL QUERIES (~20 samples)
    # =========================================================================
    {"query": "ROE là gì và VNM có ROE bao nhiêu", "label": ["glossary", "financial"]},
    {"query": "P/E là gì và so sánh P/E các ngân hàng", "label": ["glossary", "financial"]},
    {"query": "quy định IPO là gì và điều kiện", "label": ["glossary", "legal"]},
    {"query": "định nghĩa cổ tức và quy định chia cổ tức", "label": ["glossary", "legal"]},
    {"query": "EPS là gì và FPT có EPS bao nhiêu hôm nay", "label": ["glossary", "financial", "news"]},
    {"query": "tin tức về quy định mới công bố thông tin", "label": ["news", "legal"]},
    {"query": "Luật Chứng khoán quy định gì về EPS", "label": ["legal", "glossary"]},
    {"query": "so sánh ROE các ngân hàng theo quy định", "label": ["financial", "legal"]},
    {"query": "VNM công bố gì về cổ tức năm nay", "label": ["news", "financial"]},
    {"query": "thị trường hôm nay và P/E các cổ phiếu", "label": ["news", "financial"]},
]


@dataclass
class EvaluationResult:
    """Result of router evaluation."""
    accuracy: float
    f1_macro: float
    f1_per_class: Dict[str, float]
    precision_per_class: Dict[str, float]
    recall_per_class: Dict[str, float]
    confusion_matrix: Dict[str, Dict[str, int]]
    errors: List[Dict[str, Any]]


def evaluate_router(router, dataset: List[Dict] = None, verbose: bool = True) -> EvaluationResult:
    """
    Evaluate router on labeled dataset.
    
    Args:
        router: SemanticRouter or HybridRouter instance
        dataset: List of {"query": str, "label": str or List[str]}
        verbose: Print detailed results
        
    Returns:
        EvaluationResult with metrics
    """
    if dataset is None:
        dataset = EVALUATION_DATASET
    
    # Separate single-label and multi-label
    single_label_data = [d for d in dataset if isinstance(d["label"], str)]
    multi_label_data = [d for d in dataset if isinstance(d["label"], list)]
    
    # Evaluate single-label
    y_true = []
    y_pred = []
    errors = []
    
    for item in single_label_data:
        routes, scores = router.route(item["query"])
        predicted = routes[0]
        expected = item["label"]
        
        y_true.append(expected)
        y_pred.append(predicted)
        
        if predicted != expected:
            errors.append({
                "query": item["query"],
                "expected": expected,
                "predicted": predicted,
                "confidence": scores[predicted],
                "expected_score": scores.get(expected, 0)
            })
    
    # Calculate metrics
    classes = ["glossary", "legal", "financial", "news"]
    
    # Confusion matrix
    confusion = {c1: {c2: 0 for c2 in classes} for c1 in classes}
    for true, pred in zip(y_true, y_pred):
        confusion[true][pred] += 1
    
    # Per-class metrics
    precision = {}
    recall = {}
    f1 = {}
    
    for cls in classes:
        tp = confusion[cls][cls]
        fp = sum(confusion[other][cls] for other in classes if other != cls)
        fn = sum(confusion[cls][other] for other in classes if other != cls)
        
        precision[cls] = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall[cls] = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1[cls] = 2 * precision[cls] * recall[cls] / (precision[cls] + recall[cls]) \
            if (precision[cls] + recall[cls]) > 0 else 0
    
    # Overall metrics
    accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)
    f1_macro = sum(f1.values()) / len(f1)
    
    result = EvaluationResult(
        accuracy=accuracy,
        f1_macro=f1_macro,
        f1_per_class=f1,
        precision_per_class=precision,
        recall_per_class=recall,
        confusion_matrix=confusion,
        errors=errors
    )
    
    if verbose:
        print_evaluation_report(result)
    
    # Evaluate multi-label (optional, just report)
    if multi_label_data and verbose:
        print("\n=== Multi-label Evaluation ===")
        ml_correct = 0
        for item in multi_label_data:
            routes, _ = router.route(item["query"])
            expected = set(item["label"])
            predicted = set(routes)
            
            # Partial match
            overlap = len(expected & predicted) / len(expected)
            ml_correct += overlap
            
            status = "✓" if overlap >= 0.5 else "✗"
            print(f'{status} "{item["query"][:40]}..."')
            print(f'   Expected: {list(expected)}, Got: {list(predicted)}')
        
        print(f"\nMulti-label score: {ml_correct / len(multi_label_data):.2%}")
    
    return result


def print_evaluation_report(result: EvaluationResult):
    """Print formatted evaluation report."""
    print("\n" + "="*60)
    print("SEMANTIC ROUTER EVALUATION REPORT")
    print("="*60)
    
    print(f"\n📊 Overall Metrics:")
    print(f"   Accuracy: {result.accuracy:.2%}")
    print(f"   F1 Macro: {result.f1_macro:.2%}")
    
    print(f"\n📈 Per-class Metrics:")
    print(f"   {'Class':<12} {'Precision':<12} {'Recall':<12} {'F1':<12}")
    print(f"   {'-'*48}")
    for cls in ["glossary", "legal", "financial", "news"]:
        p = result.precision_per_class[cls]
        r = result.recall_per_class[cls]
        f = result.f1_per_class[cls]
        print(f"   {cls:<12} {p:<12.2%} {r:<12.2%} {f:<12.2%}")
    
    print(f"\n📉 Confusion Matrix:")
    classes = ["glossary", "legal", "financial", "news"]
    print(f"   {'Actual↓ Pred→':<12}", end="")
    for c in classes:
        print(f"{c[:4]:<8}", end="")
    print()
    
    for true_cls in classes:
        print(f"   {true_cls:<12}", end="")
        for pred_cls in classes:
            count = result.confusion_matrix[true_cls][pred_cls]
            print(f"{count:<8}", end="")
        print()
    
    if result.errors:
        print(f"\n❌ Errors ({len(result.errors)} cases):")
        for err in result.errors[:10]:  # Show first 10
            print(f'   "{err["query"][:40]}..."')
            print(f'   Expected: {err["expected"]}, Got: {err["predicted"]} (conf: {err["confidence"]:.3f})')


def tune_thresholds(
    router,
    dataset: List[Dict] = None,
    threshold_range: Tuple[float, float, float] = (0.50, 0.85, 0.05)
) -> Dict[str, float]:
    """
    Find optimal thresholds for each route.
    
    Args:
        router: Router instance
        dataset: Evaluation dataset
        threshold_range: (start, end, step)
        
    Returns:
        Dict of optimal thresholds per route
    """
    if dataset is None:
        dataset = [d for d in EVALUATION_DATASET if isinstance(d["label"], str)]
    
    classes = ["glossary", "legal", "financial", "news"]
    best_thresholds = {}
    
    print("\n🔧 Tuning Thresholds...")
    
    for cls in classes:
        best_f1 = 0
        best_thresh = 0.65
        
        for thresh in np.arange(*threshold_range):
            # Set threshold
            router.config.route_thresholds[cls] = thresh
            
            # Evaluate
            result = evaluate_router(router, dataset, verbose=False)
            f1 = result.f1_per_class[cls]
            
            if f1 > best_f1:
                best_f1 = f1
                best_thresh = thresh
        
        best_thresholds[cls] = round(best_thresh, 2)
        print(f"   {cls}: {best_thresh:.2f} (F1: {best_f1:.2%})")
    
    # Apply best thresholds
    router.config.route_thresholds = best_thresholds
    
    print(f"\n✅ Optimal thresholds applied: {best_thresholds}")
    
    return best_thresholds


def get_dataset_stats() -> Dict[str, int]:
    """Get statistics about the evaluation dataset."""
    stats = defaultdict(int)
    
    for item in EVALUATION_DATASET:
        if isinstance(item["label"], str):
            stats[item["label"]] += 1
            stats["single_label"] += 1
        else:
            for label in item["label"]:
                stats[f"multi_{label}"] += 1
            stats["multi_label"] += 1
    
    stats["total"] = len(EVALUATION_DATASET)
    return dict(stats)


if __name__ == "__main__":
    # Quick test
    from .router import HybridRouter
    
    print("Dataset stats:", get_dataset_stats())
    
    router = HybridRouter()
    result = evaluate_router(router)
    
    if result.accuracy < 0.90:
        print("\n⚠️ Accuracy below 90%, running threshold tuning...")
        tune_thresholds(router)
        print("\n📊 Re-evaluating with tuned thresholds:")
        evaluate_router(router)
