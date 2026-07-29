"""panel cell read mirror — freq 토큰 선택 + acode×period pivot (합성 parquet, 데이터 0).

``cell.py`` 의 ``readCellWide``/``_freqMask``/``_periodLabelExpr``/``cellStatements``. 합성 셀
parquet 을 tmp dataDir 에 써서 freq 분기·평탄화·dedup 을 검증 (lxml/network 0, R2).
"""

from __future__ import annotations

import ast
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit

from dartlab.providers.dart.panel.cellSchema import CELL_SCHEMA


def _cellRows() -> list[dict]:
    """합성 셀 행 — IS2 Revenue(연간/분기단독/누적) + EF 같은 acode 2축(충돌)."""
    rows = []
    # IS2 Revenue 연간 (FY annual report, 2025Q4 filing): CFY 2025, PFY 2024
    for year, mode, q, flow, scope2, val in [
        (2025, "Y", 4, "d", "ConsolidatedMember", "100"),
        (2024, "Y", 4, "d", "ConsolidatedMember", "90"),
    ]:
        rows.append(_row("2025Q4", "IS2", "ifrs-full_Revenue", "매출액", year, flow, q, mode, scope2, val))
    # IS2 Revenue 분기 (2025Q3 filing): 단독 Q3 + 누적 9M
    rows.append(_row("2025Q3", "IS2", "ifrs-full_Revenue", "매출액", 2025, "d", 3, "Q", "ConsolidatedMember", "30"))
    rows.append(_row("2025Q3", "IS2", "ifrs-full_Revenue", "매출액", 2025, "d", 3, "A", "ConsolidatedMember", "75"))
    # EF 같은 acode 2 축 (평탄화 충돌 회피)
    rows.append(_row("2025Q4", "EF", "ifrs-full_Equity", "자본", 2025, "e", 4, "Y", "RetainedEarningsMember", "7"))
    rows.append(_row("2025Q4", "EF", "ifrs-full_Equity", "자본", 2025, "e", 4, "Y", "IssuedCapitalMember", "1"))
    return rows


def _row(fp, stmt, acode, label, year, flow, q, mode, member, val):
    return {
        "corp": "TEST01",
        "rceptNo": "2026" + fp[-2:] + "00000000",
        "filingPeriod": fp,
        "statement": stmt,
        "scope": "consolidated",
        "acode": acode,
        "label": label,
        "ctxYear": year,
        "ctxFlow": flow,
        "ctxQuarter": q,
        "ctxMode": mode,
        "axisPath": member,
        "valueRaw": val,
        "cellOrder": 0,
    }


@pytest.fixture
def cellEnv() -> pl.DataFrame:
    """합성 셀 DataFrame — panelCell 파일 0, 순수 _cellWideFromCells 직접 검증."""
    return pl.DataFrame(_cellRows(), schema=CELL_SCHEMA)


def test_cell_statements() -> None:
    """셀 대상 = 재무 5표 (손익 IS1/IS2/IS3 — 단일/별도/포괄)."""
    from dartlab.providers.dart.panel.cell import cellStatements

    assert cellStatements() == frozenset({"BS", "IS1", "IS2", "IS3", "CF", "EF"})


def test_freq_year_selects_fy(cellEnv) -> None:
    """freq=year → ctxMode=Y (dFY) 만, 열=연도."""
    from dartlab.providers.dart.panel.cell import _cellWideFromCells

    w = _cellWideFromCells(cellEnv, statement="IS2", freq="year", scope="consolidated")
    assert w is not None
    periodCols = [c for c in w.columns if c.isdigit()]
    assert set(periodCols) == {"2025", "2024"}
    rev = w.filter(pl.col("acode") == "ifrs-full_Revenue")
    assert rev["2025"][0] == "100" and rev["2024"][0] == "90"


def test_freq_quarter_vs_ytd_token_split(cellEnv) -> None:
    """freq=quarter → 단독(Q)=30, ytd → 누적(A)=75 (같은 분기, 다른 토큰)."""
    from dartlab.providers.dart.panel.cell import _cellWideFromCells

    q = _cellWideFromCells(cellEnv, statement="IS2", freq="quarter", scope="consolidated")
    y = _cellWideFromCells(cellEnv, statement="IS2", freq="ytd", scope="consolidated")
    qv = q.filter(pl.col("acode") == "ifrs-full_Revenue")["2025Q3"][0]
    yv = y.filter(pl.col("acode") == "ifrs-full_Revenue")["2025Q3"][0]
    assert qv == "30"  # 단독
    assert yv == "75"  # 누적


def test_axispath_no_collision(cellEnv) -> None:
    """같은 acode 다른 axisPath → 별 행 (평탄화 충돌 0)."""
    from dartlab.providers.dart.panel.cell import _cellWideFromCells

    w = _cellWideFromCells(cellEnv, statement="EF", freq="year", scope="consolidated")
    eq = w.filter(pl.col("acode") == "ifrs-full_Equity")
    assert eq.height == 2  # RetainedEarnings + IssuedCapital
    assert set(eq["axisPath"].to_list()) == {"RetainedEarningsMember", "IssuedCapitalMember"}


def test_absent_artifact_returns_none(tmp_path, monkeypatch) -> None:
    """panel.parquet 없는 종목 → None (graceful, HF 미시도)."""
    import dartlab.config as cfg

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setenv("DARTLAB_NO_HF_DOWNLOAD", "1")
    from dartlab.providers.dart.panel.cell import readCellWide

    assert readCellWide("999999", statement="IS2", freq="year") is None


def test_invalid_statement_returns_none() -> None:
    """5표 외 statement → None."""
    from dartlab.providers.dart.panel.cell import readCellWide

    assert readCellWide("005930", statement="NT_D826380", freq="year") is None


def test_read_no_lxml_import() -> None:
    """cell read 표면은 lxml/zipfile import 0 (R2)."""
    src = Path("src/dartlab/providers/dart/panel/cell.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "lxml" not in imported and "zipfile" not in imported


# --- readStatement (native 재무제표 — XBRL+옛 항목명 통합) ---


def test_normalize_label() -> None:
    """(주N) strip + 공백 제거 → 매칭 키."""
    from dartlab.providers.dart.panel.cell import _normalizeLabel

    out = pl.select(_normalizeLabel(pl.lit("매출액 (주30)")).alias("x"))["x"][0]
    assert out == "매출액"
    out2 = pl.select(_normalizeLabel(pl.lit("수익(매출액)")).alias("x"))["x"][0]
    assert out2 == "수익(매출액)"  # 주N 아님 → 보존 (개명 항목 별 행)


def _statementRows() -> list[dict]:
    """IS2 top-level 매출 — XBRL(2025/2024) + 옛 통합(2020 매출액, 2015 수익(매출액))."""
    rows = [
        _row("2025Q4", "IS2", "ifrs-full_Revenue", "매출액 (주30)", 2025, "d", 4, "Y", "ConsolidatedMember", "300"),
        _row("2025Q4", "IS2", "ifrs-full_Revenue", "매출액 (주30)", 2024, "d", 4, "Y", "ConsolidatedMember", "290"),
    ]
    # 옛 셀 (acode=None): 같은 항목명(주석번호만 다름) → 통합 / 개명 → 별 행
    rows.append(_oldRow("2020Q4", "매출액 (주28)", 2020, "200"))
    rows.append(_oldRow("2015Q4", "수익(매출액)", 2015, "150"))
    return rows


def _oldRow(fp, label, year, val):
    r = _row(fp, "IS2", None, label, year, "d", 4, "Y", "ConsolidatedMember", val)
    r["rceptNo"] = "20" + fp[:4] + "00000000"  # 연도순 rceptNo (XBRL 최신 우선 dedup)
    return r


@pytest.fixture
def statementEnv() -> pl.DataFrame:
    """합성 셀 DataFrame (XBRL+옛 통합) — 순수 _statementFromCells 직접 검증."""
    return pl.DataFrame(_statementRows(), schema=CELL_SCHEMA)


def test_read_statement_unifies_xbrl_and_old(statementEnv) -> None:
    """항목명 정규화 통합 — '매출액'(XBRL+옛 통합) 한 행이 2025~2020 연속, 개명 '수익(매출액)' 별 행."""
    from dartlab.providers.dart.panel.cell import _statementFromCells

    w = _statementFromCells(statementEnv, statement="IS2", freq="year", scope="consolidated")
    assert w is not None
    years = sorted([c for c in w.columns if c.isdigit()])
    assert years == ["2015", "2020", "2024", "2025"]  # XBRL 경계(2024) 넘어 옛 연장
    mae = w.filter(pl.col("account") == "매출액")
    assert mae.height == 1  # (주30)/(주28) 통합
    assert mae["2025"][0] == "300" and mae["2020"][0] == "200"  # XBRL + 옛 한 행
    su = w.filter(pl.col("account") == "수익(매출액)")
    assert su.height == 1 and su["2015"][0] == "150"  # 개명 별 행 (숨김 0)


def test_read_statement_old_acode_none(statementEnv) -> None:
    """옛 셀은 acode 없이도 항목명으로 statement view 에 들어감."""
    from dartlab.providers.dart.panel.cell import _statementFromCells

    w = _statementFromCells(statementEnv, statement="IS2", freq="year", scope="consolidated")
    assert "2015" in w.columns  # acode=None 옛 셀이 과거 열 제공


@pytest.fixture
def renameEnv(tmp_path, monkeypatch):
    """개명 stitch — 최근 '매출액'(2023/2022) + 옛 '수익(매출액)'(2022/2021), 2022 금액 겹침."""
    import dartlab.config as cfg

    _ = (tmp_path, monkeypatch)
    rows = [
        # 최신 filing(높은 rceptNo) '매출액' — 2023/2022
        {**_oldRow("2023Q4", "매출액 (주30)", 2023, "10,000"), "rceptNo": "20240301000000"},
        {**_oldRow("2023Q4", "매출액 (주30)", 2022, "9,000"), "rceptNo": "20240301000000"},
        # 옛 filing(낮은 rceptNo) '수익(매출액)' — 2022(겹침)/2021
        {**_oldRow("2022Q4", "수익(매출액)", 2022, "9,000"), "rceptNo": "20230301000000"},
        {**_oldRow("2022Q4", "수익(매출액)", 2021, "8,000"), "rceptNo": "20230301000000"},
    ]
    return pl.DataFrame(rows, schema=CELL_SCHEMA)


def test_read_statement_rename_stitch(renameEnv) -> None:
    """개명 항목 → 금액 겹침(2022)으로 한 줄, **최근 이름**('매출액') 기준."""
    from dartlab.providers.dart.panel.cell import _statementFromCells

    w = _statementFromCells(renameEnv, statement="IS2", freq="year", scope="consolidated")
    assert w.height == 1, "개명 전후가 한 행으로 통합 (수익(매출액) 별 행 아님)"
    assert w["account"][0] == "매출액"  # 최근 이름 기준
    row = w.row(0, named=True)
    assert row["2023"] == "10,000" and row["2022"] == "9,000" and row["2021"] == "8,000"  # 전 기간 연속


@pytest.fixture
def cooccurEnv(tmp_path, monkeypatch):
    """공존 가드 — 한 공시(같은 rceptNo)에 '단기차입금의증가'·'단기차입금의감소' 별개 라인, 2022 금액(5,000) 우연일치."""
    _ = (tmp_path, monkeypatch)
    rc = "20240301000000"
    rows = [
        {**_oldRow("2023Q4", "단기차입금의증가", 2023, "8,000"), "rceptNo": rc},
        {**_oldRow("2023Q4", "단기차입금의증가", 2022, "5,000"), "rceptNo": rc},
        {**_oldRow("2023Q4", "단기차입금의감소", 2023, "3,000"), "rceptNo": rc},
        {**_oldRow("2023Q4", "단기차입금의감소", 2022, "5,000"), "rceptNo": rc},  # 2022 금액 겹침(우연)
    ]
    return pl.DataFrame(rows, schema=CELL_SCHEMA)


def test_stitch_cooccurrence_separates_distinct(cooccurEnv) -> None:
    """공존(한 공시 distinct 라인) 별개계정은 금액 우연일치로도 병합 안 됨 — over-merge 데이터손실 가드.

    가드 없으면 (2022,'5,000') 공유로 stitch 가 증가⊕감소 병합 → 한쪽 2023 값 손실. 가드면 분리 유지.
    """
    from dartlab.providers.dart.panel.cell import _statementFromCells

    w = _statementFromCells(cooccurEnv, statement="IS2", freq="year", scope="consolidated")
    assert w is not None
    accounts = set(w["account"].to_list())
    assert "단기차입금의증가" in accounts and "단기차입금의감소" in accounts, "공존 별개계정 분리 유지"
    inc = w.filter(pl.col("account") == "단기차입금의증가").row(0, named=True)
    dec = w.filter(pl.col("account") == "단기차입금의감소").row(0, named=True)
    assert inc["2023"] == "8,000" and dec["2023"] == "3,000"  # 둘 다 2023 값 보존(손실 0)


# ── native 재무비율 (소문자 ratios — BS/IS/CF native 항목 → core 공식, panel 자급) ──


def test_label_to_snake_id() -> None:
    """core mappings 재색인 — 정규화 항목명 → snakeId (calcRatioSeries 재료 키)."""
    from dartlab.providers.dart.panel.cell import _labelToSnakeId

    m = _labelToSnakeId()
    assert m.get("매출액") == "sales"
    assert m.get("자산총계") == "total_assets"
    assert m.get("자본총계") == "total_stockholders_equity"


def _ratioStmt(rows: list[tuple[str, dict[str, str]]]) -> pl.DataFrame:
    """합성 native statement wide — [(account, {period: valueRaw})] → [account, label, *period]."""
    periods = sorted({p for _, vals in rows for p in vals}, reverse=True)
    recs = []
    for account, vals in rows:
        rec: dict = {"account": account, "label": account}
        for p in periods:
            rec[p] = vals.get(p)
        recs.append(rec)
    return pl.DataFrame(recs)


def test_assemble_ratio_series() -> None:
    """버킷=읽은 표(BS/IS/CF), snakeId=mappings, △/콤마 파싱, period union 오름차순 정렬."""
    from dartlab.providers.dart.panel.cell import _assembleRatioSeries

    bs = _ratioStmt([("자산총계", {"2024": "1,000", "2023": "900"}), ("자본총계", {"2024": "600", "2023": "500"})])
    is2 = _ratioStmt([("매출액", {"2024": "2,000", "2023": "1,800"}), ("당기순이익", {"2024": "△100", "2023": "200"})])
    cf = _ratioStmt([("영업활동현금흐름", {"2024": "300", "2023": "250"})])

    out = _assembleRatioSeries({"BS": bs, "IS": is2, "CF": cf})
    assert out is not None
    series, years = out
    assert years == ["2023", "2024"]  # 오름차순 (calcRatioSeries yoyLag 정합)
    assert series["BS"]["total_assets"] == [900.0, 1000.0]
    assert series["IS"]["sales"] == [1800.0, 2000.0]
    assert series["IS"]["net_profit"] == [200.0, -100.0]  # △ 음수
    assert series["CF"]["operating_cashflow"] == [250.0, 300.0]


def test_assemble_ratio_series_empty() -> None:
    """재료 0 → None."""
    from dartlab.providers.dart.panel.cell import _assembleRatioSeries

    assert _assembleRatioSeries({"BS": None, "IS": None, "CF": None}) is None


def test_read_ratios_wide(monkeypatch) -> None:
    """readRatios → [ratio, label, *period] wide, roe/debtRatio 행, period 최신 좌측, 한글 라벨."""
    import dartlab.providers.dart.panel.cell as C

    bs = _ratioStmt(
        [
            ("자산총계", {"2024": "1000", "2023": "900"}),
            ("자본총계", {"2024": "600", "2023": "500"}),
            ("부채총계", {"2024": "400", "2023": "400"}),
        ]
    )
    is2 = _ratioStmt(
        [
            ("매출액", {"2024": "2000", "2023": "1800"}),
            ("영업이익", {"2024": "300", "2023": "250"}),
            ("당기순이익", {"2024": "200", "2023": "150"}),
        ]
    )
    cf = _ratioStmt([("영업활동현금흐름", {"2024": "350", "2023": "300"})])
    table = {"BS": bs, "IS2": is2, "CF": cf}
    # readRatios 는 _cellsFromPanel 1회 파싱 후 _resolveStatement(variants) 로 bs/is/cf 해소.
    monkeypatch.setattr(C, "_cellsFromPanel", lambda code, *a, **k: pl.DataFrame({"_": [1]}))
    monkeypatch.setattr(C, "_resolveStatement", lambda df, *, variants, **k: table.get(variants[0]))

    w = C.readRatios("X", freq="year")
    assert w is not None
    assert w.columns[:2] == ["ratio", "label"]
    pcols = [c for c in w.columns if c not in ("ratio", "label")]
    assert pcols == ["2024", "2023"]  # 최신 좌측
    ratios = w["ratio"].to_list()
    assert "roe" in ratios and "debtRatio" in ratios
    assert w.filter(pl.col("ratio") == "roe").row(0, named=True)["2024"] is not None
    assert w.filter(pl.col("ratio") == "roe").row(0, named=True)["label"] == "자기자본이익률 (ROE %)"


# ── 주석(NT_) 정규화 — c.panel("NT_D834300") 5표 엔진 공유 (readNoteStatement) ──


def test_collapse_degen_axis() -> None:
    """단일축 lineitem 의 degenerate axis → "" (depth-1 통과), 진짜 축 멤버는 보존(matrix 배제)."""
    from dartlab.providers.dart.panel.cell import _collapseDegenAxis

    assert _collapseDegenAxis("ConsolidatedMember|ReportedAmount") == ""
    assert _collapseDegenAxis("ConsolidatedMember") == ""
    assert _collapseDegenAxis("") == ""
    assert _collapseDegenAxis("SemiconductorMember") == "SemiconductorMember"  # 진짜 축 보존
    assert _collapseDegenAxis("ConsolidatedMember|SemiconductorMember") == "ConsolidatedMember|SemiconductorMember"


def test_read_note_statement_non_nt_returns_none() -> None:
    """NT_ 아닌 statement → None (5표 키는 readStatement 담당)."""
    from dartlab.providers.dart.panel.cell import readNoteStatement

    assert readNoteStatement("005930", statement="IS2") is None


def test_read_note_statement_reuses_engine(monkeypatch) -> None:
    """NT_ → _noteCellsFromPanel 셀 → 본진 _statementFromCells 재사용 (항목명×period, 옛 acode=None 연장)."""
    import dartlab.providers.dart.panel.cell as C

    cells = [
        _row("2024Q4", "NT_D834300", "ifrs-full_ExpenseByNature", "계", 2024, "d", 4, "Y", "", "268,144,942"),
        _row("2024Q4", "NT_D834300", "ifrs-full_ExpenseByNature", "계", 2023, "d", 4, "Y", "", "252,368,518"),
        _row("2024Q4", "NT_D834300", "ifrs-full_EmployeeBenefitsExpense", "급여", 2024, "d", 4, "Y", "", "32,877,167"),
        _oldRow("2020Q4", "급여", 2020, "25,054,684"),  # 옛 acode=None 연장
    ]
    cells[-1]["statement"] = "NT_D834300"
    monkeypatch.setattr(C, "_noteCellsFromPanel", lambda code, nt, ns="kr": pl.DataFrame(cells, schema=CELL_SCHEMA))

    w = C.readNoteStatement("X", statement="NT_D834300", freq="year")
    assert w is not None
    assert sorted(c for c in w.columns if c.isdigit()) == ["2020", "2023", "2024"]  # 옛 연장
    tot = w.filter(pl.col("account") == "계")
    assert tot.height == 1 and tot["2024"][0] == "268,144,942" and tot["2023"][0] == "252,368,518"
    sal = w.filter(pl.col("account") == "급여")
    assert sal["2024"][0] == "32,877,167" and sal["2020"][0] == "25,054,684"  # XBRL+옛 한 행


# ── 라벨 정규화 — era 표기변형 흡수 + over-merge 안전 + 쌍둥이 계약 (_attempts/pastAxisConnection 100사 검증) ──


def test_normalize_label_twin_and_variants() -> None:
    """``_normalizeLabel``(polars) ≡ ``_normKey``(scalar) 쌍둥이 + 표기변형 흡수 + over-merge 안전."""
    from dartlab.providers.dart.panel.cell import _normalizeLabel, _normKey

    # 표기변형 흡수 — 같은 항목이 같은 키로 (과거 era 연결)
    for raw, expect in [
        ("매출액 (주30)", "매출액"),  # (주N) strip
        ("Ⅰ.매출액", "매출액"),  # 로마numeral 섹션 prefix
        ("Ⅲ. 영업이익", "영업이익"),  # 로마 + 공백
        ("주당이익(단위:원)", "주당이익"),  # (단위) annotation
        ("기본주당이익(손실)(단위:원)", "기본주당이익(손실)"),  # (단위)만, (손실) 보존
        ("자산ㆍ부채의변동", "자산부채의변동"),  # 중점 strip
    ]:
        assert _normKey(raw) == expect, f"normKey({raw!r})={_normKey(raw)!r} != {expect!r}"
        got = pl.DataFrame({"label": [raw]}).select(_normalizeLabel(pl.col("label")))["label"][0]
        assert got == expect == _normKey(raw), f"normalizeLabel({raw!r})={got!r} (쌍둥이 불일치)"

    # over-merge 안전 — 의미 qualifier·아라비아 ordinal 은 *구별 보존*(다른 키)
    for a, b in [
        ("단기금융자산", "장기금융자산"),  # 단기↔장기
        ("유형자산의처분", "무형자산의처분"),  # 유형↔무형
        ("1.수입보증금", "2.수입보증금"),  # 아라비아 ordinal 보존(리스트항목 오병합 회피)
        ("중단영업이익", "영업이익"),  # 중단영업 보존
    ]:
        assert _normKey(a) != _normKey(b), f"over-merge: {a!r} ≡ {b!r}"
