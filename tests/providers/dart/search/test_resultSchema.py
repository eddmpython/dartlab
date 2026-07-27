"""providers/dart/search/resultSchema.py mirror tests."""

from __future__ import annotations

import polars as pl


def test_result_schema_import_and_empty() -> None:
    from dartlab.providers.dart.search.resultSchema import normalizeSearchResult

    assert normalizeSearchResult(pl.DataFrame()).height == 0


def test_result_schema_derives_data_as_of_from_dart_receipt() -> None:
    from dartlab.providers.dart.search.resultSchema import normalizeSearchResult

    out = normalizeSearchResult(
        pl.DataFrame(
            {
                "rcept_no": ["20250515001545"],
                "section_order": [0],
                "report_nm": ["분기보고서 (2025.03)"],
            }
        )
    )

    assert out.row(0, named=True)["dataAsOf"] == "20250515"


def test_result_schema_keeps_column_null_for_first_rows() -> None:
    """앞 100 행이 전부 null 인 컬럼이 뒤에서 값을 받아도 죽지 않는다.

    뉴스 문서만 docKey 를 채우고 공시 행은 비우는데, 공시가 앞에 몰리면
    dtype 추론(기본 infer_schema_length=100)이 Null 로 확정해 뒤의 문자열을
    못 받고 ComputeError 로 검색 전체가 죽었다. 원본 스키마를 물려주는지 검증.
    """
    from dartlab.providers.dart.search.resultSchema import normalizeSearchResult

    rows = 150
    frame = pl.DataFrame(
        {
            "rcept_no": ["20250515001545"] * rows + [f"news:{i:016x}" for i in range(rows)],
            "section_order": [0] * (rows * 2),
            # 앞 절반은 null, 뒤 절반만 값 (뉴스 docKey 와 동형).
            "docKey": [None] * rows + [f"news:{i:016x}" for i in range(rows)],
            # 반대로 앞만 값, 뒤는 null 인 boolean (공시 deleted 와 동형).
            "deleted": [False] * rows + [None] * rows,
        },
        schema={"rcept_no": pl.Utf8, "section_order": pl.Int64, "docKey": pl.Utf8, "deleted": pl.Boolean},
    )

    out = normalizeSearchResult(frame)

    assert out.height == rows * 2
    assert out.schema["docKey"] == pl.Utf8
    assert out.schema["deleted"] == pl.Boolean
    assert out.row(rows, named=True)["docKey"] == f"news:{0:016x}"
    # 뉴스 행은 sourceRef 가 news: 접두를 유지한다.
    assert out.row(rows, named=True)["sourceRef"].startswith("news:")


def test_result_schema_contract_columns_typed() -> None:
    """계약 컬럼 dtype 은 원본과 무관하게 고정된다."""
    from dartlab.providers.dart.search.resultSchema import normalizeSearchResult

    out = normalizeSearchResult(
        pl.DataFrame({"rcept_no": ["20250515001545"], "section_order": [0], "text": ["반도체 매출"]})
    )

    assert out.schema["answerable"] == pl.Boolean
    for col in ("source", "sourceRef", "dataAsOf", "snippet", "notAnswerableReason", "fieldCards"):
        assert out.schema[col] == pl.Utf8
