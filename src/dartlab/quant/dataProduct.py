"""Quant가 소유한 Data Workbench metadata provider."""

DATA_PRODUCT_DESCRIPTOR = {
    "owner": "quant",
    "layer": "L2",
    "concurrencyGroup": "companyData",
    "callable": {"module": "dartlab.quant", "attribute": "Quant"},
    "registries": (
        {
            "module": "dartlab.quant._registry",
            "attribute": "_AXIS_REGISTRY",
            "kind": "analysis",
            "subjectParam": "stockCode",
        },
    ),
}
