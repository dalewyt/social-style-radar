"""
玩法分类定义
"""

CATEGORIES = {
    "ai_photo": {
        "name": "AI Photo",
        "priority": "P0",
        "desc": "给人像照片生成完全不同的风格化照片，保持人物一致性",
        "keywords": ["portrait", "headshot", "证件照", "人像", "写真", "艺术照", "风格化照片"],
        "search_queries": [
            "AI portrait style",
            "AI headshot style",
            "AI 证件照 风格",
            "AI 人像 风格化",
        ],
    },
    "couple_photo": {
        "name": "Couple Photo",
        "priority": "P0",
        "desc": "双人合影风格化",
        "keywords": ["couple", "双人", "情侣", "合影", "together", "two people"],
        "search_queries": [
            "AI couple photo style",
            "AI 情侣照 风格",
            "AI 双人 合影",
        ],
    },
    "ai_edit": {
        "name": "AI Edit",
        "priority": "P1",
        "desc": "基于原片增加效果（滤镜、调色、特效）",
        "keywords": ["filter", "effect", "调色", "滤镜", "特效", "修图", "edit"],
        "search_queries": [
            "AI photo filter",
            "AI photo effect",
            "AI 滤镜 效果",
        ],
    },
    "ai_video": {
        "name": "AI Video",
        "priority": "P0",
        "desc": "视频风格化/转场/特效",
        "keywords": ["video", "视频", "动画", "转场", "vlog", "clip"],
        "search_queries": [
            "AI video style",
            "AI 视频 效果",
            "AI vlog filter",
        ],
    },
}


def get_category_keywords(cat_id: str) -> list:
    """获取某分类的所有关键词（小写）"""
    if cat_id in CATEGORIES:
        return [kw.lower() for kw in CATEGORIES[cat_id]["keywords"]]
    return []


def detect_category(text: str) -> str | None:
    """
    基于文本内容检测玩法分类
    返回第一个匹配的分类 ID，或 None
    """
    text_lower = text.lower()
    for cat_id, cat_info in CATEGORIES.items():
        if any(kw.lower() in text_lower for kw in cat_info["keywords"]):
            return cat_id
    return None


def get_all_search_queries() -> list:
    """获取所有分类的搜索查询"""
    queries = []
    for cat_info in CATEGORIES.values():
        queries.extend(cat_info["search_queries"])
    return queries


def get_category_search_queries(cat_id: str) -> list:
    """获取某分类的搜索查询"""
    if cat_id in CATEGORIES:
        return CATEGORIES[cat_id]["search_queries"]
    return []
