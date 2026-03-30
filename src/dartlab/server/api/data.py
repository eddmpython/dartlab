"""데이터 소스, 미리보기, 통계, Excel 내보내기 엔드포인트."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

import dartlab
from dartlab import Company

from .common import (
    HANDLED_API_ERRORS,
    sanitize_error,
    serialize_payload,
)

router = APIRouter()


# ── Data Sources ──


@router.get("/api/data/sources/{code}")
async def api_data_sources(code: str):
    """경량 데이터 소스 목록 — registry 메타 + 파일 존재 여부만 확인 (빠름)."""
    try:
        c = await asyncio.to_thread(Company, code)
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=404, detail=sanitize_error(e))

    from dartlab.core.registry import getEntries

    hasFlags = {
        "finance": c._hasFinance,
        "docs": c._hasDocs,
        "report": c._hasReport,
    }

    categoryOrder = ["finance", "report", "disclosure", "notes", "analysis", "raw"]
    categories: dict[str, list[dict]] = {}
    totalAvailable = 0

    for entry in getEntries():
        req = entry.requires or ""
        if req:
            available = hasFlags.get(req, False)
        else:
            available = True

        item = {
            "name": entry.name,
            "label": entry.label,
            "dataType": entry.dataType,
            "description": entry.description,
            "available": available,
        }
        categories.setdefault(entry.category, []).append(item)
        if available:
            totalAvailable += 1

    ordered: dict[str, list[dict]] = {}
    for cat in categoryOrder:
        if cat in categories:
            ordered[cat] = categories[cat]
    for cat in categories:
        if cat not in ordered:
            ordered[cat] = categories[cat]

    totalSources = sum(len(v) for v in ordered.values())

    return {
        "stockCode": c.stockCode,
        "corpName": c.corpName,
        "totalSources": totalSources,
        "availableSources": totalAvailable,
        "categories": ordered,
    }


@router.get("/api/data/preview/{code}/{module}")
async def api_data_preview(code: str, module: str, max_rows: int = Query(50, ge=1, le=500)):
    """데이터 미리보기 — 모듈 데이터를 JSON으로 반환 (테이블/텍스트)."""
    try:
        c = await asyncio.to_thread(Company, code)
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=404, detail=sanitize_error(e))

    from dartlab.core.registry import getEntry

    entry = getEntry(module)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"모듈 '{module}'을 찾을 수 없습니다")

    import polars as pl

    try:
        data = await asyncio.to_thread(_resolve_module_data, c, entry)
    except (AttributeError, ValueError, OSError, KeyError, TypeError) as e:
        raise HTTPException(status_code=404, detail=f"데이터를 가져올 수 없습니다: {e}")

    if data is None:
        raise HTTPException(status_code=404, detail="데이터가 없습니다")

    if isinstance(data, pl.DataFrame):
        if "year" in data.columns:
            data = data.sort("year")
        serialized = serialize_payload(data, max_rows=max_rows)
        result: dict[str, Any] = {
            **serialized,
            "module": module,
            "label": entry.label,
            "unit": entry.unit,
        }
        financeMeta = _build_finance_meta(module)
        if financeMeta:
            result["meta"] = financeMeta
        return result

    if isinstance(data, dict):
        flat: dict[str, Any] = {}
        for k, v in data.items():
            if isinstance(v, __import__("polars").DataFrame):
                continue
            if isinstance(v, list) and v and isinstance(v[0], dict):
                flat[k] = json.dumps(v, ensure_ascii=False, default=str)
            elif isinstance(v, dict):
                flat[k] = json.dumps(v, ensure_ascii=False, default=str)
            elif isinstance(v, (str, int, float, bool, type(None))):
                flat[k] = v
            else:
                flat[k] = str(v)
        return {
            "type": "dict",
            "module": module,
            "label": entry.label,
            "unit": entry.unit,
            "data": flat,
        }

    if isinstance(data, str):
        truncated = len(data) > 5000
        return {
            "type": "text",
            "module": module,
            "label": entry.label,
            "text": data[:5000] if truncated else data,
            "truncated": truncated,
        }

    return {
        "type": "unknown",
        "module": module,
        "label": entry.label,
        "data": str(data)[:2000],
    }


@router.get("/api/data/stats")
def api_data_stats():
    """로컬 데이터 현황 — 문서/재무 파일 수, dartlab 버전."""
    from dartlab.core.dataLoader import _dataDir

    stats: dict[str, Any] = {
        "version": dartlab.__version__ if hasattr(dartlab, "__version__") else "unknown",
    }
    for category in ("docs", "finance"):
        try:
            d = _dataDir(category)
            if d.exists():
                files = list(d.glob("*.parquet"))
                stats[category] = {"count": len(files), "exists": True}
            else:
                stats[category] = {"count": 0, "exists": False}
        except HANDLED_API_ERRORS:
            stats[category] = {"count": 0, "exists": False}
    return stats


@router.get("/api/spec")
def api_spec(engine: str | None = None, section: str | None = None):
    """시스템 스펙 조회 — LLM/MCP/외부 클라이언트용."""
    raise HTTPException(
        status_code=501,
        detail="스펙 조회 API는 현재 사용할 수 없습니다 (ai.spec 모듈 제거됨)",
    )


# ── Export ──


@router.get("/api/export/modules/{code}")
async def api_export_modules(code: str):
    """Excel 내보내기 가능한 모듈 목록."""
    try:
        c = await asyncio.to_thread(Company, code)
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=404, detail=sanitize_error(e))

    from dartlab.export.excel import listAvailableModules

    modules = await asyncio.to_thread(listAvailableModules, c)
    return {
        "stockCode": c.stockCode,
        "corpName": c.corpName,
        "modules": modules,
    }


@router.get("/api/export/sources/{code}")
async def api_export_sources(code: str):
    """데이터 소스 디스커버리 — registry 기반 전체 소스 트리."""
    try:
        c = await asyncio.to_thread(Company, code)
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=404, detail=sanitize_error(e))

    from dartlab.export.sources import discoverSources

    tree = await asyncio.to_thread(discoverSources, c)
    return tree.toDict()


@router.get("/api/export/templates")
def api_export_templates():
    """저장된 템플릿 목록 (프리셋 포함)."""
    from dartlab.export.store import TemplateStore

    store = TemplateStore()
    templates = store.list()
    return {
        "templates": [t.toDict() for t in templates],
    }


@router.get("/api/export/templates/{template_id}")
def api_export_template_get(template_id: str):
    """단일 템플릿 조회."""
    from dartlab.export.store import TemplateStore

    store = TemplateStore()
    t = store.get(template_id)
    if t is None:
        raise HTTPException(status_code=404, detail=f"템플릿 '{template_id}'을 찾을 수 없습니다")
    return t.toDict()


@router.post("/api/export/templates")
def api_export_template_save(req: dict):
    """템플릿 저장 (신규 or 업데이트)."""
    from dartlab.export.store import TemplateStore
    from dartlab.export.template import ExcelTemplate

    store = TemplateStore()
    t = ExcelTemplate.fromDict(req)
    tid = store.save(t)
    return {"ok": True, "templateId": tid}


@router.delete("/api/export/templates/{template_id}")
def api_export_template_delete(template_id: str):
    """템플릿 삭제."""
    from dartlab.export.store import TemplateStore

    store = TemplateStore()
    deleted = store.delete(template_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="프리셋 템플릿은 삭제할 수 없습니다")
    return {"ok": True}


@router.get("/api/export/excel/{code}")
async def api_export_excel(
    code: str,
    modules: str | None = Query(None, description="쉼표 구분 모듈: IS,BS,CF,ratios,dividend,employee"),
    template_id: str | None = Query(None, description="템플릿 ID (preset_full, preset_summary 등)"),
):
    """Excel 파일 내보내기 — .xlsx 다운로드."""
    import tempfile

    try:
        c = await asyncio.to_thread(Company, code)
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=404, detail=sanitize_error(e))

    tmpDir = Path(tempfile.gettempdir())
    safeName = c.corpName.replace("/", "_").replace("\\", "_")

    if template_id:
        from dartlab.export.excel import exportWithTemplate
        from dartlab.export.store import TemplateStore

        store = TemplateStore()
        tmpl = store.get(template_id)
        if tmpl is None:
            raise HTTPException(status_code=404, detail=f"템플릿 '{template_id}'을 찾을 수 없습니다")
        templateSafe = tmpl.name.replace("/", "_").replace("\\", "_")
        outPath = tmpDir / f"{c.stockCode}_{safeName}_{templateSafe}.xlsx"
        try:
            await asyncio.to_thread(exportWithTemplate, c, tmpl, outPath)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=sanitize_error(e))
        return FileResponse(
            path=str(outPath),
            filename=f"{c.stockCode}_{safeName}_{templateSafe}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    modList = [m.strip() for m in modules.split(",")] if modules else None
    outPath = tmpDir / f"{c.stockCode}_{safeName}.xlsx"

    try:
        from dartlab.export.excel import exportToExcel

        await asyncio.to_thread(exportToExcel, c, outputPath=outPath, modules=modList)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=sanitize_error(e))

    return FileResponse(
        path=str(outPath),
        filename=f"{c.stockCode}_{safeName}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ── Internal Helpers ──


def _resolve_module_data(c: Company, entry) -> Any:
    """registry entry에서 실제 데이터를 추출한다."""
    import dataclasses
    import enum

    import polars as pl

    name = entry.name

    if name.startswith("annual.") or name.startswith("timeseries."):
        prefix, stmt = name.split(".", 1)
        prop = "annual" if prefix == "annual" else "timeseries"
        result = getattr(c, prop, None)
        if result is None:
            return None
        series, periods = result
        stmt_data = series.get(stmt)
        if not stmt_data or not periods:
            return None

        from dartlab.providers.dart.finance.mapper import AccountMapper

        order = AccountMapper.get().sortOrder(stmt)

        rows = []
        for account, values in stmt_data.items():
            row = {"계정명": account}
            for i, p in enumerate(periods):
                row[str(p)] = values[i] if i < len(values) else None
            rows.append(row)
        if not rows:
            return None
        if order:
            rows.sort(key=lambda r: order.get(r["계정명"], 9999))
        return pl.DataFrame(rows)

    attrName = entry.funcName or entry.name
    if name in ("IS", "BS", "CF"):
        attrName = name

    data = getattr(c, attrName, None)
    if data is None:
        return None

    if callable(data) and not isinstance(data, (pl.DataFrame, dict, str)):
        data = data()

    if entry.extractor:
        try:
            data = entry.extractor(data)
        except (AttributeError, TypeError):
            pass

    if dataclasses.is_dataclass(data) and not isinstance(data, type):
        data = {k: v for k, v in dataclasses.asdict(data).items() if v is not None}

    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if isinstance(v, enum.Enum):
                cleaned[k] = v.value
            elif isinstance(v, (list, tuple)):
                cleaned[k] = [item.value if isinstance(item, enum.Enum) else item for item in v]
            else:
                cleaned[k] = v
        data = cleaned

    return data


def _build_finance_meta(moduleName: str) -> dict[str, Any]:
    """finance 시계열 모듈의 메타데이터 — 한글 라벨, 정렬, 레벨 정보."""
    if not moduleName.startswith("annual.") and not moduleName.startswith("timeseries."):
        return {}

    _, stmt = moduleName.split(".", 1)
    from dartlab.providers.dart.finance.mapper import AccountMapper

    mapper = AccountMapper.get()
    labels = mapper.labelMap()
    order = mapper.sortOrder(stmt)
    levels = mapper.levelMap(stmt)

    return {
        "labels": labels,
        "sortOrder": order,
        "levels": levels,
        "unit": "원",
        "stmtType": stmt,
    }
