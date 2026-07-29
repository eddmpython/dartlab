"""Company.status 공개 호출자가 core 종목 인덱스를 그대로 노출하는지 검증."""

import polars as pl


def test_companyStatus_delegates_to_default_data_index(monkeypatch) -> None:
    import dartlab.providers.dart.company as companyModule

    expected = pl.DataFrame(
        {
            "stockCode": ["005930"],
            "corpName": [None],
            "rows": [10],
            "yearFrom": ["2023"],
            "yearTo": ["2024"],
            "nDocs": [2],
        },
        schema={
            "stockCode": pl.String,
            "corpName": pl.String,
            "rows": pl.Int64,
            "yearFrom": pl.String,
            "yearTo": pl.String,
            "nDocs": pl.Int64,
        },
    )
    calls: list[tuple] = []

    def fakeBuildIndex(*args, **kwargs):
        calls.append((args, kwargs))
        return expected

    monkeypatch.setattr(companyModule, "buildIndex", fakeBuildIndex)

    assert companyModule.Company.status() is expected
    assert calls == [((), {})]
