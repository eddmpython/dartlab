"""EDGAR 재무 데이터 엔진.

SEC companyfacts에서 시계열을 추출하고,
DART canonical snakeId로 매핑하여 L2 엔진과 호환되는 결과를 생성한다.
"""

from dartlab.providers.edgar.finance.mapper import EdgarMapper
from dartlab.providers.edgar.finance.pivot import buildAnnual, buildTimeseries

__all__ = [
    "buildTimeseries",
    "buildAnnual",
    "EdgarMapper",
]
