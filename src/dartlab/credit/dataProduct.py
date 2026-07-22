"""Credit이 소유한 Data Workbench metadata provider."""

DATA_PRODUCT_DESCRIPTOR = {
    "owner": "credit",
    "layer": "L2",
    "concurrencyGroup": "companyData",
    "callable": {"module": "dartlab.credit", "attribute": None},
    "registries": (
        {
            "module": "dartlab.credit",
            "attribute": "_AXIS_REGISTRY",
            "kind": "analysis",
            "subjectParam": "target",
            "selectorRequired": True,
        },
    ),
}
