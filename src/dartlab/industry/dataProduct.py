"""Industry가 소유한 Data Workbench metadata provider."""

DATA_PRODUCT_DESCRIPTOR = {
    "owner": "industry",
    "layer": "L2",
    "callable": {"module": "dartlab.industry", "attribute": "Industry"},
    "registries": (
        {
            "module": "dartlab.industry",
            "attribute": "_AXIS_REGISTRY",
            "kind": "graph",
            "subjectParam": "target",
            "selectorRequired": True,
        },
    ),
}
