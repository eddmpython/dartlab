"""estimateStatements 뷰 빌더 : 라이브러리 SSOT 정렬·라벨·순서 검증 (순수 unit)."""

from __future__ import annotations

from dartlab.simulate.estimateStatements import _CANON, buildEstimateStatements, writeEstimateStatements
from dartlab.simulate.expectationLedger import appendProformaRows


def _seed(tmp_path, *, live=True):
    rows = []
    for stmt, account in (
        ("IS", "revenue"),
        ("IS", "operating_income"),
        ("BS", "total_assets"),
        ("CF", "ocf"),
        ("IS", "ebitda"),
    ):
        for q in (25, 50, 75):
            rows.append(
                {
                    "parentId": "revenue.005930.revenue.Y1.FY2026@x",
                    "code": "005930",
                    "issuedAt": "2026-07-03T09:00",
                    "issuedLive": live,
                    "targetPeriod": "FY2026",
                    "quantile": q,
                    "statement": stmt,
                    "account": account,
                    "value": 100.0 * q,
                    "bsBalanced": True,
                }
            )
    appendProformaRows(rows, baseDir=tmp_path)


def test_view_maps_labels_and_orders(tmp_path):
    _seed(tmp_path)
    df = buildEstimateStatements(baseDir=tmp_path)
    assert df is not None
    # ebitda 는 canonical 매핑에 없음(근사 금지) -> 4계정 x 3분위 = 12행
    assert df.height == 12
    row = df.filter((df["rowKey"] == "revenue") & (df["quantile"] == 50)).row(0, named=True)
    assert row["labelKr"] == "매출액" and row["statement"] == "IS" and row["sortOrder"] == 10
    assert row["parentId"].startswith("revenue.005930.")


def test_view_excludes_backfill(tmp_path):
    _seed(tmp_path, live=False)
    df = buildEstimateStatements(baseDir=tmp_path)
    assert df is not None and df.height == 0  # 공개 뷰 = 라이브 발행분만


def test_write_view_file(tmp_path):
    _seed(tmp_path)
    out = writeEstimateStatements(baseDir=tmp_path)
    assert out is not None and out.name == "estimateStatements.parquet" and out.exists()


def test_canon_has_no_duplicate_rowkeys():
    keys = [(s, k) for s, _, k, _, _, _ in _CANON]
    assert len(keys) == len(set(keys))
