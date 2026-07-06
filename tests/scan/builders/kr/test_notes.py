"""notes 빌더 단위 테스트 + 실데이터 스모크.

카탈로그 도출·wide->long 변환을 합성 데이터로 검증하고 (데이터 불필요),
requires_data 로 삼성 실 panel 의 readNoteStatements 배치 위임을 확인한다.
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.scan.builders.kr.notes import SCAN_NOTE_CONCEPTS, _noteConceptSpecs, _wideToLong


class TestConceptSpecs:
    def test_matches_derivation(self):
        assert SCAN_NOTE_CONCEPTS == _noteConceptSpecs()

    def test_registered_single_axis_notes_included(self):
        bares = {b for b, _, _ in SCAN_NOTE_CONCEPTS}
        # 대표 단일축 note 는 포함
        assert "inventory" in bares
        assert "tax" in bares
        assert "lease" in bares

    def test_text_notes_excluded(self):
        # valueType=text 주석(우발부채·유의적회계정책 등)은 횡단 대상 아님
        bares = {b for b, _, _ in SCAN_NOTE_CONCEPTS}
        assert "contingencies" not in bares
        assert "accountingPolicies" not in bares

    def test_spec_tuple_shape(self):
        for spec in SCAN_NOTE_CONCEPTS:
            bare, ntKey, label = spec
            assert bare and not bare.startswith("note.")
            assert ntKey.startswith("NT_")
            assert label


class TestWideToLong:
    def test_unpivot_drops_null_and_tags_code(self):
        wide = pl.DataFrame(
            {
                "account": ["상품", "제품"],
                "label": ["상품", "제품"],
                "2024": ["1,000", "2,000"],
                "2023": ["900", None],
            }
        )
        long = _wideToLong(wide, "005930")
        assert long is not None
        assert set(long.columns) == {"stockCode", "account", "label", "period", "value"}
        # (제품, 2023) null 제외 -> 3 행
        assert long.height == 3
        assert set(long["stockCode"].unique().to_list()) == {"005930"}
        rec = {(r["account"], r["period"]): r["value"] for r in long.iter_rows(named=True)}
        assert rec[("상품", "2024")] == "1,000"
        assert ("제품", "2023") not in rec

    def test_no_period_cols_returns_none(self):
        wide = pl.DataFrame({"account": ["x"], "label": ["x"]})
        assert _wideToLong(wide, "005930") is None


@pytest.mark.requires_data
class TestRealPanelDelegation:
    def test_readNoteStatements_batch(self):
        from dartlab.providers.dart.panel.cell import readNoteStatements

        ntKeys = [ntKey for _, ntKey, _ in SCAN_NOTE_CONCEPTS]
        out = readNoteStatements("005930", ntKeys, freq="year")
        assert isinstance(out, dict)
        assert len(out) >= 3  # 삼성전자는 다수 단일축 노트 추출
        for wide in out.values():
            assert "account" in wide.columns
            # 최소 1 개 연도 열
            assert any(c not in ("account", "label") for c in wide.columns)
