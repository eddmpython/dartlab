"""brokerage.io 단위 테스트 — 월별 파티션 write + report_id dedup + round-trip (네트워크 0)."""

from __future__ import annotations

import pytest

from dartlab.gather.sources.brokerage.io import loadLocal, writeMonthly
from dartlab.gather.sources.brokerage.schema import ReportMeta, toDataFrame

pytestmark = pytest.mark.unit


def test_write_partitions_by_month(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DARTLAB_DATA_DIR", str(tmp_path))
    items = [
        ReportMeta("nh", "NH투자", "A", "u1", "2026-06-26", ticker="005930"),
        ReportMeta("nh", "NH투자", "B", "u2", "2026-05-15"),
    ]
    changed = writeMonthly(toDataFrame(items))
    assert set(changed) == {"202606.parquet", "202605.parquet"}
    assert loadLocal().height == 2


def test_dedup_on_rerun(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DARTLAB_DATA_DIR", str(tmp_path))
    items = [ReportMeta("nh", "NH투자", "A", "u1", "2026-06-26")]
    writeMonthly(toDataFrame(items))
    writeMonthly(toDataFrame(items))  # 재수집 — 같은 report_id
    assert loadLocal().height == 1


def test_empty(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DARTLAB_DATA_DIR", str(tmp_path))
    assert writeMonthly(toDataFrame([])) == []
    assert loadLocal().height == 0


def test_merge_keeps_resolved_ticker_when_rerun_has_none(tmp_path, monkeypatch) -> None:
    """corpCode 조회가 실패한 run 의 빈 ticker 가 앞서 해소된 ticker 를 지우지 않는다."""
    monkeypatch.setenv("DARTLAB_DATA_DIR", str(tmp_path))
    writeMonthly(toDataFrame([ReportMeta("nh", "NH투자", "A", "u1", "2026-06-26", ticker="005930")]))
    writeMonthly(toDataFrame([ReportMeta("nh", "NH투자", "A", "u1", "2026-06-26")]))
    df = loadLocal()
    assert df.height == 1 and df["ticker"].to_list() == ["005930"]


def _hfMonth(tmp_path, monkeypatch, *, existing: dict, failWith: Exception | None = None):
    """hf_hub_download 를 흉내 낸다. existing 의 달은 그 행으로 월 파일을 쓰고, 나머지는 404."""
    import huggingface_hub
    from huggingface_hub.utils import EntryNotFoundError

    calls: list[str] = []

    def fakeDownload(*, repo_id, repo_type, filename, local_dir, token=None):
        calls.append(filename)
        if failWith is not None:
            raise failWith
        ym = filename.rsplit("/", 1)[-1].removesuffix(".parquet")
        if ym not in existing:
            raise EntryNotFoundError(f"404 {filename}")
        out = tmp_path / filename
        out.parent.mkdir(parents=True, exist_ok=True)
        toDataFrame(existing[ym]).write_parquet(out)
        return str(out)

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", fakeDownload)
    return calls


def test_seed_from_hf_keeps_rows_outside_this_fetch(tmp_path, monkeypatch) -> None:
    """러너는 빈 디스크라 HF 의 같은 달 파일을 받아 병합해야 첫 페이지 밖의 행이 남는다.

    예전엔 받지 않아 2026-10-12 HF 에 8 월 7 행, 9 월 17 행만 남아 있었다.
    """
    from dartlab.gather.sources.brokerage.io import seedMonthsFromHf

    monkeypatch.setenv("DARTLAB_DATA_DIR", str(tmp_path))
    older = [ReportMeta("nh", "NH투자", f"old{i}", f"o{i}", "2026-09-0" + str(i + 1)) for i in range(3)]
    calls = _hfMonth(tmp_path, monkeypatch, existing={"202609": older})
    fetched = toDataFrame(
        [ReportMeta("nh", "NH투자", "new", "n1", "2026-09-30"), ReportMeta("nh", "NH투자", "oct", "n2", "2026-10-01")]
    )

    assert seedMonthsFromHf(fetched) == ["202609.parquet"]
    writeMonthly(fetched)

    assert sorted(calls) == ["research/brokerage/202609.parquet", "research/brokerage/202610.parquet"]
    assert loadLocal().height == 5  # HF 9 월 3 행 + 이번 9 월 1 행 + 10 월 1 행


def test_seed_skips_months_already_local_and_raises_on_hf_failure(tmp_path, monkeypatch) -> None:
    """로컬에 있는 달은 받지 않고, 404 가 아닌 HF 실패는 올려 병합 base 없는 덮어쓰기를 막는다."""
    from dartlab.gather.sources.brokerage.io import seedMonthsFromHf

    monkeypatch.setenv("DARTLAB_DATA_DIR", str(tmp_path))
    fetched = toDataFrame([ReportMeta("nh", "NH투자", "A", "u1", "2026-06-26")])
    writeMonthly(fetched)
    calls = _hfMonth(tmp_path, monkeypatch, existing={}, failWith=PermissionError("401"))
    assert seedMonthsFromHf(fetched) == [] and calls == []

    other = toDataFrame([ReportMeta("nh", "NH투자", "B", "u2", "2026-07-01")])
    with pytest.raises(PermissionError):
        seedMonthsFromHf(other)
