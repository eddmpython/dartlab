"""ex21Build. 자회사 scan 빌더 단위 (합성 payload + fetch 모킹, 네트워크/OOM 무관)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_latest_tenk_accession_first_wins(monkeypatch, tmp_path):
    """recent 블록 최신순에서 첫 10-K 채택."""
    import dartlab.scan.builders.edgar.report.ex21Build as mod

    def _fakeIter(zp, *, recentOnly=True):
        yield (
            "0000320193",
            {
                "filings": {
                    "recent": {
                        "form": ["8-K", "10-K", "10-K"],
                        "accessionNumber": ["a-8k", "a-new", "a-old"],
                        "filingDate": ["2026-01-02", "2025-11-01", "2024-11-01"],
                    }
                }
            },
        )

    monkeypatch.setattr("dartlab.gather.edgar.bulkSubmissions.iterSubmissionsBulk", _fakeIter)
    monkeypatch.setattr("dartlab.gather.edgar.bulkSubmissions.downloadSubmissionsBulk", lambda: tmp_path / "z.zip")
    accs = mod.latestTenKAccessions(zipPath=tmp_path / "z.zip")
    assert accs["0000320193"] == ("a-new", "2025-11-01")  # 첫 10-K = 최신


def test_fetch_subsidiary_rows_parses_ex21(monkeypatch):
    """index.json 에서 EX-21 파일 찾고 파싱 행에 stockCode·연도 주입."""
    from dartlab.scan.builders.edgar.report.ex21Build import fetchSubsidiaryRows

    class _Resp:
        def __init__(self, payload=None, text=""):
            self._p = payload
            self.text = text

        def json(self):
            return self._p

    class _Client:
        def get(self, url, timeout=30):
            if url.endswith("index.json"):
                return _Resp(payload={"directory": {"item": [{"name": "a10-kexhibit211.htm"}, {"name": "r1.htm"}]}})
            return _Resp(text="<table><tr><td>Sub One LLC</td><td>Delaware</td></tr></table>")

    rows = fetchSubsidiaryRows("0000320193", "AAPL", "0000320193-25-000079", "2025-11-01", client=_Client())
    assert rows == [{"stockCode": "AAPL", "year": "2025", "name": "Sub One LLC", "jurisdiction": "Delaware"}]
