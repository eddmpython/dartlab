"""나머지 finance 모듈 통합 테스트."""

import polars as pl

from tests.conftest import SAMSUNG, requires_samsung


@requires_samsung
class TestDividend:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.dividend import dividend

        r = dividend(SAMSUNG)
        assert r is not None
        assert r.timeSeries is not None
        assert isinstance(r.timeSeries, pl.DataFrame)


@requires_samsung
class TestEmployee:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.employee import employee

        r = employee(SAMSUNG)
        assert r is not None
        assert r.timeSeries is not None


@requires_samsung
class TestMajorHolder:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.majorHolder import majorHolder

        r = majorHolder(SAMSUNG)
        assert r is not None
        assert r.majorHolder is not None
        assert r.majorRatio > 0

    def test_holder_overview(self):
        from dartlab.engines.company.dart.docs.finance.majorHolder import holderOverview

        r = holderOverview(SAMSUNG)
        assert r is not None


@requires_samsung
class TestShareCapital:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.shareCapital import shareCapital

        r = shareCapital(SAMSUNG)
        assert r is not None
        assert r.outstandingShares > 0


@requires_samsung
class TestSubsidiary:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.subsidiary import subsidiary

        r = subsidiary(SAMSUNG)
        assert r is not None
        assert r.investments is not None


@requires_samsung
class TestBond:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.bond import bond

        r = bond(SAMSUNG)
        # 삼성전자는 채무증권이 없을 수 있음
        # None이어도 에러 없이 반환만 확인


@requires_samsung
class TestSegment:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.segment import segments

        r = segments(SAMSUNG)
        assert r is not None
        assert r.tables is not None


@requires_samsung
class TestCostByNature:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.costByNature import costByNature

        r = costByNature(SAMSUNG)
        assert r is not None
        assert r.timeSeries is not None


@requires_samsung
class TestAffiliate:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.affiliate import affiliates

        r = affiliates(SAMSUNG)
        assert r is not None
        assert r.profiles is not None


@requires_samsung
class TestAudit:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.audit import audit

        r = audit(SAMSUNG)
        assert r is not None
        assert r.opinionDf is not None
        assert isinstance(r.opinionDf, pl.DataFrame)

    def test_fee(self):
        from dartlab.engines.company.dart.docs.finance.audit import audit

        r = audit(SAMSUNG)
        assert r is not None
        assert r.feeDf is not None


@requires_samsung
class TestExecutive:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.executive import executive

        r = executive(SAMSUNG)
        assert r is not None
        assert r.executiveDf is not None
        assert isinstance(r.executiveDf, pl.DataFrame)


@requires_samsung
class TestExecutivePay:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.executivePay import executivePay

        r = executivePay(SAMSUNG)
        assert r is not None
        assert r.payByTypeDf is not None
        assert isinstance(r.payByTypeDf, pl.DataFrame)


@requires_samsung
class TestBoardOfDirectors:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.boardOfDirectors import boardOfDirectors

        r = boardOfDirectors(SAMSUNG)
        assert r is not None
        assert r.boardDf is not None
        assert isinstance(r.boardDf, pl.DataFrame)


@requires_samsung
class TestCapitalChange:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.capitalChange import capitalChange

        r = capitalChange(SAMSUNG)
        assert r is not None
        assert r.capitalDf is not None or r.shareTotalDf is not None


@requires_samsung
class TestContingentLiability:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.contingentLiability import contingentLiability

        r = contingentLiability(SAMSUNG)
        # 삼성전자는 우발부채가 없을 수 있음 — None이어도 에러 없이 반환 확인


@requires_samsung
class TestRelatedPartyTx:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.relatedPartyTx import relatedPartyTx

        r = relatedPartyTx(SAMSUNG)
        # None이어도 에러 없이 반환 확인


@requires_samsung
class TestSanction:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.sanction import sanction

        r = sanction(SAMSUNG)
        # 제재가 없을 수 있음 — None이어도 에러 없이 반환 확인


@requires_samsung
class TestRnd:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.rnd import rnd

        r = rnd(SAMSUNG)
        assert r is not None
        assert r.rndDf is not None
        assert isinstance(r.rndDf, pl.DataFrame)


@requires_samsung
class TestInternalControl:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.internalControl import internalControl

        r = internalControl(SAMSUNG)
        assert r is not None
        assert r.controlDf is not None
        assert isinstance(r.controlDf, pl.DataFrame)


@requires_samsung
class TestAffiliateGroup:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.affiliateGroup import affiliateGroup

        r = affiliateGroup(SAMSUNG)
        assert r is not None
        assert r.groupName is not None
        assert r.affiliateDf is not None
        assert isinstance(r.affiliateDf, pl.DataFrame)


@requires_samsung
class TestFundraising:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.fundraising import fundraising

        r = fundraising(SAMSUNG)
        assert r is not None
        # 삼성전자는 발행 실적 없음
        assert r.noData is True


@requires_samsung
class TestSalesOrder:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.salesOrder import salesOrder

        r = salesOrder(SAMSUNG)
        assert r is not None
        assert r.salesDf is not None
        assert isinstance(r.salesDf, pl.DataFrame)


@requires_samsung
class TestProductService:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.productService import productService

        r = productService(SAMSUNG)
        assert r is not None
        assert r.productDf is not None
        assert isinstance(r.productDf, pl.DataFrame)


@requires_samsung
class TestRiskDerivative:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.riskDerivative import riskDerivative

        r = riskDerivative(SAMSUNG)
        assert r is not None
        assert r.fxDf is not None
        assert isinstance(r.fxDf, pl.DataFrame)


@requires_samsung
class TestArticlesOfIncorporation:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.articlesOfIncorporation import articlesOfIncorporation

        r = articlesOfIncorporation(SAMSUNG)
        assert r is not None
        assert r.purposes or r.changes or r.noData


@requires_samsung
class TestOtherFinance:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.otherFinance import otherFinance

        r = otherFinance(SAMSUNG)
        assert r is not None
        assert r.badDebt or r.inventory or r.noData


@requires_samsung
class TestCompanyHistory:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.companyHistory import companyHistory

        r = companyHistory(SAMSUNG)
        assert r is not None
        assert r.events
        assert r.eventsDf is not None
        assert isinstance(r.eventsDf, pl.DataFrame)


@requires_samsung
class TestShareholderMeeting:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.shareholderMeeting import shareholderMeeting

        r = shareholderMeeting(SAMSUNG)
        assert r is not None
        assert r.agendas or r.textOnly


@requires_samsung
class TestAuditSystem:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.auditSystem import auditSystem

        r = auditSystem(SAMSUNG)
        assert r is not None
        assert r.committee or r.activity or r.textOnly


@requires_samsung
class TestInvestmentInOther:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.investmentInOther import investmentInOther

        r = investmentInOther(SAMSUNG)
        assert r is not None
        assert r.investments or r.noData


@requires_samsung
class TestCompanyOverviewDetail:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.companyOverviewDetail import companyOverviewDetail

        r = companyOverviewDetail(SAMSUNG)
        assert r is not None
        assert r.corpName is not None
