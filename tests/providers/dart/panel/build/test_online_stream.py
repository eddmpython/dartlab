"""panel online 1패스 동등성 (P6 design-in) — plan snazzy-wibbling-origami.

build core 입력원-중립 리팩터(P2) 검증: 같은 zip 입력을 (A) 디스크 경로 ``buildPanel`` 과
(B) 메모리 bytes 스트림 ``buildPanelFromStream`` 으로 빌드하면 **회사당 flat 16-col parquet 가
row 동형**이어야 한다. 둘 다 동일 코어(``_xmlsToPeriodRows`` → 격리 공시 process)를 거치고
입력원만 zip(Path) vs zip(bytes) 로 다르다 — 동등성이 곧 online 트랙의 무손실 보장. (빈 tmp dir 라
disk=merge False·stream=merge True 모두 clean write → 동등.)

heavy + requires_data — 로컬 zip(``data/original/dart/docs/{code}``, local-only) 있어야 실행,
없으면 skip (CI 는 zip 미보유 → skip). 한 종목 2회 빌드라 무겁다 → test-lock.sh 단독, preflight 제외.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

import dartlab.config as _cfg
from dartlab.providers.dart.panel.build.builder import panelXbrlRefPath

pytestmark = [pytest.mark.requires_data, pytest.mark.heavy]

_BASE = "005930"
_ZIP_DIR = Path(_cfg.dataDir) / "original" / "dart" / "docs"
_REF_PATH = panelXbrlRefPath()  # 패키지 동봉 (data/dart/panelXbrlRef.parquet 은 폐기)


def _hasZips(code: str) -> bool:
    zips = _ZIP_DIR / code
    return zips.exists() and any(zips.glob("*.zip"))


requires_zips = pytest.mark.skipif(not _hasZips(_BASE), reason="로컬 zip 없음 (005930)")


def _loadRef() -> pl.DataFrame:
    from dartlab.providers.dart.panel.build.refScan import scanRefBaseline

    if _REF_PATH.exists():
        return pl.read_parquet(str(_REF_PATH))
    return scanRefBaseline(minCorpCount=1)


@requires_zips
def test_disk_and_stream_builds_are_identical(tmp_path: Path) -> None:
    """buildPanel(zip 디스크) ≡ buildPanelFromStream(zip bytes) — 회사당 flat parquet row 동형."""
    from dartlab.providers.dart.panel.build import buildPanel, buildPanelFromStream

    ref = _loadRef()
    zps = sorted((_ZIP_DIR / _BASE).glob("*.zip"))
    assert zps, "zip 0 — 테스트 환경 문제"

    diskBase = tmp_path / "disk"
    streamBase = tmp_path / "stream"

    diskRes = buildPanel(_BASE, refDf=ref, outBaseDir=diskBase, overwrite=True)
    # 디스크와 동일 zip 순서(sorted glob) 로 bytes 스트림 구성 — rcept = 파일 stem(14자리).
    stream = ((zp.stem, zp.read_bytes()) for zp in zps)
    streamRes = buildPanelFromStream(_BASE, stream, refDf=ref, outBaseDir=streamBase, overwrite=True)

    assert diskRes == streamRes, f"period→rowCount 불일치: disk {diskRes} vs stream {streamRes}"

    # flat: 회사당 단일 {code}.parquet (per-period 폴더 아님). 정렬 후 row 동형 비교.
    pA = diskBase / f"{_BASE}.parquet"
    pB = streamBase / f"{_BASE}.parquet"
    assert pA.exists(), "disk 빌드 산출 0"
    assert pB.exists(), "stream 빌드 산출 0"
    sortKeys = ["period", "rceptNo", "blockOrder", "leafType", "contentRaw"]
    dfA = pl.read_parquet(pA).sort(sortKeys)
    dfB = pl.read_parquet(pB).sort(sortKeys)
    assert dfA.equals(dfB), f"{_BASE}.parquet contentRaw/16-col 불일치 — 입력원별 산출 drift"


@requires_zips
def test_read_zip_bytes_matches_disk() -> None:
    """_readZipBytes(bytes) ≡ _readZip(Path) — 동일 zip 의 decoded XML 동일."""
    from dartlab.providers.dart.panel.build.documentSource import _readZip, _readZipBytes

    zp = sorted((_ZIP_DIR / _BASE).glob("*.zip"))[0]
    rceptDisk, xmlsDisk = _readZip(zp)
    rceptBytes, xmlsBytes = _readZipBytes(zp.read_bytes(), rceptDisk or zp.stem)
    assert rceptBytes == (rceptDisk or zp.stem)
    assert xmlsDisk == xmlsBytes, "디스크/bytes decoded XML 불일치"
