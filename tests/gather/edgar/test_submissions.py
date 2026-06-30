"""providers/edgar/openapi/submissions.py mirror smoke — P6."""

import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.core.edgarClient  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_filings_frame_callable() -> None:
    """filingsFrame() callable smoke."""
    from dartlab.gather.edgar.submissions import filingsFrame

    assert callable(filingsFrame)


def test_find_regular_filings_callable() -> None:
    """findRegularFilings() callable smoke."""
    from dartlab.gather.edgar.submissions import findRegularFilings

    assert callable(findRegularFilings)


def test_get_submissions_json_callable() -> None:
    """getSubmissionsJson() callable smoke."""
    from dartlab.gather.edgar.submissions import getSubmissionsJson

    assert callable(getSubmissionsJson)


def test_merge_submission_filings_callable() -> None:
    """mergeSubmissionFilings() callable smoke."""
    from dartlab.gather.edgar.submissions import mergeSubmissionFilings

    assert callable(mergeSubmissionFilings)


def _syntheticSubmissions() -> dict:
    """합성 submissions — recent 블록에 정기(10-K)·수시(8-K·DEF 14A·Form 4) + 구년도(2019) 혼재."""
    return {
        "cik": "0000320193",
        "name": "Apple Inc.",
        "filings": {
            "recent": {
                "form": ["10-K", "8-K", "DEF 14A", "4", "8-K"],
                "filingDate": ["2025-11-01", "2025-10-15", "2025-03-01", "2025-02-10", "2019-05-01"],
                "accessionNumber": [
                    "0000320193-25-001",
                    "0000320193-25-002",
                    "0000320193-25-003",
                    "0000320193-25-004",
                    "0000320193-19-009",
                ],
                "primaryDocument": ["aapl.htm", "8k.htm", "proxy.htm", "form4.xml", "old8k.htm"],
                "primaryDocDescription": ["10-K", "", "Proxy", "", ""],
            }
        },
    }


def test_find_all_filings_includes_nonregular() -> None:
    """findAllFilings — 수시(8-K·DEF 14A·Form 4) 포함, sinceYear 로 구년도(2019) 컷, 정렬·메타 정확."""
    from dartlab.gather.edgar.submissions import findAllFilings

    rows = findAllFilings(_syntheticSubmissions(), sinceYear=2023)
    forms = {r["form"] for r in rows}
    assert {"8-K", "DEF 14A", "4"} <= forms  # 수시 포함
    assert "10-K" in forms  # findAllFilings 자체는 정기도 반환(제외는 빌드/런타임 몫)
    assert all(r["filing_date"][:4] >= "2023" for r in rows)  # 2019 컷
    assert len(rows) == 4  # 5건 중 2019 1건 제외
    # filing_date ASC 정렬
    dates = [r["filing_date"] for r in rows]
    assert dates == sorted(dates)
    # 메타 정확 — cik·entityName·url
    r = next(r for r in rows if r["form"] == "8-K" and r["filing_date"] == "2025-10-15")
    assert r["cik"] == "0000320193"
    assert r["entityName"] == "Apple Inc."
    assert r["accession_no"] == "0000320193-25-002"
    assert r["filing_url"].endswith("/8k.htm")


def test_find_all_filings_empty_recent() -> None:
    """recent 블록 부재 → 빈 list (격리)."""
    from dartlab.gather.edgar.submissions import findAllFilings

    assert findAllFilings({"cik": "0000000001", "filings": {}}, sinceYear=2023) == []
