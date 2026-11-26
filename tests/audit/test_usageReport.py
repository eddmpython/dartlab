"""usageReport 의 집계 계산 단위 테스트. 네트워크를 쓰지 않는다."""

from __future__ import annotations

import csv
import datetime as dt

import pytest

from tests.audit.usageReport import (
    appendHistory,
    countByMonth,
    historyRows,
    releaseDownloads,
    render,
    summarizePypiSystem,
    weekStart,
)

pytestmark = pytest.mark.unit

TODAY = dt.date(2026, 11, 27)  # 금요일. 이 주의 월요일은 11-23.


def testWeekStartIsMonday():
    assert weekStart(dt.date(2026, 11, 27)) == dt.date(2026, 11, 23)
    assert weekStart(dt.date(2026, 11, 23)) == dt.date(2026, 11, 23)


def testSummarizePypiSeparatesHumanOsAndDropsOpenWeek():
    rows = [
        {"category": "Windows", "date": "2026-11-26", "downloads": 3},  # 이번 주: 30일 합에는 들고 주별에는 빠진다
        {"category": "Darwin", "date": "2026-11-20", "downloads": 2},  # 11-16 주
        {"category": "Linux", "date": "2026-11-20", "downloads": 50},  # 사람 설치로 세지 않는다
        {"category": "null", "date": "2026-11-10", "downloads": 4},
        {"category": "Windows", "date": "2026-10-01", "downloads": 9},  # 30일 밖
        {"category": "Windows", "date": "2026-11-27", "downloads": 7},  # 기준일 당일은 빼고 센다
    ]
    out = summarizePypiSystem(rows, TODAY, days=30, weeks=2)
    assert out["recentByOs"] == {"Windows": 3, "Darwin": 2, "Linux": 50, "null": 4}
    assert out["recentTotal"] == 59
    assert out["recentHuman"] == 5
    assert out["weeklyHuman"] == [(dt.date(2026, 11, 9), 0), (dt.date(2026, 11, 16), 2)]


def testCountByMonthFillsEmptyMonthsAcrossYear():
    stamps = ["2026-01-03T00:00:00Z", "2025-12-31T10:00:00Z", "2025-12-01T00:00:00Z", "", "2025-06-01T00:00:00Z"]
    assert countByMonth(stamps, months=3, today=dt.date(2026, 1, 15)) == [
        ("2025-11", 0),
        ("2025-12", 2),
        ("2026-01", 1),
    ]


def testReleaseDownloadsSumsAssetsNewestFirst():
    releases = [
        {"tag_name": "v1", "published_at": "2026-03-01T00:00:00Z", "assets": [{"download_count": 2}]},
        {
            "tag_name": "v2",
            "published_at": "2026-04-10T00:00:00Z",
            "assets": [{"download_count": 5}, {"download_count": 1}],
        },
        {"tag_name": "v0", "published_at": "2026-02-01T00:00:00Z", "assets": []},
    ]
    assert releaseDownloads(releases) == [("v2", "2026-04-10", 6), ("v1", "2026-03-01", 2), ("v0", "2026-02-01", 0)]


def _report() -> dict:
    return {
        "errors": ["huggingface: ConnectError"],
        "pypi": {
            "recentByOs": {"Linux": 10, "Windows": 2},
            "recentTotal": 12,
            "recentHuman": 2,
            "weeklyHuman": [(dt.date(2026, 11, 16), 2)],
        },
        "github": {
            "stars": 5,
            "forks": 1,
            "starsByMonth": [("2026-11", 1)],
            "forksByMonth": [("2026-11", 0)],
            "traffic": {"views": 9, "viewUniques": 4, "clones": 30, "cloneUniques": 3, "referrers": []},
        },
        "desktop": [("v2", "2026-04-10", 6), ("v1", "2026-03-01", 2)],
    }


def testHistoryRowsKeepOnlyWindowedAndCumulativeValues():
    rows = historyRows(_report(), TODAY)
    keys = {(r["source"], r["metric"], r["period"]): r["value"] for r in rows}
    assert keys[("pypi", "downloads.Windows", "last30d")] == 2
    assert keys[("github", "viewUniques", "last14d")] == 4
    assert keys[("desktop", "downloads", "total")] == 8
    assert ("huggingface", "downloads", "last30d") not in keys  # 읽지 못한 값은 0 으로 쓰지 않는다
    assert {r["fetchedOn"] for r in rows} == {"2026-11-27"}


def testAppendHistorySkipsSameDayDuplicates(tmp_path):
    path = tmp_path / "usage" / "history.csv"
    rows = historyRows(_report(), TODAY)
    appendHistory(path, rows)
    appendHistory(path, rows)
    with path.open(encoding="utf-8", newline="") as handle:
        stored = list(csv.DictReader(handle))
    assert len(stored) == len(rows)
    nextDay = historyRows(_report(), TODAY + dt.timedelta(days=1))
    appendHistory(path, nextDay)
    with path.open(encoding="utf-8", newline="") as handle:
        assert len(list(csv.DictReader(handle))) == 2 * len(rows)


def testRenderShowsHumanEstimateAndUnreadSource():
    text = render(_report(), TODAY)
    assert "사람 설치 추정(Windows+macOS): 2번" in text
    assert "누적 다운로드 8번" in text
    assert "[읽지 못함] huggingface: ConnectError" in text
    assert "[HF 데이터]" not in text
