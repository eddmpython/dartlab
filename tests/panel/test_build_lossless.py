"""panel 빌드 태그 무손실/무중복 회귀 (G1·R4) — plan snazzy-wibbling-origami.

빌드 무손실의 정의(§10): 한 종목 zip 의 leaf element contentRaw 글자 합 ==
빌드된 artifact contentRaw 글자 합 **+ 태그 토큰(`<`) 수 일치**. horizontalize 가
element contentRaw 를 ``str.join("")`` 로 무손실 concat 하고 build 가 태그를 strip 하지
않으므로(R4), 전역 글자·태그 합이 정확히 보존된다. 합 동치 = 손실0 ∧ dup0 ∧ 태그무손실
동시 증명.

heavy + requires_data — 로컬 zip(``data/original/dart/docs/{code}``, local-only) + 빌드
artifact 둘 다 있어야 실행, 없으면 skip (CI 는 zip 미보유 → skip, collection green).
zip 전수 재파싱이라 무겁다 → test-lock.sh 단독 실행, fast/full preflight 제외.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

import dartlab.config as _cfg

pytestmark = [pytest.mark.requires_data, pytest.mark.heavy]

_BASE = "005930"
_PANEL_DIR = Path(_cfg.dataDir) / "dart" / "panel"
_ZIP_DIR = Path(_cfg.dataDir) / "original" / "dart" / "docs"
_REF_PATH = Path(_cfg.dataDir) / "dart" / "panelXbrlRef.parquet"


def _hasInputs(code: str) -> bool:
    art = _PANEL_DIR / f"{code}.parquet"
    zips = _ZIP_DIR / code
    return art.is_file() and zips.exists() and any(zips.glob("*.zip"))


requires_inputs = pytest.mark.skipif(not _hasInputs(_BASE), reason="panel artifact 없음 (005930)")


def _sourceTotals(code: str) -> tuple[int, int]:
    """zip → walker element rows 의 (contentRaw 글자 합, `<` 태그 합). build 와 동일 경로."""
    from lxml import etree

    from dartlab.providers.dart.panel.build.documentSource import _readZip
    from dartlab.providers.dart.panel.build.refScan import scanRefBaseline
    from dartlab.providers.dart.panel.build.refScan.refMatcher import (
        _REF_TOKENS,
        precomputeRefTokens,
        setGlobalRefTokens,
    )
    from dartlab.providers.dart.panel.build.walker import detectSchemaEra, walkSections

    ref = pl.read_parquet(str(_REF_PATH)) if _REF_PATH.exists() else scanRefBaseline(minCorpCount=1)
    if _REF_TOKENS is None:
        setGlobalRefTokens(precomputeRefTokens(ref))

    parser = etree.XMLParser(recover=True, huge_tree=True)
    chars = 0
    tags = 0
    for zp in sorted((_ZIP_DIR / code).glob("*.zip")):
        rcept, xmls = _readZip(zp)
        if not xmls or not rcept:
            continue
        for xml in xmls:
            try:
                root = etree.fromstring(xml.encode("utf-8"), parser)
            except (etree.XMLSyntaxError, ValueError):
                continue
            if root is None:
                continue
            era = detectSchemaEra(root)
            for row in walkSections(root, era, ref, matchThreshold=0.70):
                cr = row.get("contentRaw") or ""
                chars += len(cr)
                tags += cr.count("<")
    return chars, tags


def _artifactTotals(code: str) -> tuple[int, int]:
    """빌드 artifact 전 period 의 (contentRaw 글자 합, `<` 태그 합)."""
    art = pl.read_parquet(_PANEL_DIR / f"{code}.parquet")
    chars = art.select(pl.col("contentRaw").str.len_chars().sum()).item() or 0
    tags = art.select(pl.col("contentRaw").str.count_matches("<", literal=True).sum()).item() or 0
    return int(chars), int(tags)


@requires_inputs
def test_build_tag_lossless() -> None:
    """G1 — source element 글자·태그 합 == artifact contentRaw 글자·태그 합 (손실0·dup0·태그무손실)."""
    srcChars, srcTags = _sourceTotals(_BASE)
    assert srcChars > 0, "source 글자 0 — zip 파싱 실패 (테스트 환경 문제)"

    artChars, artTags = _artifactTotals(_BASE)

    assert artChars == srcChars, (
        f"contentRaw 글자 합 불일치 — source {srcChars:,} vs artifact {artChars:,} "
        f"(차 {artChars - srcChars:,}) — 손실 또는 중복 발생"
    )
    assert artTags == srcTags, (
        f"태그(`<`) 토큰 수 불일치 — source {srcTags:,} vs artifact {artTags:,} "
        f"(차 {artTags - srcTags:,}) — build 에서 태그 strip/가공 발생 (R4 위반)"
    )


def _latestAnnualZip(code: str) -> Path | None:
    """가장 최신 사업보고서(dFY·IS_C2 보유) zip — Revenue 직접 파싱용."""
    from dartlab.providers.dart.panel.build.documentSource import _readZip

    for zp in sorted((_ZIP_DIR / code).glob("*.zip"), reverse=True):
        _rcept, xmls = _readZip(zp)
        if any("dFY" in xml and "IS_C2" in xml for xml in xmls):
            return zp
    return None


_hasCellInputs = _hasInputs(_BASE) and any((_ZIP_DIR / _BASE).glob("*.zip"))
requires_cell_inputs = pytest.mark.skipif(not _hasCellInputs, reason="005930 panel.parquet/zip 없음")


@requires_cell_inputs
def test_cell_roundtrip_revenue() -> None:
    """셀 무손실 — zip 의 IS_C2 Revenue dFY 값 == readCellWide('IS2', year) 복원값.

    독립 직접 파싱(lxml) vs panel.parquet→build→read 파이프라인 동치 = 셀 손실0·무가공 증명.
    """
    import re

    from lxml import etree

    from dartlab.providers.dart.panel.build.documentSource import _readZip
    from dartlab.providers.dart.panel.cell import readCellWide

    # 1) read — readCellWide 가 panel.parquet 5표 contentRaw 를 read-time 분해 (별 panelCell 0)
    wide = readCellWide(_BASE, statement="IS2", freq="year")
    assert wide is not None and wide.height > 0

    # 2) 독립 직접 파싱 — 최신 사업보고서 IS_C2 Revenue dFY (단일축)
    zp = _latestAnnualZip(_BASE)
    assert zp is not None
    _rcept, xmls = _readZip(zp)
    parser = etree.XMLParser(recover=True, huge_tree=True)
    direct: dict[int, str] = {}
    for xml in xmls:
        root = etree.fromstring(xml.encode("utf-8"), parser)
        for tg in root.iter("TABLE-GROUP"):
            if (tg.get("ACLASS", "") or "").replace("{XBRL}", "") != "IS_C2":
                continue
            for te in tg.iter("TE"):
                ctx = te.get("ACONTEXT") or ""
                if (te.get("ACODE") or "").endswith("_Revenue") and "dFY" in ctx and ctx.count("Member") == 1:
                    direct[int(re.search(r"FY(\d{4})", ctx).group(1))] = "".join(te.itertext()).strip()
    assert direct, "직접 파싱 Revenue dFY 0"

    # 3) 동치 — 직접 파싱 값이 셀 격자에 그대로 (손실·가공 0)
    rev = wide.filter((pl.col("acode") == "ifrs-full_Revenue") & (pl.col("axisPath") == "ConsolidatedMember"))
    assert rev.height == 1, "Revenue 단일축 행 1개 (평탄화 충돌 0)"
    for yr, val in direct.items():
        if str(yr) in rev.columns:
            assert rev[str(yr)][0] == val, f"{yr} Revenue 불일치: 직접 {val} vs 셀 {rev[str(yr)][0]}"


@requires_cell_inputs
def test_native_statement_extends_past_xbrl() -> None:
    """native 재무제표(is)가 XBRL 경계(2022) 너머 옛 표 파싱으로 과거 연장."""
    from dartlab.providers.dart.panel.cell import readStatement

    w = readStatement(_BASE, statement="is", freq="year")
    assert w is not None
    years = sorted(int(c) for c in w.columns if c.isdigit())
    assert years[0] <= 2016, f"native 과거 연장 실패 — 최소연도 {years[0]} (옛 표 파싱 안 됨)"
    assert max(years) >= 2024, "최근 XBRL 연도 누락"


@requires_cell_inputs
def test_native_ratios_005930() -> None:
    """native 재무비율(소문자 ratios)이 BS/IS/CF native 항목으로 계산 — finance 보다 깊은 history."""
    from dartlab.providers.dart.panel.cell import readRatios

    w = readRatios(_BASE, freq="year")
    assert w is not None
    assert w.columns[:2] == ["ratio", "label"]
    ratios = w["ratio"].to_list()
    assert "roe" in ratios and "debtRatio" in ratios, "핵심 비율 누락"
    years = sorted(int(c) for c in w.columns if c.isdigit())
    assert years[0] <= 2016, f"native 비율 과거연장 실패 — 최소연도 {years[0]}"
    # ROE 행에 유효 값(native 5표 항목 산출 성공)
    roe = w.filter(pl.col("ratio") == "roe").row(0, named=True)
    assert any(roe[str(y)] is not None for y in years), "ROE 전 기간 None (재료 매핑 실패)"
