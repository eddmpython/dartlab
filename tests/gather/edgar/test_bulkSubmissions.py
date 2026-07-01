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
    """recentOnly=False 면 과거 페이지도 포함하고, 과거 페이지 cik 이 메인과 동일해야 한다.

    옛 버그: 과거 페이지 stem(CIK0000320193-submissions-001)에서 cik 을 '320193-submissions-001' 로
    깨뜨려 cik→ticker 매핑 실패 = 과거 페이지 전량 누락(심화 백필이 얕게 나오던 근본 원인).
    """
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
    assert [cik for cik, _ in rows] == ["0000320193", "0000320193"]  # 과거 페이지도 같은 cik(매핑 성공)


def test_cik_from_stem():
    """메인·과거 페이지 stem 양쪽에서 CIK(0-padded 10)만 정확히 추출."""
    from dartlab.gather.edgar.bulkSubmissions import cikFromStem

    assert cikFromStem("CIK0000320193") == "0000320193"
    assert cikFromStem("CIK0000320193-submissions-001") == "0000320193"  # 과거 페이지도 동일 cik
    assert cikFromStem("CIK0000104169-submissions-012") == "0000104169"
