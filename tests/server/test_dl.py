"""Master API dispatch (POST /api/dl/call, GET /api/dl/capabilities) 테스트.

unit:
    - capability catalogue 가 5 L2 엔진 + Company + Story 포함
    - 잘못된 apiRef → 400
    - private (_internal) → 400
    - missing apiRef → 422 (pydantic) 또는 400

integration:
    - Company.panel 실제 호출 (데이터 있을 때만)
"""

from __future__ import annotations

import math

import polars as pl
import pytest

starlette = pytest.importorskip("starlette", reason="starlette not installed (optional [ai] dependency)")
from starlette.testclient import TestClient  # noqa: E402

from dartlab.dataHub.contracts import AssetRef, Coverage, DataPartition, DataResult  # noqa: E402
from dartlab.server import app  # noqa: E402

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestDlCapabilities:
    """GET /api/dl/capabilities — registry catalogue."""

    def test_returns_count_and_items(self, client):
        resp = client.get("/api/dl/capabilities")
        assert resp.status_code == 200
        body = resp.json()
        assert "count" in body and "items" in body
        assert body["count"] > 0
        assert isinstance(body["items"], list)
        assert all("apiRef" in item for item in body["items"])

    def test_contains_company_panel(self, client):
        resp = client.get("/api/dl/capabilities")
        refs = {item["apiRef"] for item in resp.json()["items"]}
        assert "Company.panel" in refs
        assert "Company" in refs

    def test_contains_l2_engines(self, client):
        resp = client.get("/api/dl/capabilities")
        refs = {item["apiRef"] for item in resp.json()["items"]}
        # L2 5 engines + L3 Story 가 catalogue 에 존재
        for engine in ("analysis", "quant", "credit", "macro", "industry"):
            assert engine in refs, f"engine missing from catalogue: {engine}"
        assert "data" in refs

    def test_data_workbench_catalog_is_callable_through_master_api(self, client):
        """외부 HTTP 진입점 하나로 Data Workbench catalog를 실제 호출한다."""

        resp = client.post(
            "/api/dl/call",
            json={
                "apiRef": "data",
                "args": ["catalog"],
                "kwargs": {"query": {"search": "edgarFinancialFeatures"}},
            },
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["apiRef"] == "data"
        assert [asset["assetId"] for asset in body["data"]["assets"]] == ["analysis.edgarFinancialFeatures"]

    def test_data_workbench_factor_query_is_callable_through_master_api(
        self,
        client,
        monkeypatch,
    ):
        """외부 HTTP 호출이 JSON query를 실제 factor projection까지 전달한다."""

        import dartlab

        monkeypatch.setattr(
            dartlab,
            "scan",
            lambda *args, **kwargs: pl.DataFrame(
                {
                    "종목코드": ["005930"],
                    "종목명": ["삼성전자"],
                    "2025": [12.0],
                }
            ),
        )
        resp = client.post(
            "/api/dl/call",
            json={
                "apiRef": "data",
                "args": ["query", "scan.ratio"],
                "kwargs": {
                    "query": {
                        "projection": {
                            "kind": "factor",
                            "measures": ["roe"],
                            "unit": "percent",
                            "frequency": "Y",
                        }
                    }
                },
            },
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["data"]["status"] == "ok"
        partition = body["data"]["partitions"][0]
        assert partition["projectionKind"] == "factor"
        assert partition["data"]["rows"][0]["measureId"] == "roe"


class TestDlCallValidation:
    """POST /api/dl/call — validation/whitelist."""

    def test_unknown_api_ref_400(self, client):
        resp = client.post(
            "/api/dl/call",
            json={"apiRef": "Company.thisDoesNotExist"},
        )
        assert resp.status_code == 400
        detail = resp.json().get("detail", {})
        assert detail.get("error") == "unknown_api_ref"

    def test_private_api_blocked_400(self, client):
        resp = client.post(
            "/api/dl/call",
            json={"apiRef": "_internalThing"},
        )
        assert resp.status_code == 400
        detail = resp.json().get("detail", {})
        assert detail.get("error") in {"private_api_blocked", "unknown_api_ref"}

    def test_missing_api_ref_returns_error(self, client):
        # pydantic 가 빈 apiRef 를 막거나 (422), engineCall 이 missing_api_ref 로 처리 (400)
        resp = client.post("/api/dl/call", json={})
        assert resp.status_code in {400, 422}

    def test_retired_company_show_is_unknown_not_aliased(self, client):
        """공개 show 은퇴 회귀 가드 — Company.show 를 panel 로 조용히 재작성하지 않고

        unknown_api_ref 로 명시 거절한다 (silent back-compat alias 부활 차단).
        """
        resp = client.post("/api/dl/call", json={"apiRef": "Company.show"})
        assert resp.status_code == 400
        detail = resp.json().get("detail", {})
        assert detail.get("error") == "unknown_api_ref"

    def test_capability_exists_but_no_target_returns_meaningful_error(self, client):
        """Company.panel 은 target 필요 — 빈 target 이면 graceful 실패."""
        resp = client.post(
            "/api/dl/call",
            json={"apiRef": "Company.panel"},
        )
        # 200 (어떻게든 처리) 또는 400 (target 필요) — 둘 다 허용. 500 아니면 OK.
        assert resp.status_code != 500


class TestDlStructuredDataResult:
    def test_nested_polars_is_bounded_json_and_keeps_query_continuation(self, client, monkeypatch):
        from dartlab.server.api import dl as dlModule

        values = [float(index) for index in range(205)]
        values[:3] = [math.nan, math.inf, -math.inf]
        asset = AssetRef("scan.ratio", "asset:v1")
        partition = DataPartition(
            asset=asset,
            projectionKind="factor",
            data={
                "frame": pl.DataFrame({"entityId": [f"KR:{index:06d}" for index in range(205)], "value": values}),
                "series": pl.Series("scores", [1.0, math.nan, math.inf]),
            },
            schema=(("frame", "DataFrame"), ("series", "Series")),
            rowCount=205,
            truncated=False,
            selector=(("measure", "roe"),),
            temporalStatus="LATEST_ONLY",
            lineageRefs=("source", "receipt"),
            requestId="factor",
        )
        result = DataResult(
            status="partial",
            partitions=(partition,),
            assets=(asset,),
            snapshotId="data-snapshot:v1",
            contractHash="a" * 64,
            coverage=Coverage(1, 1, 1, 0),
            gaps=(),
            lineageRefs=("source",),
            executionReceipts=("receipt",),
            continuation="opaque-next-page",
            materializationReceipt={
                "generationKey": "b" * 64,
                "terminalRootDigest": "c" * 64,
                "pins": {
                    "assetDigest": "d" * 64,
                    "sourceDigest": "e" * 64,
                    "queryDigest": "f" * 64,
                    "universeDigest": "1" * 64,
                    "contractDigest": "2" * 64,
                    "schemaDigest": "3" * 64,
                },
            },
        )
        monkeypatch.setattr(dlModule, "_dispatch", lambda *_args, **_kwargs: result)

        response = client.post("/api/dl/call", json={"apiRef": "analysis"})

        assert response.status_code == 200
        payload = response.json()["data"]
        partitionPayload = payload["partitions"][0]
        framePayload = partitionPayload["data"]["frame"]
        seriesPayload = partitionPayload["data"]["series"]
        assert payload["continuation"] == "opaque-next-page"
        assert payload["materializationReceipt"] == result.materializationReceipt
        assert partitionPayload["truncated"] is False
        assert framePayload["_type"] == "DataFrame"
        assert framePayload["rowCount"] == 205
        assert framePayload["previewRowCount"] == 200
        assert framePayload["previewTruncated"] is True
        assert [row["value"] for row in framePayload["rows"][:3]] == [None, None, None]
        assert seriesPayload["_type"] == "Series"
        assert seriesPayload["values"] == [1.0, None, None]
