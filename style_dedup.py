"""
风格去重逻辑：避免短期内重复推荐相同风格
基于风格名称和关键词的语义相似度去重
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Set

HISTORY_FILE = Path(__file__).parent / "style_history.json"
DEDUP_DAYS = 14  # 14天内的风格视为重复


def load_style_history() -> Dict:
    """
    加载历史风格记录
    格式：{
        "2025-03-08": [
            {"name": "证件照", "keywords": ["证件照", "headshot", "formal"], "category": "ai_photo"},
            ...
        ]
    }
    """
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_style_history(history: Dict) -> None:
    """保存风格历史"""
    # 只保留最近 DEDUP_DAYS 天的记录
    cutoff = datetime.now(timezone.utc) - timedelta(days=DEDUP_DAYS)
    cutoff_str = cutoff.strftime("%Y-%m-%d")
    
    pruned = {}
    for date_str, styles in history.items():
        if date_str >= cutoff_str:
            pruned[date_str] = styles
    
    HISTORY_FILE.write_text(json.dumps(pruned, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_keywords(style_name: str, description: str = "") -> Set[str]:
    """从风格名称和描述中提取关键词"""
    text = f"{style_name} {description}".lower()
    # 简单分词（可以后续改进为更智能的分词）
    keywords = set()
    for word in text.split():
        if len(word) >= 2:  # 过滤单字
            keywords.add(word)
    return keywords


def is_duplicate_style(
    style_name: str,
    style_desc: str,
    history: Dict,
    threshold: float = 0.6
) -> bool:
    """
    判断风格是否与历史记录重复
    
    Args:
        style_name: 风格名称
        style_desc: 风格描述
        history: 历史记录
        threshold: 相似度阈值（0-1），超过则视为重复
    
    Returns:
        True 如果重复，False 如果新颖
    """
    current_keywords = extract_keywords(style_name, style_desc)
    
    # 检查历史记录
    for date_str, styles in history.items():
        for hist_style in styles:
            hist_keywords = set(hist_style.get("keywords", []))
            
            # 计算 Jaccard 相似度
            if not current_keywords or not hist_keywords:
                continue
            
            intersection = len(current_keywords & hist_keywords)
            union = len(current_keywords | hist_keywords)
            similarity = intersection / union if union > 0 else 0
            
            if similarity >= threshold:
                return True
    
    return False


def filter_duplicate_styles(
    styles: List[Dict],
    history: Dict = None,
    threshold: float = 0.6
) -> List[Dict]:
    """
    过滤掉重复的风格
    
    Args:
        styles: 风格列表，每个元素包含 name, description
        history: 历史记录（可选，如果不提供则自动加载）
        threshold: 去重阈值
    
    Returns:
        去重后的风格列表
    """
    if history is None:
        history = load_style_history()
    
    filtered = []
    for style in styles:
        name = style.get("name", "")
        desc = style.get("description", "")
        
        if not is_duplicate_style(name, desc, history, threshold):
            filtered.append(style)
    
    return filtered


def record_today_styles(styles: List[Dict]) -> None:
    """记录今天推荐的风格"""
    history = load_style_history()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    today_styles = []
    for style in styles:
        name = style.get("name", "")
        desc = style.get("description", "")
        category = style.get("category")
        keywords = list(extract_keywords(name, desc))
        
        today_styles.append({
            "name": name,
            "keywords": keywords,
            "category": category,
        })
    
    history[today] = today_styles
    save_style_history(history)
