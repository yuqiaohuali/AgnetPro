"""小浪助手回应基调模型。"""

from dataclasses import dataclass

from src.emotion.Emotion_model import EmotionAnalysis


@dataclass(frozen=True)
class FeelingState:
    """助手根据用户情绪采用的回应状态。"""

    label: str  # 助手当前回应基调的名称。
    instruction: str  # 传给 Agent 的回应方式说明。


class FeelingModel:
    """根据用户情绪选择助手的回应基调。"""

    # 情绪到回应基调的映射，集中管理语气规则，便于后续扩展。
    _FEELINGS: dict[str, FeelingState] = {
        "开心": FeelingState(
            "积极",
            "保持自然、友好的语气，适度回应用户的积极情绪。",
        ),
        "悲伤": FeelingState(
            "关怀",
            "先表达理解和关心，再用温和、具体的方式提供帮助。",
        ),
        "愤怒": FeelingState(
            "冷静",
            "先认可用户的不满，避免争辩，清晰说明可以采取的解决步骤。",
        ),
        "焦虑": FeelingState(
            "耐心",
            "使用稳定、简洁的语气，把问题拆成清晰可执行的步骤。",
        ),
        "平静": FeelingState(
            "平和",
            "保持直接、清晰和友好的表达，不额外夸大情绪。",
        ),
    }

    def get_feeling(self, emotion: EmotionAnalysis | str) -> FeelingState:
        """根据情绪分析结果选择助手回应基调。"""

        label = emotion.label if isinstance(emotion, EmotionAnalysis) else emotion
        return self._FEELINGS.get(label, self._FEELINGS["平静"])
