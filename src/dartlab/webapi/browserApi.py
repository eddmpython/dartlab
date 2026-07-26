"""브라우저 서빙용 async 데이터 라우터 (browser-as-server SSOT).

dartlab 의 공개 계약(engine)만 HTTP 로 노출한다. 새 계약을 만들지 않는다. 모든 엔드포인트는
`async def` 다. sync `def` 는 Starlette 가 스레드풀로 돌려 pyodide 에서 `can't start new thread`
로 죽기 때문이다(실측). dartlab 호출 자체는 동기라 async 함수 안에서 직접 부른다(그 함수가
이벤트 루프에서 돌아 스레드를 안 쓴다).

계약 URL 은 :8400 서버(`/api/company/{code}/...`)와 형태를 맞춘다(prefix 는 배송 계층이 붙인다).
Service Worker 가 `/pyapi/*` 를 이 앱으로 넘기며 `/pyapi` 를 떼고 dispatch 한다.

Capabilities:
    브라우저에서 도는 dartlab 공개 계약(panel/select/analysis/scan/credit/story/industry/trace)을
    FastAPI 라우트로 노출. 각 라우트는 dartlab 을 직접 호출하고 결과를 JSON 안전 형태로 직렬화.

AIContext:
    browser-as-server 의 데이터 SSOT. 노트북 execute 커널과 같은 pyodide 인터프리터에서 마운트.

Guide:
    `app = buildBrowserApi()` 로 FastAPI 앱을 얻어 ASGI 로 호출한다. fastapi 는 이 함수 안에서만
    import 하므로 wheel(fastapi 제외) import 시점엔 필요 없다.

When:
    브라우저 pyodide 워커가 첫 `/pyapi` 요청을 받을 때 한 번 build.

How:
    dartlab.Company / dartlab.scan 공개 진입점을 async 라우트에서 호출, `_json` 으로 직렬화.

Requires:
    런타임에 fastapi(순수휠) + pydantic-core(pyodide lockfile). dartlab 은 이미 로드됨.

SeeAlso:
    mainPlan/browser-as-server-ssot/01-architecture.md, dartlab.server(:8400, sync 별개).
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

_ROW_CAP = 500  # 브라우저 페이로드 상한. 넘으면 잘라 보내고 truncated 표기.


def _json(obj: Any) -> Any:
    """dartlab 결과(polars DataFrame/Panel/dict/스칼라)를 JSON 안전 형태로."""
    if obj is None:
        return None
    if type(obj) in {str, bool, int, float}:
        return obj
    # polars DataFrame / dartlab Panel (둘 다 columns·height·to_dicts 를 가짐)
    to_dicts = getattr(obj, "to_dicts", None)
    columns = getattr(obj, "columns", None)
    height = getattr(obj, "height", None)
    if callable(to_dicts) and columns is not None:
        rows = obj.head(_ROW_CAP).to_dicts() if height and height > _ROW_CAP else obj.to_dicts()
        return {
            "columns": list(columns),
            "shape": list(getattr(obj, "shape", (len(rows), len(columns)))),
            "rows": rows,
            "truncated": bool(height and height > _ROW_CAP),
        }
    if is_dataclass(obj) and not isinstance(obj, type):
        return {field.name: _json(getattr(obj, field.name)) for field in fields(obj)}
    if isinstance(obj, dict):
        return {str(key): _json(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json(value) for value in obj]
    # SelectResult 등 .df 를 가진 래퍼
    df = getattr(obj, "df", None)
    if df is not None and df is not obj:
        return _json(df)
    return {"repr": str(obj)[:2000]}


def buildBrowserApi():  # noqa: C901
    """브라우저 서빙 FastAPI 앱. fastapi 는 여기서만 lazy import(wheel 은 fastapi 제외)."""
    from fastapi import FastAPI

    import dartlab

    app = FastAPI(title="dartlab browser", version=getattr(dartlab, "__version__", "0"))

    @app.get("/health")
    async def health() -> dict:
        """살아있는지 + 버전. 커널·서버 기동 확인용."""
        return {"ok": True, "version": getattr(dartlab, "__version__", "0")}

    @app.get("/company/{code}/panel/{topic}")
    async def panel(code: str, topic: str, freq: str | None = None, scope: str | None = None) -> dict:
        """항목 x 기간 격자(panel)를 topic(IS/BS/CF/섹션명)으로. freq·scope 는 선택."""
        kwargs = {}
        if freq:
            kwargs["freq"] = freq
        if scope:
            kwargs["scope"] = scope
        return _json(dartlab.Company(code).panel(topic, **kwargs))

    @app.get("/company/{code}/select/{topic}")
    async def select(code: str, topic: str, fields: str, freq: str | None = None) -> dict:
        """격자에서 원하는 계정만 이름(fields=쉼표구분)으로 골라낸다."""
        names = [f for f in fields.split(",") if f.strip()]
        kwargs = {"freq": freq} if freq else {}
        return _json(dartlab.Company(code).select(topic, names, **kwargs))

    @app.get("/company/{code}/analysis/{engine}/{axis}")
    async def analysis(code: str, engine: str, axis: str) -> Any:
        """analysis 엔진의 한 축(예 financial/수익성)을 자동 계산으로 읽는다."""
        return _json(dartlab.Company(code).analysis(engine, axis))

    @app.get("/company/{code}/credit/{axis}")
    async def credit(code: str, axis: str) -> Any:
        """신용 위험 한 축(등급·채무상환 등). 인자는 라벨 접두사."""
        return _json(dartlab.Company(code).credit(axis))

    @app.get("/company/{code}/story/{section}")
    async def story(code: str, section: str) -> Any:
        """사람이 읽는 문장 리포트의 한 섹션(한글 섹션 키)."""
        result = dartlab.Company(code).story(section)
        render = getattr(result, "render", None)
        return {"section": section, "text": render() if callable(render) else str(result)[:8000]}

    @app.get("/company/{code}/industry")
    async def industry(code: str) -> Any:
        """산업 위치(업종·공정 단계·동종사)."""
        return _json(dartlab.Company(code).industry())

    @app.get("/company/{code}/lenses")
    async def lenses(code: str) -> Any:
        """다섯 대표 렌즈의 product bundle. 브라우저는 의미를 재구현하지 않는다."""
        from dartlab.story.lensProducts import collectLensProducts, publicLensBundle

        return publicLensBundle(collectLensProducts(dartlab.Company(code)))

    @app.get("/company/{code}/trace/{topic}")
    async def trace(code: str, topic: str) -> Any:
        """이 topic 데이터가 어느 출처에서 왔는지 되짚는다."""
        return _json(dartlab.Company(code).trace(topic))

    @app.get("/scan/{axis}")
    async def scan(axis: str) -> dict:
        """전상장사 횡단분석 한 축(growth·profitability 등)을 한 표로."""
        return _json(dartlab.scan(axis))

    return app
