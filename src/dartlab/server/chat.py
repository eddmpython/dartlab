"""대화 관련 로직 — 프롬프트, 스냅샷, 히스토리."""

from __future__ import annotations

from typing import Any

import dartlab
from dartlab import Company

from .models import HistoryMessage

_MAX_HISTORY_TURNS = 10

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


def build_dynamic_chat_prompt() -> str:
    """실시간 데이터 현황을 포함한 채팅 시스템 프롬프트 생성."""
    from dartlab.core.dataLoader import _dataDir

    docs_count = 0
    finance_count = 0
    try:
        docs_dir = _dataDir("docs")
        if docs_dir.exists():
            docs_count = len(list(docs_dir.glob("*.parquet")))
    except Exception:
        pass
    try:
        fin_dir = _dataDir("finance")
        if fin_dir.exists():
            finance_count = len(list(fin_dir.glob("*.parquet")))
    except Exception:
        pass

    version = dartlab.__version__ if hasattr(dartlab, "__version__") else "unknown"

    return (
        "당신은 DartLab의 금융 분석 AI 어시스턴트입니다. "
        "한국 주식시장과 DART 전자공시 데이터에 대해 전문적으로 답변합니다.\n\n"
        f"## DartLab 정보\n"
        f"- **버전**: {version}\n"
        f"- **Python 라이브러리**: `pip install dartlab` (PyPI)\n"
        f"- **GitHub**: https://github.com/eddmpython/dartlab\n\n"
        f"## 현재 보유 데이터 (실시간)\n"
        f"- **공시 문서(docs)**: {docs_count}개 기업의 정기보고서 파싱 데이터\n"
        f"  - 재무제표 36개 항목 (매출, 영업이익, 자산, 부채 등)\n"
        f"  - 공시 서술 섹션 4개 항목 (사업개요, 위험요소, 주요계약, 연구개발)\n"
        f"  - K-IFRS 주석 12개 항목 (재고자산, 매출채권, 유형자산 등)\n"
        f"- **재무제표(finance)**: {finance_count}개 상장기업의 XBRL 재무제표 (2015~최근)\n"
        f"  - 손익계산서, 재무상태표, 현금흐름표\n"
        f"  - 분기별 standalone 시계열\n"
        f"  - 재무비율 자동 계산 (ROE, ROA, 부채비율, 영업이익률 등)\n\n"
        "## 사용 가능한 기능\n"
        "사용자가 기능이나 데이터에 대해 물으면 아래를 안내하세요:\n"
        "- `삼성전자 분석해줘` — 종목명 + 질문으로 재무분석\n"
        "- `데이터 현황 알려줘` — 보유 데이터 수와 상태\n"
        "- `어떤 종목이 있어?` / `삼성 검색` — 종목 검색\n"
        "- `삼성전자 어떤 데이터가 있어?` — 특정 종목의 사용 가능 모듈 목록\n"
        "- `삼성전자 원본 재무제표 보여줘` — 원본 데이터 조회\n"
        "- 36개 정량 분석 모듈: 매출분석, 세그먼트, R&D, 배당, 임원보수, 주주, 감사, 우발부채 등\n"
        "- 재무비율: ROE, ROA, 부채비율, 유동비율, FCF, 이자보상배율 자동계산\n"
        "- 업종별 벤치마크 비교 (14개 업종)\n\n"
        "## 답변 규칙\n"
        "- 수치가 2개 이상 등장하면 반드시 마크다운 테이블(|표)로 정리하세요.\n"
        "- 핵심 수치는 **굵게** 표시하세요.\n"
        "- 질문과 같은 언어로 답변하세요.\n"
        "- 답변은 간결하되, 근거가 있는 분석을 제공하세요.\n"
        "- 숫자만 나열하지 말고 해석에 집중하세요.\n"
        "- 특정 종목을 분석하려면 종목명이나 종목코드를 알려달라고 안내하세요."
    )


def build_history_messages(history: list[HistoryMessage] | None) -> list[dict[str, str]]:
    """클라이언트의 대화 기록을 LLM messages 포맷으로 변환. 최근 N턴만 유지."""
    if not history:
        return []
    trimmed = history[-(_MAX_HISTORY_TURNS * 2) :]
    msgs = []
    for h in trimmed:
        role = h.role if h.role in ("user", "assistant") else "user"
        text = h.text.strip()
        if not text:
            continue
        if role == "assistant" and h.meta and h.meta.stockCode:
            mod_str = ", ".join(h.meta.modules) if h.meta.modules else "N/A"
            text = f"[이전 분석: {h.meta.company or '?'} ({h.meta.stockCode}), 사용 모듈: {mod_str}]\n{text}"
        msgs.append({"role": role, "content": text})
    return msgs


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
