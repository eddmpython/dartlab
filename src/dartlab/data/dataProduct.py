"""Data Workbench 자체의 capability metadata provider."""

DATA_PRODUCT_DESCRIPTOR = {
    "owner": "data",
    "layer": "L2.5",
    "callable": {"module": "dartlab.data", "attribute": "Data"},
    "registries": (
        {
            "module": "dartlab.data.entry",
            "attribute": "_AXIS_REGISTRY",
            "kind": "platform",
            "subjectParam": None,
        },
    ),
}
