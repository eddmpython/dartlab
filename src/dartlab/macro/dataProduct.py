"""Macro가 소유한 Data Workbench metadata provider."""

DATA_PRODUCT_DESCRIPTOR = {
    "owner": "macro",
    "layer": "L2",
    "callable": {"module": "dartlab.macro", "attribute": "Macro"},
    "registries": (
        {
            "module": "dartlab.macro",
            "attribute": "_AXIS_REGISTRY",
            "kind": "analysis",
            "subjectParam": "target",
        },
    ),
}
