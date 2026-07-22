"""Gather Data Workbench metadata provider 계약 검증."""

from __future__ import annotations


def testGatherDeclaresL1RegistryProvider():
    from dartlab.gather.dataProduct import DATA_PRODUCT_DESCRIPTOR

    assert DATA_PRODUCT_DESCRIPTOR["owner"] == "gather"
    assert DATA_PRODUCT_DESCRIPTOR["layer"] == "L1"
    assert DATA_PRODUCT_DESCRIPTOR["registries"] == (
        {
            "module": "dartlab.gather.entry.dispatch",
            "attribute": "AXIS_REGISTRY",
            "kind": "source",
            "subjectParam": "target",
        },
    )
