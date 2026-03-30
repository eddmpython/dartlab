"""서버 대화 헬퍼."""

from __future__ import annotations

from typing import Any

from .models import HistoryMessage

OLLAMA_MODEL_GUIDE: list[dict[str, str]] = [
    {
        "name": "qwen3",
        "size": "8B",
        "vram": "~6GB",
        "quality": "높음",
        "speed": "보통",
        "note": "한국어 재무분석에 가장 추천",
    },
    {"name": "gemma2", "size": "9B", "vram": "~7GB", "quality": "높음", "speed": "보통", "note": "다국어 성능 우수"},
    {"name": "llama3.2", "size": "3B", "vram": "~3GB", "quality": "보통", "speed": "빠름", "note": "저사양 PC 추천"},
    {"name": "mistral", "size": "7B", "vram": "~5GB", "quality": "보통", "speed": "빠름", "note": "영문 질문에 강함"},
    {"name": "phi4", "size": "14B", "vram": "~10GB", "quality": "매우높음", "speed": "느림", "note": "GPU 12GB+ 추천"},
    {
        "name": "qwen3:14b",
        "size": "14B",
        "vram": "~10GB",
        "quality": "매우높음",
        "speed": "느림",
        "note": "최고 품질, 고사양 PC",
    },
]


def extract_last_stock_code(history: list[HistoryMessage] | None) -> str | None:
    """히스토리에서 가장 최근 분석된 종목코드를 추출."""
    if not history:
        return None
    for h in reversed(history):
        if h.meta and h.meta.stockCode:
            return h.meta.stockCode
    return None


def build_topic_summary_question(topic: str) -> str:
    """Topic summary를 core.analyze()에 요청할 때 쓰는 canonical 질문."""
    return (
        f"현재 보고 있는 '{topic}' 섹션만 기준으로 핵심을 3~5문장으로 요약해줘. "
        "수치가 있으면 포함하고, 기간 변화가 있으면 짚어주고, 마지막에 한 줄 판단을 붙여줘."
    )


__all__ = [
    "OLLAMA_MODEL_GUIDE",
    "build_topic_summary_question",
    "extract_last_stock_code",
]
