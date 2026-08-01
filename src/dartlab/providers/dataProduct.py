"""Providers가 소유한 Data Workbench metadata provider."""

DATA_PRODUCT_DESCRIPTOR = {
    "owner": "providers",
    "layer": "L1",
    "companySurface": True,
    "registries": (),
    "universeResolvers": (
        {
            "universeKind": "listedEquity",
            "markets": ("KR", "US"),
            "memberships": ("listed",),
            "sourceAliasMarkets": ("US",),
            "module": "dartlab.providers.universe",
            "attribute": "listedEquityUniverse",
        },
    ),
}
