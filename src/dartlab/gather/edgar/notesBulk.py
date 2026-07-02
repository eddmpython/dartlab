"""SEC DERA Financial Statement and Notes 데이터셋 수집. 부문(차원) 포함 전체 XBRL 사실의 SSOT.

companyfacts 집계 API 는 차원(dimension) 사실을 주지 않아 부문별 매출(segment revenue)을 못 준다.
DERA notes 데이터셋(월별/분기별 zip: sub·num·dim·tag tsv)은 제출된 XBRL 인라인 사실 전체를 차원까지
담는다(실측: AAPL FY2025 BusinessSegments=Americas 178.4B 등 부문·제품 축 전부). 본 모듈은 zip 수집과
tsv 스트리밍만 담당하고, 어떤 tag·축을 쓸지는 scan 빌더(가공)가 정한다.

배포 주기: 2009q1~2022q4 분기(`{yyyy}q{n}_notes.zip`), 2023_01~ 월별(`{yyyy}_{mm}_notes.zip`).
과거분은 불변이라 존재하면 재다운로드하지 않는다(당월분만 갱신 대상).
"""

from __future__ import annotations

import csv
import io
import zipfile
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import httpx

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

_BASE_URL = "https://www.sec.gov/files/dera/data/financial-statement-notes-data-sets"
_UA = "dartlab eddmpython@gmail.com"
_TIMEOUT = httpx.Timeout(120.0, read=None, write=60.0, connect=30.0)


def _notesDir() -> Path:
    """`data/edgar/_bulk/notes/` 저장 폴더(없으면 생성)."""
    from dartlab.core.dataLoader import _getDataRoot

    d = _getDataRoot() / "edgar" / "_bulk" / "notes"
    d.mkdir(parents=True, exist_ok=True)
    return d


def notesStems(*, sinceYear: int = 2015, today: date | None = None) -> list[str]:
    """가용 notes zip stem 목록(과거→현재). 분기(~2022q4) + 월별(2023_01~) 배포 주기 반영.

    Args:
        sinceYear: 시작 연도(기본 2015, allFilings 메타 깊이와 대칭).
        today: 기준일(테스트 주입용). None 이면 오늘.

    Returns:
        list[str]. ``2015q1`` ... ``2022q4``, ``2023_01`` ... 직전월 순서.

    Raises:
        없음.

    Example:
        >>> notesStems(sinceYear=2022, today=date(2023, 3, 15))
        ['2022q1', '2022q2', '2022q3', '2022q4', '2023_01', '2023_02']

    SeeAlso:
        - ``downloadNotesBulk`` (stem 단위 다운로드)

    Requires:
        - 표준 라이브러리만.

    Capabilities:
        - DERA 배포 주기(분기→월 전환)를 한 곳에서 캡슐화. 백필 runner 의 순회 SSOT.

    Guide:
        - 백필은 최신부터 역순(reversed)으로 돌리면 터미널이 먼저 점등된다.

    When:
        - 백필 runner·CI 스텝이 처리 대상 stem 을 열거할 때.

    How:
        - 2022 까지 분기 stem, 2023 부터 기준일 직전월까지 월 stem 생성.

    AIContext:
        internal 수집 헬퍼. AI 직접 호출 X.
    """
    t = today or date.today()
    stems = [f"{y}q{q}" for y in range(sinceYear, 2023) for q in range(1, 5) if y >= sinceYear]
    y, m = 2023, 1
    while (y, m) < (t.year, t.month):
        stems.append(f"{y}_{m:02d}")
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return stems


def downloadNotesBulk(stem: str, *, force: bool = False) -> Path:
    """단일 notes zip(`{stem}_notes.zip`)을 `_bulk/notes/` 로 다운로드. 과거분은 존재 시 스킵.

    Args:
        stem: ``2025_10`` (월별) 또는 ``2022q4`` (분기별).
        force: True 면 존재해도 재다운로드(당월 zip 갱신용).

    Returns:
        Path. 로컬 zip 경로.

    Raises:
        httpx.HTTPStatusError: 4xx/5xx (미배포 stem 포함).
        OSError: 파일 쓰기 실패.

    Example:
        >>> downloadNotesBulk("2025_10")  # doctest: +SKIP

    SeeAlso:
        - ``iterNotesTsv`` (다운로드본 스트리밍)
        - ``dartlab.gather.edgar.bulk.downloadCompanyfactsBulk`` (동형 bulk 수집)

    Requires:
        - httpx (SEC fair-access User-Agent)

    Capabilities:
        - 부문·제품 축 포함 전체 XBRL 사실 원천 확보(월 ~300MB).

    Guide:
        - 과거 stem 은 불변이라 존재 체크만으로 스킵. 당월분만 ``force=True`` 로 갱신.

    When:
        - segments 백필 runner·edgarSync 월별 갱신 스텝.

    How:
        - GET streaming 으로 tmp 에 받고 rename(부분 다운로드 방어).

    AIContext:
        internal 수집기. AI 직접 호출 X.
    """
    out = _notesDir() / f"{stem}_notes.zip"
    if out.exists() and not force:
        return out
    url = f"{_BASE_URL}/{stem}_notes.zip"
    tmp = out.with_suffix(".zip.tmp")
    with httpx.Client(headers={"User-Agent": _UA}, timeout=_TIMEOUT, follow_redirects=True) as client:
        with client.stream("GET", url) as r:
            r.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in r.iter_bytes(chunk_size=1 << 20):
                    f.write(chunk)
    tmp.replace(out)
    _log.info(f"[notesBulk] {stem}: {out.stat().st_size / 1e6:.0f}MB 다운로드")
    return out


def iterNotesTsv(zipPath: Path, member: str) -> Iterator[dict[str, str]]:
    """notes zip 안 tsv(member)를 행 dict 로 스트리밍(메모리 상수).

    Args:
        zipPath: notes zip 경로.
        member: ``sub.tsv`` · ``num.tsv`` · ``dim.tsv`` 등.

    Returns:
        Iterator[dict[str, str]]. tsv 헤더 키 행.

    Raises:
        KeyError: member 부재.
        zipfile.BadZipFile: 손상 zip.

    Example:
        >>> next(iterNotesTsv(Path("2025_10_notes.zip"), "sub.tsv"))  # doctest: +SKIP

    SeeAlso:
        - ``downloadNotesBulk``

    Requires:
        - 표준 라이브러리만 (zipfile·csv).

    Capabilities:
        - num.tsv(월 ~800MB)도 상수 메모리로 순회.

    Guide:
        - 도메인 필터(tag·축 선별)는 호출측(scan 빌더) 책임.

    When:
        - scan 빌더가 부문 매출 등 차원 사실을 추출할 때.

    How:
        - zipfile 스트림 + csv.DictReader (uncompress 전개 없음).

    AIContext:
        internal 스트리밍 헬퍼. AI 직접 호출 X.
    """
    # txt/footnote 류 초대형 필드가 기본 한도(128KB)를 넘는 zip 실존(2017q4 크래시 실측) → 상향.
    csv.field_size_limit(1 << 27)
    with zipfile.ZipFile(zipPath) as z, z.open(member) as f:
        reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t")
        yield from reader


__all__ = ["downloadNotesBulk", "iterNotesTsv", "notesStems"]
