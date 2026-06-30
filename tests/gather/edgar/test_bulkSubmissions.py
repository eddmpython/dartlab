"""bulkSubmissions — submissions.zip 순회(recentOnly 가 과거 페이지 제외) 단위. 네트워크/OOM 무관."""

from __future__ import annotations

import json
import zipfile

import pytest

pytestmark = pytest.mark.unit


def _makeZip(path, entries: dict[str, dict]) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        for name, payload in entries.items():
            zf.writestr(name, json.dumps(payload))


def test_iter_recent_only_skips_older_pages(tmp_path):
    """recentOnly=True 면 메인 CIK{10}.json 만 yield, 과거 페이지(-submissions-NNN)는 제외."""
    from dartlab.gather.edgar.bulkSubmissions import iterSubmissionsBulk

    zp = tmp_path / "submissions.zip"
    _makeZip(
        zp,
        {
            "CIK0000320193.json": {"cik": "320193", "name": "Apple Inc."},
            "CIK0000320193-submissions-001.json": {"cik": "320193", "older": True},
            "CIK0000789019.json": {"cik": "789019", "name": "Microsoft"},
            "README.txt": {},  # 비-json 무시
        },
    )
    got = dict(iterSubmissionsBulk(zp, recentOnly=True))
    assert set(got) == {"0000320193", "0000789019"}  # 메인 2개만, 과거 페이지 제외
    assert got["0000320193"]["name"] == "Apple Inc."


def test_iter_all_includes_older(tmp_path):
    """recentOnly=False 면 과거 페이지도 포함."""
    from dartlab.gather.edgar.bulkSubmissions import iterSubmissionsBulk

    zp = tmp_path / "submissions.zip"
    _makeZip(
        zp,
        {
            "CIK0000320193.json": {"cik": "320193"},
            "CIK0000320193-submissions-001.json": {"cik": "320193", "older": True},
        },
    )
    rows = list(iterSubmissionsBulk(zp, recentOnly=False))
    assert len(rows) == 2  # 메인 + 과거 페이지
