"""notesBulk. stem 열거 규칙 + tsv 스트리밍 계약 (합성 zip, 네트워크/OOM 무관)."""

from __future__ import annotations

import zipfile
from datetime import date

import pytest

pytestmark = pytest.mark.unit


def test_list_notes_stems_quarterly_then_monthly():
    """2022 까지 분기, 2023 부터 직전월까지 월 stem. 당월은 미포함(미완성 zip)."""
    from dartlab.gather.edgar.notesBulk import listNotesStems

    stems = listNotesStems(sinceYear=2022, today=date(2023, 3, 15))
    assert stems == ["2022q1", "2022q2", "2022q3", "2022q4", "2023_01", "2023_02"]


def test_list_notes_stems_year_rollover():
    """12월 → 1월 롤오버."""
    from dartlab.gather.edgar.notesBulk import listNotesStems

    stems = listNotesStems(sinceYear=2023, today=date(2024, 1, 10))
    assert stems[-2:] == ["2023_11", "2023_12"]


def test_iter_notes_tsv_streams_rows(tmp_path):
    """zip 안 tsv 를 dict 행으로 스트리밍."""
    from dartlab.gather.edgar.notesBulk import iterNotesTsv

    zp = tmp_path / "x_notes.zip"
    with zipfile.ZipFile(zp, "w") as z:
        z.writestr("sub.tsv", "adsh\tcik\tform\nA-1\t320193\t10-K\n")
    rows = list(iterNotesTsv(zp, "sub.tsv"))
    assert rows == [{"adsh": "A-1", "cik": "320193", "form": "10-K"}]
