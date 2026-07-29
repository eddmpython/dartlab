"""DART 금액 문자열과 단위 라벨 정규화 SSOT.

원문 숫자 파싱과 단위 감지를 분리한다. ``parseAmount`` 는 원문에 배율을
적용하지 않고 숫자만 반환하며, 원 환산이 필요한 호출자는
``detectUnitScale`` 을 명시적으로 사용한다.
"""

from __future__ import annotations

import math
import re
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import polars as pl

UNIT_SCALE_TO_WON = MappingProxyType(
    {
        "원": 1,
        "천원": 1_000,
        "백만원": 1_000_000,
        "억원": 100_000_000,
        "십억원": 1_000_000_000,
        "조원": 1_000_000_000_000,
    }
)

_CANONICAL_UNITS: dict[str, str] = {
    "원": "원",
    "천원": "천원",
    "백만원": "백만원",
    "억원": "억원",
    "십억원": "십억원",
    "조원": "조원",
    "주": "주",
    "%": "%",
    "달러": "달러",
    "천달러": "천달러",
    "백만달러": "백만달러",
    "usd": "USD",
    "천usd": "천USD",
    "백만usd": "백만USD",
}
_UNIT_RE = re.compile(r"단위\s*[:：]?\s*([^)\]\n<]+)", re.IGNORECASE)
_NOTE_RE = re.compile(r"^\(?\s*주\s*[\d,\s]+\)?$")
_PLAIN_NUMBER_RE = re.compile(r"^(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)$")


def _normalizedUnitKey(value: str) -> str:
    return re.sub(r"\s+", "", value).lower()


_NORMALIZED_UNITS = {_normalizedUnitKey(alias): canonical for alias, canonical in _CANONICAL_UNITS.items()}
_UNIT_ALIASES_BY_LENGTH = tuple(sorted(_NORMALIZED_UNITS, key=len, reverse=True))


def detectUnitLabel(text: str | None) -> str | None:
    """단위 캡션에서 알려진 canonical 단위 라벨을 반환한다.

    ``억원, %`` 같은 복합 캡션은 첫 단위를 사용한다. 미지·부재 단위는
    추측하지 않고 ``None`` 을 반환한다.

    Args:
        text: ``(단위: 백만원)`` 형태의 원문 캡션.

    Returns:
        canonical 단위 라벨. 단위를 확정할 수 없으면 ``None``.

    Raises:
        없음.

    Example:
        >>> detectUnitLabel("(단위: 백만원)")
        '백만원'
    """
    if not text:
        return None
    match = _UNIT_RE.search(text)
    if match is None:
        return None
    raw = match.group(1).strip().rstrip(")] ").strip()
    key = _normalizedUnitKey(raw)
    exact = _NORMALIZED_UNITS.get(key)
    if exact is not None:
        return exact
    for alias in _UNIT_ALIASES_BY_LENGTH:
        if key.startswith(f"{alias},") or key.startswith(f"{alias}/"):
            return _NORMALIZED_UNITS[alias]
    return None


def unitScaleToWon(unitLabel: str | None) -> int | None:
    """canonical 금액 단위의 원 환산 배율을 반환한다.

    Args:
        unitLabel: ``detectUnitLabel`` 이 반환한 canonical 단위.

    Returns:
        원 환산 배율. 비금액·미지 단위는 ``None``.

    Raises:
        없음.

    Example:
        >>> unitScaleToWon("백만원")
        1000000
    """
    if unitLabel is None:
        return None
    return UNIT_SCALE_TO_WON.get(unitLabel)


def detectUnitScale(text: str | None, *, defaultUnit: str | None = None) -> int | None:
    """본문 단위의 원 환산 배율.

    단위가 없거나 미지이면 ``defaultUnit`` 을 명시한 호출자만 기본값을 받는다.

    Args:
        text: 단위 캡션 원문.
        defaultUnit: 원문에서 단위를 찾지 못했을 때 사용할 canonical 단위.

    Returns:
        원 환산 배율. 단위를 확정할 수 없으면 ``None``.

    Raises:
        없음.

    Example:
        >>> detectUnitScale("단위: 억원")
        100000000
    """
    scale = unitScaleToWon(detectUnitLabel(text))
    if scale is not None:
        return scale
    return unitScaleToWon(defaultUnit)


def parseAmount(value: Any) -> float | None:
    """DART 숫자 셀을 float로 변환한다.

    콤마·공백과 ``△``/``▲``/괄호/부호 음수를 지원한다. 주석번호와
    숫자 외 문자가 섞인 셀은 숫자를 이어 붙이지 않고 ``None`` 으로 둔다.

    Args:
        value: DART 표에서 읽은 숫자 셀.

    Returns:
        배율을 적용하지 않은 숫자. 유효한 숫자가 아니면 ``None``.

    Raises:
        없음.

    Example:
        >>> parseAmount("(1,234)")
        -1234.0
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else None

    text = str(value).strip()
    if not text or text == "-" or _NOTE_RE.fullmatch(text):
        return None

    parenthesized = text.startswith("(") and text.endswith(")")
    negativePrefix = text[0] in "△▲-−"
    if parenthesized:
        text = text[1:-1].strip()
    elif text[0] in "△▲+-−":
        text = text[1:].strip()

    compact = re.sub(r"\s+", "", text)
    if _PLAIN_NUMBER_RE.fullmatch(compact) is None:
        return None
    number = float(compact.replace(",", ""))
    return -number if parenthesized or negativePrefix else number


def parseAmountExpr(column: str | pl.Expr) -> pl.Expr:
    """``parseAmount`` 와 같은 계약의 Polars Float64 표현식을 만든다.

    Args:
        column: 변환할 컬럼 이름 또는 Polars 표현식.

    Returns:
        유효하지 않은 숫자를 null로 두는 Float64 표현식.

    Raises:
        Polars가 입력 표현식을 구성하지 못하면 해당 예외를 전달한다.

    Example:
        >>> import polars as pl
        >>> pl.DataFrame({"v": ["1,000"]}).select(parseAmountExpr("v")).item()
        1000.0
    """
    import polars as pl

    expr = pl.col(column) if isinstance(column, str) else column
    text = expr.cast(pl.Utf8).str.strip_chars()
    compact = text.str.replace_all(r"\s+", "")
    valid = compact.str.contains(
        r"^(?:[△▲+\-−]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)"
        r"|\((?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)\))$"
    )
    negative = (
        compact.str.starts_with("△")
        | compact.str.starts_with("▲")
        | compact.str.starts_with("-")
        | compact.str.starts_with("−")
        | (compact.str.starts_with("(") & compact.str.ends_with(")"))
    )
    magnitude = compact.str.strip_chars("()△▲+-−").str.replace_all(",", "").cast(pl.Float64, strict=False)
    return (
        pl.when(expr.is_null() | ~valid)
        .then(pl.lit(None).cast(pl.Float64))
        .when(negative)
        .then(-magnitude)
        .otherwise(magnitude)
    )
