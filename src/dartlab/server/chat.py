"""대화 관련 로직 — 프롬프트, 스냅샷, 히스토리."""

from __future__ import annotations

from typing import Any

import polars as pl

import dartlab
from dartlab import Company

from .dialogue import ConversationState, build_dialogue_policy
from .models import HistoryMessage

_MAX_HISTORY_TURNS = 10
_MAX_HISTORY_CHARS = 12000
_MAX_HISTORY_MESSAGE_CHARS = 1800

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


def build_dynamic_chat_prompt(state: ConversationState | None = None) -> str:
    """실시간 데이터 현황을 포함한 채팅 시스템 프롬프트 생성."""
    from dartlab.core.dataLoader import _dataDir

    def _count(category: str) -> int:
        try:
            data_dir = _dataDir(category)
        except (FileNotFoundError, KeyError, OSError, PermissionError, ValueError):
            return 0
        if not data_dir.exists():
            return 0
        return len(list(data_dir.glob("*.parquet")))

    docs_count = _count("docs")
    finance_count = _count("finance")
    edgar_docs_count = _count("edgarDocs")
    edgar_finance_count = _count("edgar")

    version = dartlab.__version__ if hasattr(dartlab, "__version__") else "unknown"

    prompt = (
        "당신은 DartLab의 금융 분석 AI 어시스턴트입니다. "
        "한국 DART 전자공시와 미국 SEC EDGAR 데이터를 함께 다루며, "
        "사용자가 지금 무엇을 할 수 있는지 먼저 설명하고 다음 행동까지 제안합니다.\n\n"
        f"## DartLab 정보\n"
        f"- **버전**: {version}\n"
        f"- **Python 라이브러리**: `pip install dartlab` (PyPI)\n"
        f"- **GitHub**: https://github.com/eddmpython/dartlab\n\n"
        f"## 현재 보유 데이터 (실시간)\n"
        f"- **DART docs**: {docs_count}개 기업의 정기보고서 파싱 데이터\n"
        f"- **DART finance**: {finance_count}개 상장기업의 XBRL 재무제표\n"
        f"- **EDGAR docs**: {edgar_docs_count}개 ticker의 SEC 공시 문서 데이터\n"
        f"- **EDGAR finance**: {edgar_finance_count}개 ticker의 companyfacts 데이터\n\n"
        "## 사용 가능한 기능\n"
        "사용자가 기능이나 데이터에 대해 물으면 아래를 안내하세요:\n"
        "- `삼성전자 분석해줘` — 종목명 + 질문으로 재무분석\n"
        "- `AAPL 어떤 데이터가 있어?` — EDGAR company 기준 사용 가능 데이터 확인\n"
        "- `EDGAR에서 더 받을 수 있어?` — 추가 수집 가능한 범위와 경로 설명\n"
        "- `OpenDart/OpenEdgar로 뭐가 돼?` — 공개 API 범위 설명\n"
        "- `AAPL filings 원문 가져와줘` / `삼성전자 배당 OpenAPI로 조회해줘` — 공개 API 직접 호출\n"
        "- `GPT 연결하면 코딩도 돼?` — 현재 가능한 코딩 보조와 미지원 범위 설명\n"
        "- `데이터 현황 알려줘` — 보유 데이터 수와 상태\n"
        "- `어떤 종목이 있어?` / `삼성 검색` — 종목 검색\n"
        "- `삼성전자 어떤 데이터가 있어?` — 특정 종목의 사용 가능 모듈 목록\n"
        "- `삼성전자 원본 재무제표 보여줘` — 원본 데이터 조회\n"
        "- sections/show/trace/diff 기반 공시 탐색\n"
        "- OpenDart/OpenEdgar 공개 API 직접 호출 + saver 실행\n"
        "- 재무비율: ROE, ROA, 부채비율, 유동비율, FCF, 이자보상배율 자동계산\n"
        "- 업종별 벤치마크 비교, insight/rank/sector 분석\n"
        "- Excel 내보내기, 템플릿 생성/재사용\n\n"
        "## 답변 규칙\n"
        "- 기능 범위나 가능 여부를 묻는 질문이면 가능한 것, 바로 할 수 있는 것, 아직 안 되는 것을 먼저 짧게 정리하세요.\n"
        "- 수치가 2개 이상 등장하면 반드시 마크다운 테이블(|표)로 정리하세요.\n"
        "- 핵심 수치는 **굵게** 표시하세요.\n"
        "- 질문과 같은 언어로 답변하세요.\n"
        "- 답변은 간결하되, 근거가 있는 분석을 제공하세요.\n"
        "- 숫자만 나열하지 말고 해석에 집중하세요.\n"
        "- 특정 종목을 분석하려면 종목명이나 종목코드를 알려달라고 안내하세요."
    )
    if state is not None:
        prompt += "\n\n" + build_dialogue_policy(state)
    return prompt


def build_history_messages(history: list[HistoryMessage] | None) -> list[dict[str, str]]:
    """클라이언트의 대화 기록을 LLM messages 포맷으로 변환. 최근 N턴만 유지."""
    if not history:
        return []
    trimmed = history[-(_MAX_HISTORY_TURNS * 2) :]
    prepared: list[dict[str, str]] = []
    for h in trimmed:
        role = h.role if h.role in ("user", "assistant") else "user"
        text = h.text.strip()
        if not text:
            continue
        if role == "assistant" and h.meta:
            summary_parts = []
            if h.meta.company or h.meta.stockCode:
                company_text = h.meta.company or "?"
                if h.meta.stockCode:
                    company_text += f" ({h.meta.stockCode})"
                summary_parts.append(company_text)
            if h.meta.market:
                summary_parts.append(f"시장: {h.meta.market}")
            if h.meta.topicLabel or h.meta.topic:
                summary_parts.append(f"주제: {h.meta.topicLabel or h.meta.topic}")
            if h.meta.dialogueMode:
                summary_parts.append(f"모드: {h.meta.dialogueMode}")
            if h.meta.userGoal:
                summary_parts.append(f"목표: {h.meta.userGoal}")
            if h.meta.modules:
                summary_parts.append(f"모듈: {', '.join(h.meta.modules)}")
            if summary_parts:
                text = f"[이전 대화 상태: {' | '.join(summary_parts)}]\n{text}"
        prepared.append({"role": role, "content": _compress_history_text(text)})

    total = 0
    selected: list[dict[str, str]] = []
    for item in reversed(prepared):
        content_len = len(item["content"])
        if selected and total + content_len > _MAX_HISTORY_CHARS:
            break
        selected.append(item)
        total += content_len
    return list(reversed(selected))


def _compress_history_text(text: str) -> str:
    """길어진 과거 대화를 앞뒤 핵심만 남기도록 압축."""
    if len(text) <= _MAX_HISTORY_MESSAGE_CHARS:
        return text
    head = int(_MAX_HISTORY_MESSAGE_CHARS * 0.65)
    tail = _MAX_HISTORY_MESSAGE_CHARS - head
    return text[:head].rstrip() + "\n...\n" + text[-tail:].lstrip()


def _stringify_focus_value(value: Any, *, max_rows: int = 12, max_chars: int = 2400) -> str:
    from dartlab.engines.ai.context import df_to_markdown

    if value is None:
        return "(데이터 없음)"
    if isinstance(value, pl.DataFrame):
        return df_to_markdown(value, max_rows=max_rows, compact=True)
    text = str(value)
    return text if len(text) <= max_chars else text[:max_chars] + "\n... (truncated)"


def build_focus_context(company: Company | Any, state: ConversationState) -> str | None:
    """현재 viewer/topic 맥락을 LLM 입력용 근거 블록으로 승격."""
    if not state.topic or not hasattr(company, "show"):
        return None

    lines = ["## 현재 사용자가 보고 있는 섹션"]
    lines.append(f"- topic: `{state.topic}`")
    if state.topic_label:
        lines.append(f"- label: {state.topic_label}")
    if state.company and state.stock_code:
        lines.append(f"- company: {state.company} ({state.stock_code})")

    try:
        overview = company.show(state.topic)
    except (AttributeError, KeyError, TypeError, ValueError):
        overview = None

    if isinstance(overview, pl.DataFrame) and overview.height > 0:
        lines.append("")
        lines.append("### 블록 목차")
        lines.append(_stringify_focus_value(overview, max_rows=6))

        block_col = (
            "block" if "block" in overview.columns else "blockOrder" if "blockOrder" in overview.columns else None
        )
        if block_col:
            first_block = overview.row(0, named=True).get(block_col)
            if isinstance(first_block, int):
                try:
                    block_value = company.show(state.topic, first_block)
                except (AttributeError, KeyError, TypeError, ValueError):
                    block_value = None
                if block_value is not None:
                    lines.append("")
                    lines.append(f"### 현재 섹션 대표 block={first_block}")
                    lines.append(_stringify_focus_value(block_value))

    if hasattr(company, "trace"):
        try:
            trace = company.trace(state.topic)
        except (AttributeError, KeyError, TypeError, ValueError):
            trace = None
        if trace:
            lines.append("")
            lines.append("### source trace")
            lines.append(_stringify_focus_value(trace, max_chars=1600))

    return "\n".join(lines)


def extract_last_stock_code(history: list[HistoryMessage] | None) -> str | None:
    """히스토리에서 가장 최근 분석된 종목코드를 추출."""
    if not history:
        return None
    for h in reversed(history):
        if h.meta and h.meta.stockCode:
            return h.meta.stockCode
    return None


def build_snapshot(company: Company) -> dict | None:
    """ratios + 핵심 시계열에서 즉시 표시할 스냅샷 데이터 추출."""
    ratios = getattr(company, "ratios", None)
    if ratios is None:
        return None

    isFinancial = False
    sectorInfo = getattr(company, "sector", None)
    if sectorInfo is not None:
        try:
            from dartlab.engines.sector.types import Sector

            isFinancial = sectorInfo.sector == Sector.FINANCIALS
        except (ImportError, AttributeError):
            isFinancial = False

    def _fmt(val, suffix=""):
        if val is None:
            return None
        abs_v = abs(val)
        sign = "-" if val < 0 else ""
        if abs_v >= 1e12:
            return f"{sign}{abs_v / 1e12:,.1f}조{suffix}"
        if abs_v >= 1e8:
            return f"{sign}{abs_v / 1e8:,.0f}억{suffix}"
        if abs_v >= 1e4:
            return f"{sign}{abs_v / 1e4:,.0f}만{suffix}"
        if abs_v >= 1:
            return f"{sign}{abs_v:,.0f}{suffix}"
        return f"0{suffix}"

    def _pct(val):
        return f"{val:.1f}%" if val is not None else None

    def _judge_pct(val, good, caution):
        if val is None:
            return None
        if val >= good:
            return "good"
        if val >= caution:
            return "caution"
        return "danger"

    def _judge_pct_inv(val, good, caution):
        if val is None:
            return None
        if val <= good:
            return "good"
        if val <= caution:
            return "caution"
        return "danger"

    items = []
    roeGood, roeCaution = (8, 5) if isFinancial else (10, 5)
    roaGood, roaCaution = (0.5, 0.2) if isFinancial else (5, 2)

    if ratios.revenueTTM is not None:
        items.append({"label": "매출(TTM)", "value": _fmt(ratios.revenueTTM), "status": None})
    if ratios.operatingIncomeTTM is not None:
        items.append(
            {
                "label": "영업이익(TTM)",
                "value": _fmt(ratios.operatingIncomeTTM),
                "status": "good" if ratios.operatingIncomeTTM > 0 else "danger",
            }
        )
    if ratios.netIncomeTTM is not None:
        items.append(
            {
                "label": "순이익(TTM)",
                "value": _fmt(ratios.netIncomeTTM),
                "status": "good" if ratios.netIncomeTTM > 0 else "danger",
            }
        )
    if ratios.operatingMargin is not None:
        items.append(
            {
                "label": "영업이익률",
                "value": _pct(ratios.operatingMargin),
                "status": _judge_pct(ratios.operatingMargin, 10, 5),
            }
        )
    if ratios.roe is not None:
        items.append({"label": "ROE", "value": _pct(ratios.roe), "status": _judge_pct(ratios.roe, roeGood, roeCaution)})
    if ratios.roa is not None:
        items.append({"label": "ROA", "value": _pct(ratios.roa), "status": _judge_pct(ratios.roa, roaGood, roaCaution)})
    if ratios.debtRatio is not None:
        items.append(
            {"label": "부채비율", "value": _pct(ratios.debtRatio), "status": _judge_pct_inv(ratios.debtRatio, 100, 200)}
        )
    if ratios.currentRatio is not None:
        items.append(
            {
                "label": "유동비율",
                "value": _pct(ratios.currentRatio),
                "status": _judge_pct(ratios.currentRatio, 150, 100),
            }
        )
    if ratios.fcf is not None:
        items.append({"label": "FCF", "value": _fmt(ratios.fcf), "status": "good" if ratios.fcf > 0 else "danger"})
    if ratios.revenueGrowth3Y is not None:
        items.append(
            {
                "label": "매출 3Y CAGR",
                "value": _pct(ratios.revenueGrowth3Y),
                "status": _judge_pct(ratios.revenueGrowth3Y, 5, 0),
            }
        )

    annual = getattr(company, "annual", None)
    trend = None
    if annual is not None:
        series, years = annual
        if years and len(years) >= 2:
            rev_list = series.get("IS", {}).get("sales")
            if rev_list:
                n = min(5, len(rev_list))
                recent_years = years[-n:]
                recent_vals = rev_list[-n:]
                trend = {"years": recent_years, "values": [v for v in recent_vals]}

    if not items:
        return None

    snapshot: dict[str, Any] = {"items": items}
    if trend:
        snapshot["trend"] = trend
    if ratios.warnings:
        snapshot["warnings"] = ratios.warnings[:3]

    return snapshot
