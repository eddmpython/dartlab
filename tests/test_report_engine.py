"""reportEngine 통합 테스트."""

import polars as pl

from tests.conftest import SAMSUNG, requires_report


@requires_report
class TestExtract:
    def test_extractRaw(self):
        from dartlab.engines.company.dart.report import extractRaw

        df = extractRaw(SAMSUNG, "dividend")
        assert df is not None
        assert isinstance(df, pl.DataFrame)
        assert df.height > 0
        assert "apiType" in df.columns
        assert "year" in df.columns
        assert "quarterNum" in df.columns

    def test_extractRaw_unknown_apiType(self):
        from dartlab.engines.company.dart.report import extractRaw

        df = extractRaw(SAMSUNG, "nonexistent")
        assert df is None

    def test_extractClean_numeric(self):
        from dartlab.engines.company.dart.report import extractClean

        df = extractClean(SAMSUNG, "employee")
        assert df is not None
        assert df["sm"].dtype == pl.Float64

    def test_extractClean_str_override(self):
        from dartlab.engines.company.dart.report import extractClean

        df = extractClean(SAMSUNG, "auditOpinion")
        assert df is not None
        assert df["adtor"].dtype == pl.Utf8

    def test_extractAnnual(self):
        from dartlab.engines.company.dart.report import extractAnnual

        df = extractAnnual(SAMSUNG, "dividend", quarterNum=4)
        assert df is not None
        assert (df["quarterNum"] == 4).all()

    def test_extractAnnual_default_quarter(self):
        from dartlab.engines.company.dart.report import extractAnnual

        df = extractAnnual(SAMSUNG, "employee")
        assert df is not None
        assert (df["quarterNum"] == 2).all()

    def test_extractResult(self):
        from dartlab.engines.company.dart.report import extractResult

        r = extractResult(SAMSUNG, "dividend")
        assert r is not None
        assert r.apiType == "dividend"
        assert r.label == "배당"
        assert r.nYears > 0
        assert isinstance(r.df, pl.DataFrame)

    def test_null_columns_dropped(self):
        from dartlab.engines.company.dart.report import extractRaw

        df = extractRaw(SAMSUNG, "dividend")
        for c in df.columns:
            assert df[c].null_count() < df.height

    def test_stlm_dt_null_rows_filtered(self):
        from dartlab.engines.company.dart.report import extractRaw

        df = extractRaw(SAMSUNG, "dividend")
        assert df["stlm_dt"].null_count() == 0


@requires_report
class TestPivotDividend:
    def test_basic(self):
        from dartlab.engines.company.dart.report import pivotDividend

        r = pivotDividend(SAMSUNG)
        assert r is not None
        assert len(r.years) > 0
        assert len(r.dps) == len(r.years)
        assert len(r.dividendYield) == len(r.years)
        assert r.nYears == len(r.years)

    def test_has_values(self):
        from dartlab.engines.company.dart.report import pivotDividend

        r = pivotDividend(SAMSUNG)
        nonNull = [v for v in r.dps if v is not None]
        assert len(nonNull) > 0

    def test_df_attached(self):
        from dartlab.engines.company.dart.report import pivotDividend

        r = pivotDividend(SAMSUNG)
        assert isinstance(r.df, pl.DataFrame)


@requires_report
class TestPivotEmployee:
    def test_basic(self):
        from dartlab.engines.company.dart.report import pivotEmployee

        r = pivotEmployee(SAMSUNG)
        assert r is not None
        assert len(r.years) > 0
        assert len(r.totalEmployee) == len(r.years)

    def test_employee_count(self):
        from dartlab.engines.company.dart.report import pivotEmployee

        r = pivotEmployee(SAMSUNG)
        latest = [v for v in r.totalEmployee if v is not None][-1]
        assert latest > 10000


@requires_report
class TestPivotMajorHolder:
    def test_basic(self):
        from dartlab.engines.company.dart.report import pivotMajorHolder

        r = pivotMajorHolder(SAMSUNG)
        assert r is not None
        assert len(r.years) > 0
        assert len(r.totalShareRatio) == len(r.years)

    def test_has_holders(self):
        from dartlab.engines.company.dart.report import pivotMajorHolder

        r = pivotMajorHolder(SAMSUNG)
        assert len(r.latestHolders) > 0
        assert "name" in r.latestHolders[0]
        assert "ratio" in r.latestHolders[0]


@requires_report
class TestPivotExecutive:
    def test_basic(self):
        from dartlab.engines.company.dart.report import pivotExecutive

        r = pivotExecutive(SAMSUNG)
        assert r is not None
        assert r.totalCount > 0
        assert isinstance(r.df, pl.DataFrame)


@requires_report
class TestPivotAudit:
    def test_basic(self):
        from dartlab.engines.company.dart.report import pivotAudit

        r = pivotAudit(SAMSUNG)
        assert r is not None
        assert len(r.years) > 0
        assert len(r.opinions) == len(r.years)
        assert len(r.auditors) == len(r.years)


@requires_report
class TestTypes:
    def test_api_types(self):
        from dartlab.engines.company.dart.report import API_TYPE_LABELS, API_TYPES

        assert len(API_TYPES) == 28
        for t in API_TYPES:
            assert t in API_TYPE_LABELS


@requires_report
class TestCompanyReport:
    def test_accessor_exists(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        assert c.report is not None

    def test_dividend(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        r = c.report.dividend
        assert r is not None
        assert len(r.dps) > 0

    def test_employee(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        r = c.report.employee
        assert r is not None
        assert len(r.totalEmployee) > 0

    def test_majorHolder(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        r = c.report.majorHolder
        assert r is not None
        assert len(r.totalShareRatio) > 0

    def test_executive(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        r = c.report.executive
        assert r is not None
        assert r.totalCount > 0

    def test_audit(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        r = c.report.audit
        assert r is not None
        assert len(r.opinions) > 0

    def test_extract(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        df = c.report.extract("stockTotal")
        assert df is not None
        assert isinstance(df, pl.DataFrame)
        assert df.height > 0

    def test_extractAnnual(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        df = c.report.extractAnnual("corporateBond")
        assert df is not None
        assert isinstance(df, pl.DataFrame)
