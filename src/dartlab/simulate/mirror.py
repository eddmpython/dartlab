"""거울 작업대 물질화 드라이버 : 순수 커널을 공개계약 엔진 호출로 구동한다 (L2.5 simulate).

Capabilities:
    - bulkSelects: reflectAxes + declared(universeScope=bulk) 로 물질화할 (engine, axis, item) 작업
      목록을 자동 구성한다. 카탈로그 원자(account/ratio)는 무target 공개 호출로 항목을 전개한다
      (손 선별 0, 도태는 사후 coverage). per-company(stockRequired) 축은 벌크에서 배제.
    - materialize: 공개계약 dartlab.{engine}("{axis}", item) 1회 호출 -> 순수 커널 foldToCanonical
      -> 정규 롱. 실패는 값 조작 없이 gap 행.
    - runWorkbench: 작업 목록 전수 물질화 -> 단일 정규 롱 + coverage 성적표 + gap 원장.

AIContext:
    개념 #1 데이터 작업대의 값 물질화 층. 순수 계산은 L1.5 reference.capability.mirror 가, 엔진 실호출은
    여기가 담당한다. 호출은 공개계약 3형태(가이드/무target 목록/물질화)만 탄다. parquet 직독·내부 리더
    (table.py 등)·Company 루프는 이 모듈에 등장하지 않는다 (tests/audit/workbenchPurity 강제).

Guide:
    runWorkbench(bulkSelects()) 로 전 벌크 축을 물질화하거나, materialize(engine, axis, item=...) 로
    단일 슬라이스만 지연 물질화한다. 860 전수 같은 비싼 배치는 명시 호출에서만 돈다 (사전빌드 0).

When:
    여러 엔진 축을 하나의 (entity, period, item, value) 격자로 실제 값까지 세울 때.

Requires:
    dartlab 루트 facade (공개 verb). reference.capability.mirror (순수 커널). polars.

How:
    reflectAxes -> declared 로 벌크 축 선별 -> 카탈로그 무target 전개 -> 축별 엔진 호출 -> foldToCanonical
    -> concat. coverage = (engine, axis) 별 종목/행/status 집계 = "도태는 측정" 원장.

Raises:
    없음. 축별 호출 실패는 격리되어 gap 행이 되고 나머지 축 물질화는 계속된다.

SeeAlso:
    - reference.capability.mirror (순수 커널: reflectAxes·foldToCanonical·laneOf)
    - mainPlan/scenario-simulator/18-workbench-mirror-design.md (설계 PR4)

Layer: L2.5 simulate. dartlab 루트 facade + L1.5 커널 배선 (다중 L2 결합 합법).
"""

from __future__ import annotations

import time
from typing import Any

import polars as pl

from dartlab.reference.capability.mirror import foldToCanonical, reflectAxes, universeScopeOf


def _call(engine: str, axis: str, item: str | None, **callKw) -> Any:
    """공개계약 dartlab.{engine}("{axis}"[, item]) 호출. 내부 리더·parquet 경로를 타지 않는다."""
    import dartlab

    verb = getattr(dartlab, engine, None)
    if verb is None:
        raise ValueError(f"엔진 verb 없음: {engine}")
    return verb(axis, item, **callKw) if item else verb(axis, **callKw)


def catalogItems(engine: str, axis: str) -> list[str]:
    """카탈로그 축의 항목을 무target 공개 호출로 전개 → [name...]. 손 선별 0.

    Args:
        engine: 엔진 이름. axis: 카탈로그 원자 축 (declared.listFn 보유, 예 scan.account).

    Returns:
        항목 name 리스트. 무target 호출이 (name, ...) 카탈로그 DataFrame 을 주면 그 name 열. 아니면 빈 [].

    Example:
        >>> "sales" in catalogItems("scan", "account")
        True

    Raises:
        없음. 호출 실패·비카탈로그 반환은 빈 리스트 (상위가 축 자체를 단일 물질화로 처리).
    """
    try:
        raw = _call(engine, axis, None)
    except Exception:
        return []
    if isinstance(raw, pl.DataFrame) and "name" in raw.columns:
        return raw["name"].to_list()
    return []


def bulkSelects(*, expandCatalog: bool = True) -> list[tuple[str, str, str | None]]:
    """물질화할 (engine, axis, item) 작업 목록 자동 구성. declared 로 벌크만, 카탈로그는 전개.

    Args:
        expandCatalog: True 면 카탈로그 원자(listFn 보유)를 항목 전수로 펼친다 (account 860 등).

    Returns:
        (engine, axis, item) 튜플 리스트. item 은 카탈로그 전개분만 채워지고 나머지는 None.
        per-company(stockRequired) 축은 제외 (벌크 작업대 대상 아님).

    Example:
        >>> sel = bulkSelects(expandCatalog=False)
        >>> ("scan", "ratio", None) in sel
        True

    Raises:
        없음.
    """
    selects: list[tuple[str, str, str | None]] = []
    for row in reflectAxes().iter_rows(named=True):
        declared = row["declared"] or {}
        if universeScopeOf(declared) == "perCompany":
            continue
        engine, axis = row["engine"], row["axis"]
        if expandCatalog and declared.get("listFn"):
            items = catalogItems(engine, axis)
            selects.extend((engine, axis, it) for it in items) if items else selects.append((engine, axis, None))
        else:
            selects.append((engine, axis, None))
    return selects


def materialize(engine: str, axis: str, *, item: str | None = None, **callKw) -> tuple[pl.DataFrame, list[dict]]:
    """공개계약 호출 1회 -> 순수 커널로 정규 롱. 실패는 값 조작 없이 gap 행.

    Args:
        engine: 엔진 이름. axis: 축 이름. item: 카탈로그 항목 (account/ratio 등). callKw: freq·market 등.

    Returns:
        (canonical long df, gap rows). 계약 위반·미지 형태는 df 없이 gap 만 (결손 0 대체 금지).

    Example:
        >>> df, gaps = materialize("scan", "ratio", item="roe", freq="Y")
        >>> df.height > 0
        True

    Raises:
        없음. 호출 예외는 gapReason=contractError 1행으로 격리된다.
    """
    from dartlab.reference.capability.mirror import emitGap

    declared = _declaredFor(engine, axis)
    try:
        raw = _call(engine, axis, item, **callKw)
    except Exception as e:
        return pl.DataFrame(), [emitGap(engine, axis, "contractError", f"{type(e).__name__}: {e}"[:70])]
    return foldToCanonical(raw, engine=engine, axis=axis, item=item, declared=declared)


def _declaredFor(engine: str, axis: str) -> dict:
    cat = reflectAxes().filter((pl.col("engine") == engine) & (pl.col("axis") == axis))
    return cat["declared"][0] if cat.height else {}


def runWorkbench(
    selects: list[tuple[str, str, str | None]], *, progress: bool = False, **callKw
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """작업 목록 전수 물질화 -> (정규 롱, coverage 성적표, gap 원장). 도태는 coverage 가 측정.

    Args:
        selects: (engine, axis, item) 목록 (bulkSelects 산출). progress: 진행 인쇄. callKw: freq 등.

    Returns:
        (canonical, coverage, gaps). canonical = 단일 정규 롱. coverage = (engine, axis) 별 종목/행.
        gaps = 실패/격리 원장.

    Example:
        >>> canon, cov, gaps = runWorkbench([("scan", "ratio", "roe")], freq="Y")
        >>> canon["item"][0]
        'roe'

    Raises:
        없음. 축별 실패는 격리되고 나머지는 계속된다.
    """
    frames, gaps = [], []
    t0 = time.perf_counter()
    for i, (engine, axis, item) in enumerate(selects):
        df, g = materialize(engine, axis, item=item, **callKw)
        if df.height:
            frames.append(df)
        gaps.extend(g)
        if progress and (i + 1) % 50 == 0:
            print(
                f"  {i + 1}/{len(selects)} ({time.perf_counter() - t0:.0f}s) rows={sum(f.height for f in frames):,}",
                flush=True,
            )
    canonical = pl.concat(frames) if frames else pl.DataFrame(schema={c: pl.Utf8 for c in ("engine", "axis", "item")})
    coverage = (
        canonical.group_by(["engine", "axis", "lane"]).agg(
            종목=pl.col("entity").n_unique(), 행=pl.len(), status=pl.col("status").first()
        )
        if canonical.height
        else pl.DataFrame()
    )
    gapDf = pl.DataFrame(gaps) if gaps else pl.DataFrame()
    return canonical, coverage.sort("행", descending=True) if coverage.height else coverage, gapDf
