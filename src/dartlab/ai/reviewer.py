"""c.review() AI 요약 계층 — 데이터 보고서 위에 섹션별 AI 의견을 붙인다.

review.py가 데이터 나열 (검토서), reviewer.py가 AI 해석 레이어 (종합의견).
AI 설정이 없으면 데이터만 출력 + 안내 메시지.
"""

from __future__ import annotations

from collections import OrderedDict

_OPINION_CACHE: OrderedDict[str, str] = OrderedDict()
_CACHE_MAX = 50


def buildReviewWithAI(
    company,
    section: str | None = None,
    layout=None,
    helper: bool | None = None,
    guide: str | None = None,
    *,
    preset: str | None = None,
    detail: bool | None = None,
    basePeriod: str | None = None,
):
    """AI 섹션별 의견이 포함된 분석 보고서.

    guide: 사용자 추가 분석 관점 (예: "반도체 사이클 관점에서 평가해줘")
    """
    from dartlab.review.registry import buildReview

    report = buildReview(company, section=section, layout=layout, helper=helper, preset=preset, detail=detail, basePeriod=basePeriod)

    # AI 설정 확인
    llm = _getProvider()
    if llm is None:
        report.aiNote = "AI 종합의견을 보려면 dartlab.ai.setup()으로 AI를 설정하세요."
        return report

    # 섹션별 AI 의견 생성
    from dartlab.review.utils import isTerminal as _isTerminal

    report.aiNote = None

    if _isTerminal():
        from rich.console import Console
        from rich.live import Live
        from rich.spinner import Spinner

        console = Console(stderr=True)
        spinner = Spinner("dots", text="AI 분석 준비 중...")
        ctx = Live(spinner, console=console, transient=True)
    else:
        from contextlib import nullcontext

        ctx = nullcontext()

    with ctx as live:
        for sec in report.sections:
            if live is not None:
                from rich.spinner import Spinner as _Sp

                live.update(_Sp("dots", text=f"{sec.key} AI 의견 생성 중..."))
            opinion = _generateSectionOpinion(sec, company, llm, guide=guide)
            if opinion:
                sec.aiOpinion = opinion

    return report


def _getProvider():
    """AI provider 인스턴스 반환. 사용 불가면 None."""
    try:
        from dartlab.ai import get_config
        from dartlab.ai.providers import create_provider

        config = get_config()
        if not config.provider:
            return None
        llm = create_provider(config)
        if not llm.check_available():
            return None
        return llm
    except (ImportError, AttributeError, ValueError, OSError):
        return None


def _cacheKey(section, company, guide: str | None) -> str:
    """섹션 데이터 + 종목 + 가이드의 SHA256."""
    import hashlib

    serialized = _serializeSection(section)
    stockCode = getattr(company, "stockCode", "")
    raw = f"{stockCode}:{section.key}:{guide or ''}:{serialized}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _generateSectionOpinion(
    section,
    company,
    llm,
    *,
    guide: str | None = None,
) -> str | None:
    """한 섹션의 데이터를 직렬화 → AI에게 핵심 판단 요청."""
    serialized = _serializeSection(section)
    if not serialized:
        return None

    # 캐시 확인
    key = _cacheKey(section, company, guide)
    if key in _OPINION_CACHE:
        _OPINION_CACHE.move_to_end(key)
        return _OPINION_CACHE[key]

    corpName = getattr(company, "corpName", "")
    baseSystem = (
        "당신은 기업 재무 분석 전문가입니다. "
        "아래 데이터를 읽고 다음 구조로 분석하세요:\n"
        "1. 핵심 판단 (1줄): 이 섹션의 데이터가 말하는 한 줄 결론\n"
        "2. 근거 (2~3줄): 수치를 인용하여 판단을 뒷받침\n"
        "3. 주의점 (1줄): 이 데이터만으로 판단하기 어려운 부분\n\n"
        "수치 근거를 반드시 포함하고, 긍정/부정/중립을 명확히 구분하세요. "
        "투자 권유는 하지 마세요."
    )

    # aiGuide + 사용자 guide 결합
    guideParts = []
    if section.aiGuide:
        guideParts.append(section.aiGuide)
    if guide:
        guideParts.append(guide)
    if guideParts:
        baseSystem += "\n\n[분석 관점]\n" + "\n".join(guideParts)

    # 순환 서사 컨텍스트 — 섹션 간 인과관계 인지
    if section.threads:
        threadContext = "\n".join(f"- {t.title}: {t.story}" for t in section.threads)
        baseSystem += (
            "\n\n[교차 분석 컨텍스트]\n"
            "이 섹션은 다른 섹션과 다음과 같은 인과관계가 감지되었습니다:\n"
            f"{threadContext}\n"
            "이 맥락을 고려하여 독립 분석이 아닌 연결된 관점에서 분석하세요."
        )

    prompt = f"[{corpName}] {section.title}\n\n{serialized}\n\n위 데이터의 분석:"

    messages = [
        {"role": "system", "content": baseSystem},
        {"role": "user", "content": prompt},
    ]

    try:
        response = llm.complete(messages)
        result = response.answer.strip() if response and response.answer else None
    except (OSError, ValueError, TimeoutError):
        result = None

    # 캐시 저장
    if result:
        _OPINION_CACHE[key] = result
        while len(_OPINION_CACHE) > _CACHE_MAX:
            _OPINION_CACHE.popitem(last=False)

    return result


def _serializeSection(section) -> str:
    """AnalysisSection을 LLM 입력용 텍스트로 직렬화."""
    from dartlab.review.blocks import (
        FlagBlock,
        HeadingBlock,
        MetricBlock,
        TableBlock,
        TextBlock,
    )

    lines: list[str] = []

    # 섹션 메타데이터
    lines.append(f"[섹션] {section.title}")
    if section.helper:
        lines.append(f"[분석 포인트]\n{section.helper}")
    lines.append("")
    lines.append("[데이터]")

    for block in section.blocks:
        if isinstance(block, HeadingBlock):
            prefix = "##" if block.level == 1 else "###"
            lines.append(f"{prefix} {block.title}")

        elif isinstance(block, TextBlock):
            lines.append(block.text)

        elif isinstance(block, MetricBlock):
            for label, value in block.metrics:
                lines.append(f"- {label}: {value}")

        elif isinstance(block, TableBlock):
            lines.append(_serializeTable(block))

        elif isinstance(block, FlagBlock):
            icon = "⚠" if block.kind == "warning" else "✦"
            for f in block.flags:
                lines.append(f"{icon} {f}")

        elif hasattr(block, "df"):
            # SelectResult / ChartResult — DataFrame 직렬화
            try:
                import polars as pl

                df = block.df
                if isinstance(df, pl.DataFrame) and not df.is_empty():
                    label = getattr(block, "label", "")
                    if label:
                        lines.append(f"### {label}")
                    cols = df.columns
                    lines.append("| " + " | ".join(cols) + " |")
                    lines.append("| " + " | ".join("---" for _ in cols) + " |")
                    for row in df.iter_rows():
                        cells = [str(v) if v is not None else "-" for v in row]
                        lines.append("| " + " | ".join(cells) + " |")
            except (ImportError, AttributeError):
                pass

    return "\n".join(lines)


def _serializeTable(block) -> str:
    """TableBlock을 마크다운 테이블로 직렬화."""
    import polars as pl

    df = block.df
    if not isinstance(df, pl.DataFrame) or df.is_empty():
        return ""

    rows = []
    cols = df.columns
    rows.append("| " + " | ".join(cols) + " |")
    rows.append("| " + " | ".join("---" for _ in cols) + " |")

    for row in df.iter_rows():
        cells = [str(v) if v is not None else "-" for v in row]
        rows.append("| " + " | ".join(cells) + " |")

    return "\n".join(rows)
