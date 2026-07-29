"""providers/dart/search/entityGraph.py mirror tests."""

from __future__ import annotations

import json

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def _catalog() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "stockCode": "042700",
                "corpName": "한미반도체",
                "grade": "dCR-AA",
                "weakAxis": "사업안정성",
                "stageName": "후공정(패키징)",
                "chainName": "반도체",
                "dataAsOf": "20260616",
                "neighborsJson": json.dumps(
                    [
                        {
                            "stockCode": "290520",
                            "corpName": "신도기연",
                            "grade": "dCR-BBB",
                            "weakAxis": "현금흐름",
                            "stageName": "후공정(패키징)",
                        }
                    ],
                    ensure_ascii=False,
                ),
            }
        ]
    )


def test_attach_entity_graph_cards_resolves_stock_code() -> None:
    from dartlab.providers.dart.search.entityGraph import attachEntityGraphCards

    df = pl.DataFrame(
        [
            {
                "corp_name": "042700",
                "stock_code": "042700",
                "sourceRef": "dart:allFilings:x#section=0",
            }
        ]
    )

    out = attachEntityGraphCards(df, catalog=_catalog())
    row = out.row(0, named=True)
    cards = json.loads(row["entityCards"])

    assert row["entityResolved"] is True
    assert row["entityStockCode"] == "042700"
    assert row["entityCardCount"] == 5
    assert any(card["label"] == "creditWeakAxis" and "dCR-AA" in card["value"] for card in cards)
    assert any(card["label"] == "peer:신도기연" for card in cards)
    assert all(card.get("sourceRef") == "dart:allFilings:x#section=0" for card in cards)


def test_attach_entity_graph_cards_no_catalog_is_noop() -> None:
    from dartlab.providers.dart.search.entityGraph import attachEntityGraphCards

    df = pl.DataFrame([{"corp_name": "한미반도체", "sourceRef": "x"}])

    out = attachEntityGraphCards(df, catalog=pl.DataFrame())

    assert out.columns == df.columns
    assert out.to_dicts() == df.to_dicts()


def test_load_entity_graph_catalog_uses_env_path(monkeypatch, tmp_path) -> None:
    from dartlab.providers.dart.search import entityGraph

    path = tmp_path / "entityGraphCatalog.parquet"
    _catalog().write_parquet(path)
    monkeypatch.setenv("DARTLAB_SEARCH_ENTITY_GRAPH_CATALOG", str(path))
    entityGraph._CATALOG_CACHE.clear()

    loaded = entityGraph.loadEntityGraphCatalog()

    assert loaded is not None
    assert loaded.height == 1


def test_load_entity_graph_catalog_corruption_is_visible(monkeypatch, tmp_path, caplog) -> None:
    """optional enrichment 저하는 허용하되 손상 원인을 침묵시키지 않는다."""
    from dartlab.providers.dart.search import entityGraph

    path = tmp_path / "entityGraphCatalog.parquet"
    path.write_bytes(b"not parquet")
    monkeypatch.setenv("DARTLAB_SEARCH_ENTITY_GRAPH_CATALOG", str(path))
    entityGraph._CATALOG_CACHE.clear()
    caplog.set_level("WARNING")

    assert entityGraph.loadEntityGraphCatalog() is None
    assert str(path) in caplog.text
    assert "비활성화" in caplog.text
