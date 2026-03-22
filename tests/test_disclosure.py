"""disclosure 모듈 테스트."""

from tests.conftest import SAMSUNG, requires_samsung


@requires_samsung
class TestBusiness:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.disclosure.business import business

        r = business(SAMSUNG)
        assert r is not None
        assert r.sections is not None


@requires_samsung
class TestOverview:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.disclosure.companyOverview import companyOverview

        r = companyOverview(SAMSUNG)
        assert r is not None


@requires_samsung
class TestMdna:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.disclosure.mdna import mdna

        r = mdna(SAMSUNG)
        assert r is not None
        assert r.sections is not None


@requires_samsung
class TestRawMaterial:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.disclosure.rawMaterial import rawMaterial

        r = rawMaterial(SAMSUNG)
        assert r is not None
