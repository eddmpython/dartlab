"""스크리닝 결과에서 숫자가 좋아 보이는 함정을 찾아 표와 함께 건넨다.

왜 필요한가. `Company.panel` 은 이미 판단 재료를 실어 보낸다(`panelInsight`). 부채비율과
자기자본비율을 계산해 표에 넣고, 업종 내 위치와 판단이 뒤집히는 지점까지 붙인다. 그런데
전 종목을 거르는 `scan` 은 조건 필드 값만 돌려준다. 같은 회사를 두 경로로 보면 판정이
갈린다.

실측(2026-08-06). "ROE 15% 이상, 부채비율 100% 미만" 으로 6 종목을 걸렀더니 3 종목이
부채비율 음수였다. 그중 001140 은 2025FY 부채총계 771억원에 지배주주지분 -169억원인
완전자본잠식이었고, 신용 dCR-B- 에 1년 부도확률 10% 였다. 자본이 마이너스라 부채비율이
-456.4% 로 계산됐고 그 음수가 "100 미만" 을 통과했다. 같은 회사를 `Company.panel` 로 열면
부채비율 -456.4%, 자기자본비율 -28.1%, 유동비율 21.0% 가 그대로 보인다. 재료가 있는
경로는 잡고 없는 경로는 놓친 것이다.

자기자본이 음수면 그것을 분모로 쓰는 지표는 값이 뒤집힌다. 부채비율은 음수가 되고, ROE 는
손실이 나도 양수가 된다(음수/음수). 001140 의 ROE 70.71% 가 그 경우다. 그래서 "수익성이
높고 빚이 적은 회사" 를 찾는 조건에 파산 직전 회사가 상위로 들어온다.

**행을 지우지 않는다.** 사용자가 준 조건은 그대로 적용하고, 성립하지 않는 비교가 섞여
있다는 사실만 적어 보낸다. 조용히 빼면 왜 없는지 알 수 없고, 그대로 두면 우량주로 읽힌다.
지어내지도 않는다. 여기서 쓰는 것은 결과 표에 이미 있는 값뿐이고 추가 조회가 없다.
"""

from __future__ import annotations

from typing import Any

# 자기자본을 분모로 쓰는 지표. 자기자본이 음수면 값의 부호가 뒤집혀 비교가 성립하지 않는다.
_EQUITY_DENOMINATOR_HINTS = ("debtratio", "부채비율", "equityratio", "자기자본비율", "roe")
# 음수가 자본잠식을 뜻하는 지표. 부채는 음수가 될 수 없으므로 부채비율 음수는 자본 음수뿐이다.
_NEGATIVE_MEANS_IMPAIRED = ("debtratio", "부채비율", "equityratio", "자기자본비율")
_MAX_LISTED_CODES = 8


def _isNumber(value: Any) -> bool:
    """bool 을 수치로 세지 않는다. 파이썬에서 True 는 1 이라 조용히 섞인다."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _matchingColumns(columns: list[str], hints: tuple[str, ...]) -> list[str]:
    """열 이름의 마지막 마디를 힌트와 맞춘다. `finance.ratio.debtRatio` 도 `부채비율` 도 잡는다."""
    matched: list[str] = []
    for column in columns:
        tail = str(column).rsplit(".", 1)[-1].casefold()
        if any(hint in tail for hint in hints):
            matched.append(column)
    return matched


def _codeOf(row: dict[str, Any]) -> str:
    """행에서 종목코드를 꺼낸다. 한글 열과 영문 열을 모두 본다."""
    for key in ("종목코드", "stockCode", "code"):
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def _formatCodes(codes: list[str]) -> str:
    """코드 목록을 한 줄로. 길면 몇 개 더 있는지 밝히고 자른다."""
    if len(codes) <= _MAX_LISTED_CODES:
        return ", ".join(codes)
    shown = ", ".join(codes[:_MAX_LISTED_CODES])
    return f"{shown} 외 {len(codes) - _MAX_LISTED_CODES}"


def impairedEquityDetail(columns: list[str], rows: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    """자본잠식이 의심되는 종목코드와, 그렇게 판정하게 만든 열 이름을 함께 돌려준다.

    열 이름을 같이 돌려주는 이유가 있다. 경고문에 "부채비율이 음수" 라고 못박아 두면
    표에 부채비율 열이 없고 자기자본비율만 있을 때 없는 근거를 말하게 된다. 모델은 그
    문장을 그대로 인용하므로, 실제로 음수였던 열만 문장에 쓴다.
    """
    targets = _matchingColumns(columns, _NEGATIVE_MEANS_IMPAIRED)
    if not targets:
        return [], []
    impaired: list[str] = []
    signals: list[str] = []
    for row in rows:
        hit = [column for column in targets if _isNumber(row.get(column)) and float(row[column]) < 0]
        if not hit:
            continue
        code = _codeOf(row)
        if code and code not in impaired:
            impaired.append(code)
        for column in hit:
            if column not in signals:
                signals.append(column)
    return impaired, signals


def impairedEquityRows(columns: list[str], rows: list[dict[str, Any]]) -> list[str]:
    """자기자본이 음수라 비교가 성립하지 않는 종목코드를 찾는다."""
    return impairedEquityDetail(columns, rows)[0]


def missingNameRows(columns: list[str], rows: list[dict[str, Any]]) -> list[str]:
    """종목명이 비어 온 종목코드를 찾는다. 상장목록에 없는 코드에서 발생한다."""
    if "종목명" not in columns and "corpName" not in columns:
        return []
    key = "종목명" if "종목명" in columns else "corpName"
    missing: list[str] = []
    for row in rows:
        if row.get(key) in (None, ""):
            code = _codeOf(row)
            if code and code not in missing:
                missing.append(code)
    return missing


def screenTrapNotes(columns: list[str], rows: list[dict[str, Any]]) -> list[str]:
    """Sig: screenTrapNotes(columns, rows) -> list[str].

    Args: 스크리닝 결과의 열 이름과 행 목록이다.
    Returns: 사람이 읽는 한 줄 경고 목록. 함정이 없으면 빈 목록이다.
    Example: `notes = screenTrapNotes(["종목코드", "부채비율"], rows)`.
    """
    if not rows:
        return []
    notes: list[str] = []

    impaired, signals = impairedEquityDetail(columns, rows)
    if impaired:
        affected = ", ".join(_matchingColumns(columns, _EQUITY_DENOMINATOR_HINTS)) or "자기자본 기준 지표"
        notes.append(
            f"자본잠식 의심 {len(impaired)}건: {_formatCodes(impaired)}. "
            f"{', '.join(signals)}이 음수인데 이 값은 자기자본이 마이너스일 때만 나옵니다. "
            f"자기자본을 분모로 쓰는 지표({affected})는 부호가 뒤집혀 이 종목들에서는 조건 비교가 성립하지 않습니다. "
            f"손실을 내도 ROE 가 양수로 나옵니다. 수치가 좋아 보이는 쪽이 아니라 위험한 쪽입니다. "
            f"각 종목은 Company.panel 의 재무상태표로 자기자본을 직접 확인하세요."
        )

    missing = missingNameRows(columns, rows)
    if missing:
        notes.append(
            f"종목명이 비어 있는 행 {len(missing)}건: {_formatCodes(missing)}. "
            f"상장목록에 없는 코드입니다. 이름을 얻으려고 종목마다 개별 조회를 돌리지 마세요."
        )
    return notes
