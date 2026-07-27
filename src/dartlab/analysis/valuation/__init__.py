"""Analyst 엔진 데이터 타입 — 종합 분석 결과."""

from __future__ import annotations

from dataclasses import dataclass, field

# 자료형과 의견 분류는 `types` 가 정본이다. 예전에는 이 파사드가 세 정의를 글자까지
# 똑같이 복사해 갖고 있었다. 한쪽 임계값만 옮기면 같은 회사가 import 경로에 따라 다른
# 의견을 받는다.
from dartlab.analysis.valuation.types import (  # noqa: E402
    _OPINION_MAP,
    AnalystReport,
    ValuationMethod,
    _classifyOpinion,
    opinionFromUpside,
)
from dartlab.core.utils.fmt import fmtPrice
