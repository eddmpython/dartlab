"""Analysis가 소유한 Data Workbench metadata provider."""

DATA_PRODUCT_DESCRIPTOR = {
    "owner": "analysis",
    "layer": "L2",
    "concurrencyGroup": "companyData",
    "callable": {"module": "dartlab.analysis.financial", "attribute": "Analysis"},
    "registries": (
        {
            "module": "dartlab.analysis.financial._registry",
            "attribute": "_AXIS_REGISTRY",
            "kind": "analysis",
            "subjectParam": "stockCode",
            "selectorRequired": True,
        },
    ),
    "assets": (
        {
            "assetId": "analysis.simulationInputs",
            "kind": "snapshot",
            "label": "시뮬레이터 재무 입력 스냅샷",
            "description": "Company 분기 재무를 요청 기간까지 절단한 read-once 입력",
            "executor": {
                "module": "dartlab.analysis.financial.dataAssets",
                "attribute": "simulationInputs",
            },
            "subjectParam": "subject",
            "validTimeParam": "asOf",
            "temporalSupport": ("latest", "validAt"),
            "metadata": {"stockRequired": True, "returnType": "dict"},
        },
        {
            "assetId": "analysis.edgarFinancialFeatures",
            "kind": "featureSet",
            "label": "EDGAR 영업회사 축약 재무 feature",
            "description": "로컬 companyfacts에서 knownAt 기준으로 구성한 조건부 축약 재무 관측",
            "executor": {
                "module": "dartlab.analysis.financial.dataAssets",
                "attribute": "edgarFinancialFeatures",
            },
            "sourceModules": (
                "dartlab.analysis.financial.filingFeatures",
                "dartlab.analysis.financial.edgarPitState",
                "dartlab.analysis.financial.stepProjection",
                "dartlab.providers.edgar.finance.facts",
            ),
            "subjectParam": "subject",
            "knowledgeTimeParam": "knownAt",
            "temporalSupport": ("knownAt",),
            "selectorKind": "subject",
            "selectorRequired": True,
            "executionMode": "subjectFanout",
            "universeMarkets": ("US",),
            "metadata": {
                "definitionVersion": "edgar-reduced-operating-financial-features-v1",
                "featureCoverage": "reducedOperatingCompany",
                "knownAtRequired": True,
                "market": "US",
                "observationPIT": True,
                "returnType": "feature-observation-input-v1",
                "stockRequired": True,
            },
        },
    ),
}
