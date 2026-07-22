"""Data Workbench 팩터 커널의 반사, 이질 접기, gap 방출 검증.

엔진 데이터 0인 순수 투영 검증이다. 합성 fixture는 실제 반환 형태만 재현한다.

Covers:
- reflectAxes: loadCapabilities 소비로 축 + declared 획득 (raw 레지스트리 재반사 없음), 척추 3축이
  declared.listFn 을 갖는다.
- foldToCanonical: KR wide·US wide·envDict·scoreDict·entityMetric·스칼라 6형태 -> 단일 정규 롱.
- 갭 방출: 중첩 dict -> nonTabular 격리(환경 레인 유출 0), 역할불명 컬럼 -> unknownColumnRole.
- laneOf: declared(listFn) 우선으로 척추 확정, declared 없으면 AMBIGUOUS 표면화.
- universeScopeOf: stockRequired 선언으로 per-company 판정 (universeScope 발명 불요).
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.data.factorKernel import (
    CANON,
    foldToCanonical,
    laneOf,
    reflectAxes,
    universeScopeOf,
)

pytestmark = pytest.mark.unit

SPINE_ATOMS = ("scan.account", "scan.ratio", "scan.note")


def testReflectAxesFromCapabilities():
    """축 카탈로그가 loadCapabilities 소비로 반사되고 척추 원자가 listFn 을 선언한다."""
    from dartlab.reference.capability.dataProducts import axisRegistryTargets

    cat = reflectAxes()
    assert cat.height >= 100
    expectedOwners = {owner for owner, _module, _attribute in axisRegistryTargets()}
    assert set(cat["engine"].to_list()) == expectedOwners
    for atom in SPINE_ATOMS:
        eng, ax = atom.split(".")
        row = cat.filter((pl.col("engine") == eng) & (pl.col("axis") == ax))
        assert row.height == 1, f"{atom} 미반사"
        assert row["declared"][0].get("listFn"), f"{atom} listFn 미선언"


def testFoldHeterogeneousToOneLong():
    """6 이질 형태가 하나의 정규 롱으로 접히고 레인이 순수함수로 떨어진다."""
    fixtures = [
        (
            "scan",
            "account",
            pl.DataFrame({"종목코드": ["005930"], "종목명": ["삼성"], "2025": [300.0]}),
            {"returnType": "DataFrame", "listFn": "scanAccountList"},
        ),
        (
            "scan",
            "accountUs",
            pl.DataFrame({"stockCode": ["AAPL"], "corpName": ["Apple"], "2025": [390.0]}),
            {"returnType": "DataFrame", "listFn": "scanAccountList"},
        ),
        ("macro", "cycle", {"phase": "expansion", "fci": 0.31}, {"act": 1}),
        ("quant", "altman", {"scores": {"005930": 7.4}}, {"stockRequired": False}),
        ("scan", "governance", pl.DataFrame({"종목코드": ["005930"], "grade": ["A"]}), {"returnType": "DataFrame"}),
        ("scan", "peakCap", 42.0, {}),
    ]
    frames, gaps = [], []
    for engine, axis, raw, declared in fixtures:
        df, g = foldToCanonical(raw, engine=engine, axis=axis, declared=declared)
        frames.append(df)
        gaps.extend(g)
    canonical = pl.concat(frames)
    assert list(canonical.columns) == list(CANON)
    assert canonical.height >= 6
    # 척추 2축(KR/US wide)이 spine 으로, scoreDict 가 crossSection 으로
    assert set(canonical.filter(pl.col("axis") == "account")["lane"].unique()) == {"spine"}
    assert set(canonical.filter(pl.col("axis") == "altman")["lane"].unique()) == {"crossSection"}
    # 등급(grade)은 valueText 로 (0 대체 금지)
    gov = canonical.filter(pl.col("axis") == "governance")
    assert gov["valueText"][0] == "A" and gov["value"][0] is None


def testNestedDictQuarantinedNotLeaked():
    """중첩 dict(graph)는 환경 레인으로 새지 않고 nonTabular 로 격리된다."""
    df, gaps = foldToCanonical({"nodes": [{"id": "a"}], "edges": []}, engine="industry", axis="edges")
    assert df.height == 0
    assert len(gaps) == 1 and gaps[0]["gapReason"] == "nonTabular"


def testUnknownColumnSurfaced():
    """yearWide 에 역할 불명 컬럼이 섞이면 조용히 melt 하지 않고 unknownColumnRole 로 방출한다."""
    dirty = pl.DataFrame({"종목코드": ["005930"], "종목명": ["삼성"], "시장구분": ["KOSPI"], "2025": [10.0]})
    df, gaps = foldToCanonical(
        dirty, engine="scan", axis="ratioDirty", declared={"returnType": "DataFrame"}, item="roe"
    )
    reasons = {g["gapReason"] for g in gaps}
    assert "unknownColumnRole" in reasons
    assert "시장구분" in [g["valueText"] for g in gaps if g["gapReason"] == "unknownColumnRole"][0]


def testItemLabelDistinguishesRatios():
    """wide 반환은 항목이 열에 없으므로 item 인자로 roe/debtRatio 를 구분해야 한다 (실측 결함 가드)."""
    roe = pl.DataFrame({"종목코드": ["005930"], "종목명": ["삼성"], "2025": [10.36]})
    df, _ = foldToCanonical(
        roe, engine="scan", axis="ratio", item="roe", declared={"returnType": "DataFrame", "listFn": "scanRatioList"}
    )
    assert df["item"][0] == "roe"


def testUniverseScopeFromDeclaration():
    """per-company 는 stockRequired 선언으로 안다 (universeScope 발명 불필요)."""
    assert universeScopeOf({"stockRequired": True, "multiStock": False}) == "perCompany"
    assert universeScopeOf({"stockRequired": False}) == "bulk"
    assert universeScopeOf({"returnType": "DataFrame"}) == "bulk"


def testLaneAmbiguousWhenUndeclared():
    """declared 없는 entityMetric 은 조용히 확정하지 않고 ambiguous 로 표면화한다."""
    frame = pl.DataFrame({"종목코드": ["005930"], "per": [12.4], "pbr": [1.1]})
    lane, status = laneOf("entityMetric", frame, declared={})
    assert status == "ambiguous"


def testScoreDictNonNumericIsGapNotCrash():
    """점수가 None·비수치면 float 크래시 대신 valueText 로 접힌다 (배치 중단 방지)."""
    df, gaps = foldToCanonical(
        {"scores": {"005930": None, "000660": "N/A", "005380": 7.4}}, engine="quant", axis="altman"
    )
    assert df.height == 3  # 크래시 없음
    none_row = df.filter(pl.col("entity") == "005930")
    assert none_row["value"][0] is None and none_row["valueText"][0] is None
    na_row = df.filter(pl.col("entity") == "000660")
    assert na_row["value"][0] is None and na_row["valueText"][0] == "N/A"
    assert df.filter(pl.col("entity") == "005380")["value"][0] == 7.4


def testEnvFramePreservesPeriod():
    """entity 없는 period-wide(envFrame)는 기간을 period 로 보존한다 (item 유출·latest 소실 금지)."""
    macro = pl.DataFrame({"지표": ["GDP", "CPI"], "2023": [100.0, 2.1], "2024": [105.0, 3.5]})
    df, gaps = foldToCanonical(macro, engine="macro", axis="series")
    assert set(df["period"].unique()) == {"2023", "2024"}  # 기간이 latest 로 소실 안 됨
    assert set(df["item"].unique()) == {"GDP", "CPI"}  # 라벨이 item 으로 보존
    gdp24 = df.filter((pl.col("item") == "GDP") & (pl.col("period") == "2024"))
    assert gdp24["value"][0] == 105.0


def testEmptyReturnEmitsGap():
    """빈 반환(빈 dict/scores)도 gap 원장에 남는다 (canonical·coverage·gap 셋에서 사라지는 사각 방지)."""
    df, gaps = foldToCanonical({}, engine="macro", axis="empty")
    assert df.height == 0
    assert len(gaps) == 1 and gaps[0]["gapReason"] == "emptyReturn"
    df2, gaps2 = foldToCanonical({"scores": {}}, engine="quant", axis="emptyScores")
    assert len(gaps2) == 1 and gaps2[0]["gapReason"] == "emptyReturn"


def testMixedDtypeFramePreservesNumerics():
    """숫자+문자 혼합 프레임(등급+ROE)에서 숫자값이 String 승격으로 죽지 않는다 (272K 소실 회귀)."""
    mixed = pl.DataFrame(
        {"종목코드": ["005930"], "종목명": ["삼성"], "영업이익률": [21.1], "ROE": [10.4], "등급": ["A"]}
    )
    df, _ = foldToCanonical(mixed, engine="scan", axis="profitability", declared={"returnType": "DataFrame"})
    roe = df.filter(pl.col("item") == "ROE")
    assert roe["value"][0] == 10.4 and roe["valueText"][0] is None  # 숫자 보존
    grade = df.filter(pl.col("item") == "등급")
    assert grade["valueText"][0] == "A" and grade["value"][0] is None  # 문자는 valueText


def testPeriodRegexRejectsNonYears():
    """period 정규식이 종목코드·무효월·계정코드를 period 로 오탐하지 않는다."""
    from dartlab.data.factorKernel import _periodCols

    assert _periodCols(["005930", "202599", "1000", "2400"]) == []  # 비-period
    assert _periodCols(["2025", "2025Q3", "202503"]) == ["2025", "2025Q3", "202503"]  # 진짜 period


def testNestedMixedKeysNoCrash():
    """중첩 dict 의 키 타입이 섞여도 지문 생성이 크래시하지 않고 gap 을 낸다."""
    df, gaps = foldToCanonical({1: {"x": 1}, "a": {"y": 2}}, engine="x", axis="y")
    assert df.height == 0 and gaps[0]["gapReason"] == "nonTabular"
