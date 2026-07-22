"""Analysis가 소유한 Data Workbench metadata provider."""

DATA_PRODUCT_DESCRIPTOR = {
    "owner": "analysis",
    "layer": "L2",
    "callable": {"module": "dartlab.analysis.financial", "attribute": "Analysis"},
    "registries": (
        {
            "module": "dartlab.analysis.financial._registry",
            "attribute": "_AXIS_REGISTRY",
            "kind": "analysis",
            "subjectParam": "stockCode",
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
    ),
}
