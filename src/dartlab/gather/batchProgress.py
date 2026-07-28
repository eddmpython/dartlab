"""배치 수집 진행 표시 조립.

DART 배치와 EDGAR 배치는 워커를 N 개 띄우고 rich ``Live`` 로 워커별 한 줄 + 전체
진행 bar 를 갱신한다. 두 배치가 그 표를 각자 조립하고 있었는데 칸 수, 색, bar 폭,
백분율 서식이 글자까지 같았다. 표 모양이 곧 화면이라 한쪽만 손대면 두 화면이 갈라진다.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.table import Table


def buildWorkerTable(numWorkers: int, workerLines: Sequence[str], completed: int, total: int) -> Table:
    """워커 상태 줄과 전체 진행 bar 를 rich Table 로 조립한다.

    Capabilities:
        워커 인덱스 열(``W0``, ``W1`` ...) 과 상태 줄, 그리고 50 칸 진행 bar 한 줄을
        가진 grid Table 을 만든다.

    AIContext:
        배치 수집이 ``rich.live.Live`` 로 화면을 갱신할 때마다 불린다. 데이터가 아니라
        화면 조립이라 반환값을 근거로 삼지 않는다.

    Guide:
        호출자는 ``workerLines`` 리스트를 제자리에서 갱신하고 이 함수를 다시 불러
        새 Table 을 받는다. ``total`` 이 0 이면 백분율은 0 으로 둔다.

    When:
        ``batchCollect`` (DART) 와 ``batchCollectEdgar`` (EDGAR) 의 progress 모드에서.

    How:
        ``Table.grid`` 에 워커 수만큼 행을 넣고 마지막에 bar 행을 덧붙인다.

    Requires:
        ``rich`` 패키지. 함수 안에서 import 하므로 progress 모드가 아니면 부담이 없다.

    Args:
        numWorkers: 표시할 워커 수. ``workerLines`` 앞에서부터 이 개수만큼 읽는다.
        workerLines: 워커별 현재 상태 줄.
        completed: 지금까지 끝난 항목 수.
        total: 전체 항목 수. 0 이면 백분율을 0 으로 둔다.

    Returns:
        ``rich.table.Table``. ``Live.update`` 에 그대로 넘긴다.

    Raises:
        IndexError: ``workerLines`` 가 ``numWorkers`` 보다 짧을 때.

    Example:
        >>> table = buildWorkerTable(2, ["대기", "수집 중"], 3, 10)
        >>> type(table).__name__
        'Table'

    SeeAlso:
        ``dartlab.gather.dart.batch`` . DART 배치 수집.
        ``dartlab.gather.edgar.batch`` . EDGAR 배치 수집.
    """
    from rich.table import Table
    from rich.text import Text

    tbl = Table.grid(padding=(0, 1))
    tbl.add_column(style="bold cyan", width=4)
    tbl.add_column()

    for i in range(numWorkers):
        tbl.add_row(f"W{i}", workerLines[i])

    pct = completed / total * 100 if total else 0
    filled = int(pct / 2)
    barStr = "█" * filled + "░" * (50 - filled)
    barText = Text(f"[{barStr}] {completed}/{total} ({pct:.0f}%)")
    tbl.add_row("", barText)
    return tbl
