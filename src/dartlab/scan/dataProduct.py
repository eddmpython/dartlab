"""Scan이 소유한 Data Workbench metadata provider."""

DATA_PRODUCT_DESCRIPTOR = {
    "owner": "scan",
    "layer": "L1.5",
    "callable": {"module": "dartlab.scan", "attribute": "Scan"},
    "registries": (
        {
            "module": "dartlab.scan.router",
            "attribute": "_AXIS_REGISTRY",
            "kind": "table",
            "subjectParam": None,
        },
    ),
}
