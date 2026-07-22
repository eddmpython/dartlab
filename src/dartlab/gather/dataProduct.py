"""Gather가 소유한 Data Workbench metadata provider."""

DATA_PRODUCT_DESCRIPTOR = {
    "owner": "gather",
    "layer": "L1",
    "callable": {"module": "dartlab.gather.entry", "attribute": "GatherEntry"},
    "registries": (
        {
            "module": "dartlab.gather.entry.dispatch",
            "attribute": "AXIS_REGISTRY",
            "kind": "source",
            "subjectParam": "target",
        },
    ),
}
