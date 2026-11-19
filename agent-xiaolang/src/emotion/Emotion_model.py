"""用户情绪分析模型。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EmotionAnalysis:
    """一次用户输入的情绪分析结果。"""

    label: str  # 用户当前的主要情绪。
    confidence: float  # 关键词匹配得到的相对置信度。
    keywords: tuple[str, ...]  # 命中的情绪关键词。


class EmotionModel:
    """使用轻量关键词规则识别用户的主要情绪。"""

    # 各类情绪的关键词，避免每轮分析都额外调用大模型。
    _KEYWORDS: dict[str, tuple[str, ...]] = {
        "开心": (
            "开心",
            "高兴",
            "快乐",
            "喜欢",
            "满意",
            "感谢",
            "谢谢",
            "太好了",
            "good",
            "happy",
            "great",
        ),
        "悲伤": (
            "难过",
            "伤心",
            "失望",
            "委屈",
            "孤独",
            "哭",
            "崩溃",
            "不开心",
            "不高兴",
            "不满意",
            "sad",
            "disappointed",
        ),
        "愤怒": (
            "生气",
            "愤怒",
            "恼火",
            "气死",
            "烦死",
            "投诉",
            "垃圾",
            "angry",
            "mad",
        ),
        "焦虑": (
            "焦虑",
            "担心",
            "害怕",
            "紧张",
            "不安",
            "怎么办",
            "压力",
            "anxious",
            "worried",
        ),
    }

    def analyze(self, text: str) -> EmotionAnalysis:
        """分析文本并返回命中的主要情绪。"""

        normalized_text = text.strip().lower()
        if not normalized_text:
            return EmotionAnalysis("平静", 0.5, ())

        scores: dict[str, int] = {}
        matched_keywords: dict[str, tuple[str, ...]] = {}

        for label, keywords in self._KEYWORDS.items():
            matches = tuple(
                keyword
                for keyword in sorted(keywords, key=len, reverse=True)
                if keyword in normalized_text
                and not self._is_negated(normalized_text, keyword)
            )
            if matches:
                scores[label] = len(matches)
                matched_keywords[label] = matches

        if not scores:
            return EmotionAnalysis("平静", 0.5, ())

        label = max(scores, key=lambda item: scores[item])
        score = scores[label]
        confidence = round(min(0.95, 0.65 + score * 0.1), 2)

        return EmotionAnalysis(label, confidence, matched_keywords[label])

    @staticmethod
    def _is_negated(text: str, keyword: str) -> bool:
        """判断关键词前是否存在常见否定词。"""

        negations = ("不", "没", "没有", "不太", "not ")
        return any(f"{negation}{keyword}" in text for negation in negations)
