"""판정 엔진의 결과 dict 를 모델이 읽는 본문과 인용 가능한 근거로 편다.

실측(2026-08-06)으로 드러난 비대칭이다. `Company.panel` 은 표와 파생 지표와 업종 기준이
붙은 본문 1810 자를 건네는데, 정작 판정을 내는 `Company.analysis` 와 `Company.quant` 와
`Company.credit` 은 본문이 0 자다. 요약은 "실행 완료" 다섯 글자이고, 내용은 9184 자짜리
중첩 dict 로 넘어간다.

결과가 그대로 나타났다. 같은 배터리에서 panel 경로로 답한 질문은 근거 39 건이었고,
analysis 와 quant 경로로 답한 질문은 3226 자를 쓰고도 근거 3 건에 인용 2 건이었다. 답변에
적힌 수치가 맞는데도 확인할 방법이 없는 상태다.

모델이 읽는 것은 본문이다. dict 안에만 있는 것은 없는 것과 같다. 신용 등급과 산업 국면
때 배운 것과 정확히 같은 실패이고, 같은 방법으로 고친다. **지어내지 않고 이미 있는 것을
옮겨 적는다.** 계산도 해석도 여기서 하지 않는다.

블록마다 `history` 배열이 있는 것이 이 엔진들의 공통 모양이라, 그것을 기간 x 지표 표로
편다. 표를 그리면 그 표를 가리키는 근거도 함께 발급한다. 본문만 주고 근거를 안 주면
답변은 읽히되 인용되지 않는다.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from dartlab.ai.contracts import Ref

# 한 블록에서 보일 기간 수. 더 보이면 표가 읽히지 않고 payload 예산만 먹는다.
_MAX_PERIODS = 8
# 한 표에 보일 지표 수. 기간 열은 여기에 포함하지 않는다.
_MAX_METRICS = 8
# 본문 전체 상한. 소비하는 CLI 가 받아 주는 크기 안에 있어야 결과가 통째로 버려지지 않는다.
_MAX_BODY_CHARS = 6000
# 최상위 스칼라를 보일 개수. 판정 엔진은 결론을 여기 담아 보내므로 넉넉히 둔다.
_MAX_SCALARS = 16
# 기간을 뜻하는 키 이름 후보. 엔진마다 다른 이름을 쓴다.
_PERIOD_KEYS = ("period", "연도", "date", "asOf", "기간")
# 표로 펼 값이 아니라 상태를 말하는 키.
_STATUS_KEYS = ("status", "assessmentStatus", "available", "zone", "grade", "score", "interpretation", "reason")
# 기간처럼 생긴 키. 2025 / 2025FY / 2025Q3 / 2025-03 을 받는다.
_PERIOD_PATTERN = re.compile(r"^(?:19|20)\d{2}(?:FY|Q[1-4]|-\d{2})?$")


def _periodKey(row: Mapping[str, Any]) -> str | None:
    """행에서 기간 열 이름을 고른다. 없으면 None 이다."""
    for key in _PERIOD_KEYS:
        if key in row:
            return key
    return None


def _formatCell(value: Any) -> str:
    """값 하나를 표 한 칸으로. 큰 금액은 조원 억원으로 줄여 읽게 한다."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "예" if value else "아니오"
    if isinstance(value, (int, float)):
        number = float(value)
        if abs(number) >= 1e12:
            return f"{number / 1e12:,.1f}조원"
        if abs(number) >= 1e8:
            return f"{number / 1e8:,.0f}억원"
        if number == int(number) and abs(number) < 1e6:
            return f"{int(number):,}"
        return f"{number:,.2f}"
    text = str(value)
    return text[:60] if len(text) > 60 else text


def _omittedNote(kind: str, total: int, shown: int) -> list[str]:
    """잘라낸 것을 밝힌다.

    조용히 자르면 모델이 보인 것을 전부로 읽고, 없는 것을 없다고 단정한다. 실측
    (2026-08-06)에서 모델은 `assessmentStatus partial` 을 읽고 스스로 확신을 좁혔다.
    같은 판단을 하려면 무엇이 잘렸는지 알아야 한다.
    """
    return [f"({kind} {total} 개 중 {shown} 개만 보였습니다.)"] if total > shown else []


def _historyTable(history: Sequence[Any]) -> list[str]:
    """기간별 dict 목록을 기간 x 지표 markdown 표로 편다. 표가 안 되면 빈 목록이다."""
    allRows = [row for row in history if isinstance(row, Mapping)]
    rows = allRows[:_MAX_PERIODS]
    if not rows:
        return []
    periodKey = _periodKey(rows[0])
    if periodKey is None:
        return []
    metrics: list[str] = []
    for row in rows:
        for key, value in row.items():
            if key == periodKey or key in metrics:
                continue
            if isinstance(value, (Mapping, list, tuple)):
                continue
            metrics.append(key)
    shownMetrics = metrics[:_MAX_METRICS]
    if not shownMetrics:
        return []
    periods = [str(row.get(periodKey)) for row in rows]
    lines = ["| 지표 | " + " | ".join(periods) + " |", "|---|" + "|".join(["---:"] * len(periods)) + "|"]
    for metric in shownMetrics:
        cells = [_formatCell(row.get(metric)) for row in rows]
        if all(cell == "-" for cell in cells):
            continue
        lines.append(f"| {metric} | " + " | ".join(cells) + " |")
    if len(lines) <= 2:
        return []
    lines.extend(_omittedNote("기간", len(allRows), len(rows)))
    lines.extend(_omittedNote("지표", len(metrics), len(shownMetrics)))
    return lines


def _periodMapTable(block: Mapping[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    """{기간: 값} 모양을 한 줄짜리 표로 편다. 엔진마다 시계열을 이 모양으로도 준다."""
    keys = [str(key) for key in block]
    if len(keys) < 2 or not all(_PERIOD_PATTERN.match(key) for key in keys):
        return [], []
    if any(isinstance(value, (Mapping, list, tuple)) for value in block.values()):
        return [], []
    periods = sorted(keys, reverse=True)[:_MAX_PERIODS]
    lines = [
        "| 기간 | " + " | ".join(periods) + " |",
        "|---|" + "|".join(["---:"] * len(periods)) + "|",
        "| 값 | " + " | ".join(_formatCell(block[period]) for period in periods) + " |",
        *_omittedNote("기간", len(keys), len(periods)),
    ]
    rows = [{"period": period, "value": block[period]} for period in periods]
    return lines, rows


def _tableBlocks(payload: Mapping[str, Any]) -> list[tuple[str, list[str], list[dict[str, Any]]]]:
    """표로 펼 수 있는 블록만 (이름, 표 줄, 근거용 행) 으로 모은다.

    본문과 근거가 같은 판정을 쓰도록 여기 한 곳에서만 고른다. 두 곳에서 따로 고르면
    본문에는 있는데 인용할 근거가 없는 표가 생긴다.
    """
    blocks: list[tuple[str, list[str], list[dict[str, Any]]]] = []
    for name, block in payload.items():
        if not isinstance(block, Mapping):
            continue
        history = block.get("history")
        if isinstance(history, Sequence) and not isinstance(history, (str, bytes)):
            # 자르지 않고 통째로 넘긴다. 여기서 먼저 자르면 몇 개를 잘랐는지 알 수 없어
            # 잘라낸 사실을 밝힐 수 없다.
            lines = _historyTable(history)
            if lines:
                rows = [row for row in history if isinstance(row, Mapping)][:_MAX_PERIODS]
                blocks.append((name, lines, [dict(row) for row in rows]))
                continue
        lines, rows = _periodMapTable(block)
        if lines:
            blocks.append((name, lines, rows))
    return blocks


def _blockRefId(apiRef: str, target: str | None, name: str) -> str:
    """표 하나를 가리키는 근거 id. 본문과 근거가 같은 이름을 쓰도록 여기서만 만든다."""
    return ":".join(part for part in ("table", apiRef, str(target or ""), name) if part)


def _scalarLines(payload: Mapping[str, Any]) -> list[str]:
    """최상위 스칼라 값. 판정 엔진은 신호와 강도를 여기에 담아 보낸다."""
    parts = [
        f"{key} {_formatCell(value)}"
        for key, value in payload.items()
        if not isinstance(value, (Mapping, list, tuple, set)) and value is not None
    ]
    shown = parts[:_MAX_SCALARS]
    return [f"- {part}." for part in shown] + [f"- {note}" for note in _omittedNote("값", len(parts), len(shown))]


def _statusLine(name: str, block: Mapping[str, Any]) -> str:
    """상태 키만 모아 한 줄로. 못 재는 것을 못 잰다고 적어야 모델이 지어내지 않는다."""
    parts = []
    for key in _STATUS_KEYS:
        if key not in block:
            continue
        value = block[key]
        if isinstance(value, (Mapping, list, tuple)) or value is None:
            continue
        parts.append(f"{key} {_formatCell(value)}")
    return f"- {name}: {', '.join(parts)}." if parts else ""


def engineResultMarkdown(apiRef: str, target: str | None, payload: Any) -> str:
    """엔진 결과를 모델이 읽는 본문으로 편다.

    Capabilities:
        블록마다 `history` 배열을 가진 판정 엔진 결과를 기간 x 지표 표와 상태 줄로 편다.
        계산이나 해석은 하지 않고 이미 있는 값을 옮겨 적기만 한다.

    Args:
        apiRef: 호출된 공개 계약 이름. 제목에 쓴다.
        target: 축 이름. 없으면 생략한다.
        payload: 엔진이 돌려준 직렬화된 결과.

    Returns:
        str: 펼 것이 없으면 빈 문자열이다.

    Example:
        `body = engineResultMarkdown("Company.analysis", "이익품질", payload)`
    """
    if not isinstance(payload, Mapping):
        return ""
    heading = f"## {apiRef}" + (f" {target}" if target else "")
    blocks = _tableBlocks(payload)
    tabled = {name for name, _lines, _rows in blocks}
    statuses = [
        line
        for name, block in payload.items()
        if isinstance(block, Mapping) and name not in tabled and (line := _statusLine(name, block))
    ]
    scalars = _scalarLines(payload)
    if not blocks and not statuses and not scalars:
        return ""
    lines = [heading, ""]
    for name, table, _rows in blocks:
        # 제목에 근거 id 를 같이 적는다. 실측(2026-08-06)에서 모델이 표 이름은 본문에 쓰면서
        # 인용은 못 했다. 가리킬 이름을 눈앞에 두지 않으면 인용은 비싼 일이 된다.
        lines.append(f"### {name} (`{_blockRefId(apiRef, target, name)}`)")
        lines.extend(table)
        lines.append("")
    if scalars:
        lines.append("### 핵심 값")
        lines.extend(scalars)
        lines.append("")
    if statuses:
        lines.append("### 상태와 한계")
        lines.extend(statuses)
        lines.append("")
    body = "\n".join(lines)
    if len(body) <= _MAX_BODY_CHARS:
        return body
    return body[:_MAX_BODY_CHARS] + "\n(본문이 길어 여기서 끊었습니다.)\n"


# 계단형 판정. 값이 바뀐 지점이 이보다 많으면 계단이 아니라 그냥 변동하는 계열이다.
_MAX_STEP_ROWS = 24
# 고유값이 행 수의 이 분의 일 이하일 때 계단으로 본다.
_STEP_SPARSITY = 10


def _isPlainNumber(value: Any) -> bool:
    """bool 을 수치로 세지 않는다. 파이썬에서 True 는 1 이라 조용히 섞인다."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _stepValueColumn(allRows: list[Mapping[str, Any]], columns: list[str]) -> str | None:
    """같은 값이 길게 이어지는 수치 열 하나를 찾는다. 없으면 None 이다."""
    if len(columns) != 2:
        return None
    for column in columns:
        values = [row.get(column) for row in allRows]
        if not values or not all(_isPlainNumber(value) for value in values):
            continue
        if len({float(value) for value in values}) <= max(2, len(values) // _STEP_SPARSITY):
            return column
    return None


def _previewRows(allRows: list[Mapping[str, Any]], columns: list[str]) -> tuple[list[Mapping[str, Any]], bool]:
    """미리보기 행을 고른다. 계단형 시계열이면 값이 바뀐 지점을 고른다.

    앞에서 여덟 행을 자르는 것은 대부분의 표에서 맞다. 그런데 며칠씩 같은 값이 이어지는
    계열에서는 앞부분이 정확히 아무 일도 없는 구간이다. 실측(2026-08-06): 3 년 기준금리
    946 행을 받은 답변이 본문에서 본 것은 2024-01-01 부터 여드레치이고 값이 전부 3.50 이었다.
    그래서 모델은 변경 시점을 찾으려 기간을 쪼개 열한 번 다시 불렀다. 표가 쓸모없으면
    호출로 메운다.

    값이 바뀐 지점만 남기면 946 행이 몇 줄이 되고 그 몇 줄이 질문의 답이다. 크기는 줄고
    정보는 는다. 마지막 시점은 값이 안 바뀌었어도 반드시 싣는다. "지금 얼마인가" 가 거의
    항상 질문의 일부다.
    """
    if len(allRows) <= _MAX_PERIODS:
        return allRows, False
    valueColumn = _stepValueColumn(allRows, columns)
    if valueColumn is None:
        return allRows[:_MAX_PERIODS], False
    picked: list[Mapping[str, Any]] = []
    sentinel = object()
    previous: Any = sentinel
    for row in allRows:
        current = row.get(valueColumn)
        if previous is sentinel or current != previous:
            picked.append(row)
            previous = current
    if picked and picked[-1] is not allRows[-1]:
        picked.append(allRows[-1])
    if len(picked) <= 1 or len(picked) > _MAX_STEP_ROWS:
        return allRows[:_MAX_PERIODS], False
    return picked, True


def frameMarkdown(apiRef: str, target: str | None, payload: Any) -> str:
    """격자 결과의 미리보기 행을 표로 편다.

    Capabilities:
        `{_type: DataFrame, columns, rows}` 모양을 markdown 표로 편다. 옛 계약은 행 수와
        열 이름만 본문에 줘서 값이 하나도 보이지 않았다.

    Args:
        apiRef: 호출된 공개 계약 이름.
        target: 호출 범위.
        payload: 직렬화된 격자.

    Returns:
        str: 행이 없으면 빈 문자열이다.

    Example:
        `body = frameMarkdown("Company.credit", "005930", payload)`
    """
    if not isinstance(payload, Mapping):
        return ""
    allRows = [row for row in (payload.get("rows") or []) if isinstance(row, Mapping)]
    allColumns = [str(column) for column in (payload.get("columns") or [])]
    columns = allColumns[:_MAX_METRICS]
    rows, stepped = _previewRows(allRows, columns)
    # 직렬화 시점에 이미 변경 지점만 고른 경우가 있다. 그때 여기서 다시 고를 것은 없지만
    # 무엇을 본 것인지는 그대로 말해야 한다. 앞부분을 본 것으로 읽히면 나머지를 모른다고
    # 판단해 다시 부른다.
    stepped = stepped or str(payload.get("previewMode") or "") == "valueChanges"
    if not rows or not columns:
        return ""
    heading = f"## {apiRef}" + (f" {target}" if target else "")
    lines = [
        heading,
        "",
        "| " + " | ".join(columns) + " |",
        "|" + "|".join(["---"] * len(columns)) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_formatCell(row.get(column)) for column in columns) + " |")
    total = payload.get("rowCount")
    shown = len(rows)
    lines.append("")
    if stepped:
        lines.append(
            f"전체 {total if isinstance(total, int) else len(allRows)}행 중 값이 바뀐 지점 {shown}개만 보였습니다. "
            f"나머지 행은 직전 값과 같습니다."
        )
    elif isinstance(total, int) and total > shown:
        lines.append(f"전체 {total}행 중 {shown}행만 보였습니다.")
    lines.extend(_omittedNote("열", len(allColumns), len(columns)))
    lines.append("")
    body = "\n".join(lines)
    if len(body) <= _MAX_BODY_CHARS:
        return body
    return body[:_MAX_BODY_CHARS] + "\n(본문이 길어 여기서 끊었습니다.)\n"


def engineResultRefs(apiRef: str, target: str | None, payload: Any) -> list[Ref]:
    """본문에 표로 편 블록마다 인용 가능한 근거를 발급한다.

    Capabilities:
        표로 그려진 블록 하나가 근거 하나가 된다. 본문만 주고 근거를 안 주면 답변은
        읽히되 인용되지 않는다. 실측에서 이 엔진들의 근거는 실행 영수증 하나뿐이었다.

    Args:
        apiRef: 호출된 공개 계약 이름.
        target: 호출 범위. 이 경로에서는 종목코드가 실려 오므로 그대로 ref id 에 넣어
            회사별로 구분한다.
        payload: 엔진이 돌려준 직렬화된 결과.

    Returns:
        list[Ref]: 표로 편 블록이 없으면 빈 목록이다.

    Example:
        `refs = engineResultRefs("analysis.이익품질", "005930", payload)`
    """
    if not isinstance(payload, Mapping):
        return []
    scope = str(target or "")
    return [
        Ref(
            id=_blockRefId(apiRef, scope, name),
            kind="tableRef",
            title=f"{apiRef} {target or ''} {name}".strip(),
            source=apiRef,
            payload={"apiRef": apiRef, "axis": target or None, "block": name, "history": rows},
        )
        for name, _lines, rows in _tableBlocks(payload)
    ]


__all__ = ["engineResultMarkdown", "engineResultRefs", "frameMarkdown"]
