"""Console output helpers for CLI commands — Rich 기반."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    import polars as pl

_console = Console()
_err_console = Console(stderr=True)


def get_console() -> Console:
    """공용 Rich Console 반환."""
    return _console


def print_error(message: str) -> None:
    _err_console.print(f"[bold red]오류:[/] {message}")


def print_info(message: str = "") -> None:
    _console.print(message)


def print_warning(message: str) -> None:
    _err_console.print(f"[bold yellow]경고:[/] {message}")


def _is_numeric_col(dtype_str: str) -> bool:
    """Polars dtype 문자열이 숫자형인지 판별."""
    return bool(re.search(r"(Int|UInt|Float|Decimal)", dtype_str))


def _format_number(val) -> str:
    """숫자 포맷: 천단위 쉼표, 소수점 유지."""
    if val is None:
        return ""
    if isinstance(val, float):
        if val != val:  # NaN
            return ""
        if val == int(val) and abs(val) < 1e15:
            return f"{int(val):,}"
        return f"{val:,.2f}"
    if isinstance(val, int):
        return f"{val:,}"
    return str(val)


def print_dataframe(
    df: "pl.DataFrame",
    *,
    title: str | None = None,
    max_rows: int = 50,
) -> None:
    """Polars DataFrame을 Rich Table로 렌더링.

    - 숫자 우정렬, 천단위 쉼표
    - 양수/음수 색상 구분
    - 최대 max_rows행 표시
    """
    if df.is_empty():
        _console.print("[dim]데이터가 없습니다.[/]")
        return

    table = Table(title=title, show_lines=False, padding=(0, 1))
    schema = df.schema

    for col_name in df.columns:
        dtype_str = str(schema[col_name])
        justify = "right" if _is_numeric_col(dtype_str) else "left"
        table.add_column(col_name, justify=justify, no_wrap=True)

    display_df = df.head(max_rows)
    for row in display_df.iter_rows(named=True):
        cells = []
        for col_name in df.columns:
            val = row[col_name]
            dtype_str = str(schema[col_name])
            if _is_numeric_col(dtype_str):
                formatted = _format_number(val)
                if isinstance(val, (int, float)) and val is not None:
                    if isinstance(val, float) and val != val:
                        cells.append("")
                    elif val < 0:
                        cells.append(f"[red]{formatted}[/]")
                    else:
                        cells.append(formatted)
                else:
                    cells.append(formatted)
            elif val is None:
                cells.append("")
            else:
                cells.append(str(val))
        table.add_row(*cells)

    _console.print(table)
    if len(df) > max_rows:
        _console.print(f"[dim]... {len(df) - max_rows}행 추가 (총 {len(df)}행)[/]")


def print_search_results(results: "pl.DataFrame") -> None:
    """dartlab.search() 결과를 Rich Table로 표시."""
    print_dataframe(results, title="검색 결과")
