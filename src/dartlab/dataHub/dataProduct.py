"""Data Workbench 자체의 capability metadata provider."""

DATA_PRODUCT_DESCRIPTOR = {
    "owner": "dataHub",
    "layer": "L2.5",
    "callable": {"module": "dartlab.dataHub", "attribute": "DataHub"},
    "registries": (
        {
            "module": "dartlab.dataHub.entry",
            "attribute": "_AXIS_REGISTRY",
            "kind": "platform",
            "subjectParam": None,
        },
    ),
}
