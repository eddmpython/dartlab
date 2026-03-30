"""맥락 인식 힌트 엔진 — 상황별 사용자 안내.

각 상황(Company 생성, 분석 요청, 스캔 요청 등)에서
사용자에게 도움이 될 힌트를 중앙 관리한다.
"""

from __future__ import annotations

from typing import Any


def onCompanyCreated(company: Any) -> list[str]:
    """Company 생성 후 표시할 힌트 목록.

    Args:
        company: Company 인스턴스 (DartCompany 또는 EdgarCompany).

    Returns:
        힌트 문자열 리스트. 비어있으면 안내 없음.
    """
    hints: list[str] = []

    hasDocs = getattr(company, "_hasDocs", False)
    hasFinance = getattr(company, "_hasFinanceParquet", False)
    hasReport = getattr(company, "_hasReport", False)
    stockCode = getattr(company, "stockCode", "")

    # 데이터 보완 안내
    if hasDocs and not hasFinance:
        hints.append(f"finance 데이터를 추가하면 재무비율/분석을 사용할 수 있습니다: dartlab.collect('{stockCode}')")
    if hasDocs and not hasReport:
        hints.append("report 데이터를 추가하면 배당/임원/지배구조 상세를 볼 수 있습니다")

    # freshness 안내
    freshnessResult = getattr(company, "_freshnessResult", None)
    if freshnessResult and hasattr(freshnessResult, "ageInDays"):
        age = freshnessResult.ageInDays
        if age is not None and age > 90:
            hints.append(f"데이터가 {age}일 전 기준입니다. 갱신: c.update() 또는 dartlab collect {stockCode}")

    return hints


def nextSteps(company: Any) -> list[str]:
    """Company 생성 후 '다음에 뭘 할 수 있는지' 안내.

    Args:
        company: Company 인스턴스.

    Returns:
        "명령어   설명" 형식 문자열 리스트.
    """
    hasFinance = getattr(company, "_hasFinanceParquet", False)
    hasDocs = getattr(company, "_hasDocs", False)
    steps: list[str] = []

    if hasFinance:
        steps.append("c.BS / c.IS / c.CF   재무제표")
        steps.append("c.ratios             재무비율")
    if hasDocs:
        steps.append("c.show(topic)        공시 원문 조회")
        steps.append("c.index              전체 목록")
    steps.append("c.insights           7영역 등급 요약")
    steps.append("c.review()           14축 분석 보고서")

    return steps


def onScanRequested(axis: str) -> str | None:
    """스캔 호출 시 안내. 데이터 부족하면 안내 반환."""
    try:
        from dartlab.guide import guide

        result = guide.checkReady("scan")
        if not result.ok:
            return result.guideText()
    except ImportError:
        pass
    return None


def onAnalysisRequested(axis: str | None = None) -> str | None:
    """분석 축 선택 시 안내. axis=None이면 축 선택 가이드."""
    if axis is not None:
        return None

    return (
        "분석 축을 선택하세요:\n"
        "  구조: 수익구조, 자금조달, 자산구조, 현금흐름\n"
        "  성과: 수익성, 성장성, 안정성, 효율성\n"
        "  종합: 종합평가, 이익품질, 비용구조\n"
        "  투자: 자본배분, 투자효율\n"
        "  외부: 지배구조, 공시변화, 비교분석\n"
        "  전망: 매출전망, 예측신호\n"
        '  예시: c.analysis("수익구조")'
    )


# ── 키 관리 통합 안내 ──

# 키가 필요한 기능 → (환경변수, 서비스명, 발급URL, 안내) 매핑
_KEY_REQUIREMENTS: dict[str, dict[str, str]] = {
    "dart": {
        "envKey": "DART_API_KEY",
        "label": "DART OpenAPI",
        "signupUrl": "https://opendart.fss.or.kr",
        "guide": "전자공시 API 키 — 한국 상장기업 공시 직접 수집에 필요",
        "setupCmd": 'dartlab.setup("dart-key")',
    },
    "fred": {
        "envKey": "FRED_API_KEY",
        "label": "FRED (미국 연방준비제도)",
        "signupUrl": "https://fred.stlouisfed.org/docs/api/api_key.html",
        "guide": "미국 거시경제 데이터 (금리, 실업률, GDP 등) 수집에 필요",
        "setupCmd": "FRED_API_KEY=... (.env에 직접 입력)",
    },
    "ecos": {
        "envKey": "ECOS_API_KEY",
        "label": "ECOS (한국은행 경제통계)",
        "signupUrl": "https://ecos.bok.or.kr/api/",
        "guide": "한국 거시경제 데이터 (기준금리, 환율, 물가 등) 수집에 필요",
        "setupCmd": "ECOS_API_KEY=... (.env에 직접 입력)",
    },
}


def onKeyRequired(service: str) -> str:
    """키가 필요한 기능 호출 시 안내 메시지 생성.

    Args:
        service: "dart", "fred", "ecos", 또는 AI provider id ("gemini", "groq" 등).

    Returns:
        키 신청 방법 + 입력 방법 안내 문자열.
    """
    # 1) 전용 서비스 (dart, fred, ecos)
    req = _KEY_REQUIREMENTS.get(service)
    if req:
        return (
            f"\n  {req['label']} API 키가 필요합니다.\n"
            f"  {req['guide']}\n\n"
            f"  1. 키 발급: {req['signupUrl']}\n"
            f"  2. 설정 방법 (택1):\n"
            f"     a) dartlab.setup() → {req['setupCmd']}\n"
            f"     b) .env 파일에 직접 입력: {req['envKey']}=발급받은키\n"
            f"     c) 환경변수 설정: export {req['envKey']}=발급받은키\n"
        )

    # 2) AI provider (gemini, groq, cerebras 등)
    try:
        from dartlab.guide.providers import _PROVIDERS

        spec = _PROVIDERS.get(service)
        if spec and spec.auth_kind == "api_key" and spec.env_key:
            lines = [
                f"\n  {spec.label} API 키가 필요합니다.",
                f"  {spec.description}",
            ]
            if spec.freeTierHint:
                lines.append(f"  ({spec.freeTierHint})")
            lines.append("")
            if spec.signupUrl:
                lines.append(f"  1. 키 발급: {spec.signupUrl}")
            lines.append("  2. 설정 방법 (택1):")
            lines.append(f'     a) dartlab.setup("{service}") → 대화형 입력')
            lines.append(f"     b) .env 파일에 직접 입력: {spec.env_key}=발급받은키")
            lines.append(f"     c) 환경변수 설정: export {spec.env_key}=발급받은키")
            lines.append("")
            return "\n".join(lines)
    except ImportError:
        pass

    return f"\n  '{service}' 서비스의 API 키가 필요합니다.\n  dartlab.setup()으로 설정하세요.\n"


def promptKeyIfMissing(service: str) -> str | None:
    """키가 없으면 안내 출력 + 대화형 입력 시도. 반환: 키 또는 None.

    노트북/REPL 환경에서 키 입력까지 한 흐름으로 처리한다.
    비대화형 환경(서버, CI)에서는 안내만 출력하고 None 반환.

    Args:
        service: "dart", "fred", "ecos", 또는 AI provider id.

    Returns:
        설정된 키 문자열, 또는 건너뛴 경우 None.
    """
    import os

    # 이미 설정되어 있나?
    req = _KEY_REQUIREMENTS.get(service)
    if req:
        envKey = req["envKey"]
        existing = os.environ.get(envKey)
        if existing:
            return existing
        # 대화형 입력 시도
        print(onKeyRequired(service))
        try:
            from dartlab.guide.env import promptAndSave

            return promptAndSave(envKey, label=req["label"], guide=req["signupUrl"])
        except (EOFError, KeyboardInterrupt):
            return None

    # AI provider
    try:
        from dartlab.guide.providers import _PROVIDERS

        spec = _PROVIDERS.get(service)
        if spec and spec.auth_kind == "api_key" and spec.env_key:
            existing = os.environ.get(spec.env_key)
            if existing:
                return existing
            print(onKeyRequired(service))
            try:
                from dartlab.guide.env import promptAndSave

                return promptAndSave(spec.env_key, label=spec.label, guide=spec.signupUrl or "")
            except (EOFError, KeyboardInterrupt):
                return None
    except ImportError:
        pass

    return None
