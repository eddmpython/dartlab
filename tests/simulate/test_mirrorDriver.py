"""거울 작업대 물질화 드라이버 : 공개계약 호출 -> 정규 롱 + 카탈로그 전개 + gap (simulate/mirror).

엔진 데이터를 실제로 부른다 (requires_data). 벌크 경로만 (Company 루프 0).

Covers:
- materialize: scan.ratio(roe) 공개계약 호출 -> 척추 롱, 없는 축은 contractError gap.
- catalogItems: scan.account 무target 공개 호출로 860 목록 전개 (손 선별 0).
- bulkSelects: per-company(stockRequired) 축 제외.
- runWorkbench: 소량 목록 -> 정규 롱 + coverage 성적표.
"""

from __future__ import annotations

import pytest

from dartlab.simulate.mirror import bulkSelects, catalogItems, materialize, runWorkbench

pytestmark = [pytest.mark.integration, pytest.mark.requires_data]


def testMaterializeSpine():
    df, gaps = materialize("scan", "ratio", item="roe", freq="Y")
    assert df.height > 100
    assert set(df["lane"].unique()) == {"spine"}
    assert set(df["item"].unique()) == {"roe"}
    assert not gaps


def testMaterializeContractErrorIsGapNotCrash():
    df, gaps = materialize("scan", "__nosuchaxis__")
    assert df.height == 0
    assert len(gaps) == 1 and gaps[0]["gapReason"] == "contractError"


def testCatalogExpandsWithoutHandPick():
    items = catalogItems("scan", "account")
    assert len(items) > 500 and "sales" in items


def testBulkSelectsExcludesPerCompany():
    sel = bulkSelects(expandCatalog=False)
    keys = {(e, a) for e, a, _ in sel}
    assert ("scan", "ratio") in keys
    # quant 기술축(stockRequired=True)은 벌크에서 제외
    assert ("quant", "indicators") not in keys


def testRunWorkbenchCoverage():
    canon, cov, gaps = runWorkbench([("scan", "ratio", "roe"), ("scan", "ratio", "debtRatio")], freq="Y")
    assert canon.height > 200
    assert cov.height >= 1 and "종목" in cov.columns
    assert set(canon["item"].unique()) == {"roe", "debtRatio"}


def testBatchSurvivesOneFailingAxis(monkeypatch):
    """한 축이 fold/호출에서 예외를 던져도 배치 전체가 죽지 않고 나머지가 계속된다 (격리)."""
    import dartlab.simulate.mirror as drv

    real = drv._call

    def flaky(engine, axis, item, **kw):
        if axis == "boom":
            raise RuntimeError("의도적 폭발")
        return real(engine, axis, item, **kw)

    monkeypatch.setattr(drv, "_call", flaky)
    canon, cov, gaps = runWorkbench([("scan", "boom", None), ("scan", "ratio", "roe")], freq="Y")
    assert canon.height > 100  # 정상 축은 물질화됨 (배치 안 죽음)
    assert any(g["gapReason"] == "contractError" for g in gaps.to_dicts())


def testDeclaredIndexReadOnly():
    """캐시된 declared 인덱스는 외부/내부 mutate 가 막혀 캐시 오염이 불가능하다."""
    from dartlab.simulate.mirror import _declaredIndex

    idx = _declaredIndex()
    k = next(iter(idx))
    with pytest.raises(TypeError):
        idx["fake"] = 1  # 외부 dict 읽기전용
    with pytest.raises(TypeError):
        idx[k]["x"] = 1  # 내부 declared 읽기전용
