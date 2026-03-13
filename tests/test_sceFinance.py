"""SCE(자본변동표) 피벗 테스트."""

from tests.conftest import SAMSUNG, requires_finance


class TestSceMapper:
    def test_normalizeCauseExact(self):
        from dartlab.engines.dart.finance.sceMapper import normalizeCause
        assert normalizeCause("당기순이익") == "net_income"
        assert normalizeCause("기초자본") == "beginning_equity"
        assert normalizeCause("기말자본") == "ending_equity"
        assert normalizeCause("배당금 지급") == "dividends"
        assert normalizeCause("자기주식의 취득") == "treasury_acquired"

    def test_normalizeCauseSpaceRemoval(self):
        from dartlab.engines.dart.finance.sceMapper import normalizeCause
        assert normalizeCause("기초 자 본") == "beginning_equity"
        assert normalizeCause("배당 금 지급") == "dividends"

    def test_normalizeCauseFallback(self):
        from dartlab.engines.dart.finance.sceMapper import normalizeCause
        assert normalizeCause("미래를위한해외사업장XYZ") == "fx_translation"
        assert normalizeCause("종목별공정가치변동") == "fvoci_valuation"

    def test_normalizeCauseUnmapped(self):
        from dartlab.engines.dart.finance.sceMapper import normalizeCause
        result = normalizeCause("완전히_알수없는_계정명_XYZABC")
        assert result.startswith("unmapped:")

    def test_normalizeDetailBasic(self):
        from dartlab.engines.dart.finance.sceMapper import normalizeDetail
        assert normalizeDetail("자본금 [member]") == "share_capital"
        assert normalizeDetail("이익잉여금 [구성요소]") == "retained_earnings"
        assert normalizeDetail(None) == "unknown"
        assert normalizeDetail("") == "unknown"

    def test_normalizeDetailPipe(self):
        from dartlab.engines.dart.finance.sceMapper import normalizeDetail
        assert normalizeDetail("지배기업 소유주지분|이익잉여금 [member]") == "retained_earnings"
        assert normalizeDetail("연결재무제표 [member]") == "total"

    def test_normalizeDetailFallback(self):
        from dartlab.engines.dart.finance.sceMapper import normalizeDetail
        assert normalizeDetail("기타포괄손익누계액 관련항목 [member]") == "accumulated_oci"

    def test_unmapped_rows_are_preserved_in_matrix(self):
        import polars as pl
        from dartlab.engines.dart.finance.pivot import _buildSceMatrixFromDf

        df = pl.DataFrame(
            {
                "bsns_year": ["2025", "2025"],
                "reprt_nm": ["4분기", "4분기"],
                "sj_div": ["SCE", "SCE"],
                "fs_div": ["CFS", "CFS"],
                "account_id": ["unknown_1", "known_1"],
                "account_nm": ["완전히알수없는변동", "기말자본"],
                "account_detail": ["완전히알수없는상세", "연결재무제표 [member]"],
                "thstrm_amount": ["10", "100"],
            }
        )

        result = _buildSceMatrixFromDf(df)
        assert result is not None
        matrix, years = result
        assert years == ["2025"]
        year_data = matrix["2025"]
        assert "ending_equity" in year_data
        preserved_cause = [k for k in year_data if k.startswith("other_")]
        assert preserved_cause
        preserved_detail = list(year_data[preserved_cause[0]].keys())
        assert any(k.startswith("detail_") for k in preserved_detail)


@requires_finance
class TestScePivot:
    def test_buildSceMatrixBasic(self):
        from dartlab.engines.dart.finance.pivot import buildSceMatrix
        result = buildSceMatrix(SAMSUNG)
        assert result is not None
        matrix, years = result
        assert len(years) >= 1
        assert isinstance(matrix, dict)
        latestYear = years[-1]
        assert latestYear in matrix
        assert "ending_equity" in matrix[latestYear]

    def test_buildSceMatrixCauses(self):
        from dartlab.engines.dart.finance.pivot import buildSceMatrix
        result = buildSceMatrix(SAMSUNG)
        matrix, years = result
        allCauses = set()
        for year in matrix:
            allCauses.update(matrix[year].keys())
        assert "beginning_equity" in allCauses
        assert "ending_equity" in allCauses
        assert "net_income" in allCauses

    def test_buildSceAnnualBasic(self):
        from dartlab.engines.dart.finance.pivot import buildSceAnnual
        result = buildSceAnnual(SAMSUNG)
        assert result is not None
        series, years = result
        assert "SCE" in series
        assert len(years) >= 1
        assert "ending_equity__total" in series["SCE"]

    def test_buildSceAnnualSeriesLength(self):
        from dartlab.engines.dart.finance.pivot import buildSceAnnual
        result = buildSceAnnual(SAMSUNG)
        series, years = result
        nYears = len(years)
        for key, vals in series["SCE"].items():
            assert len(vals) == nYears, f"{key}: {len(vals)} != {nYears}"

    def test_sceMatrixIntegrity(self):
        from dartlab.engines.dart.finance.pivot import buildSceMatrix
        result = buildSceMatrix(SAMSUNG)
        matrix, years = result
        for year in years[-2:]:
            yearData = matrix.get(year, {})
            beginTotal = yearData.get("beginning_equity", {}).get("total")
            endTotal = yearData.get("ending_equity", {}).get("total")
            if beginTotal is not None and endTotal is not None and endTotal != 0:
                diff = endTotal - beginTotal
                changes = 0
                for cause, details in yearData.items():
                    if cause in ("beginning_equity", "ending_equity", "adjusted_beginning", "equity_change_total"):
                        continue
                    val = details.get("total")
                    if val is not None:
                        changes += val
                gap = diff - changes
                gapPct = abs(gap / endTotal * 100)
                assert gapPct < 50, f"{year}: gap {gapPct:.1f}% > 50%"
