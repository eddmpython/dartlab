"""데이터 소스, 미리보기, 통계, Excel 내보내기 엔드포인트."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from dartlab.company import Company


def _packageVersion() -> str:
    """설치된 dartlab 버전. facade 를 거치지 않고 패키지 메타데이터에서 직접 읽는다."""

    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("dartlab")
    except PackageNotFoundError:
        return "0.0.0"


from .common import (
    HANDLED_API_ERRORS,
    guideDetail,
    serializePayload,
)

router = APIRouter()


# ── Data Sources ──


@router.get("/api/data/sources/{code}")
async def apiDataSources(code: str):
    """경량 데이터 소스 목록 — registry 메타 + 파일 존재 여부만 확인 (빠름)."""
    try:
        c = await asyncio.to_thread(Company, code)
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))

    from dartlab.core.registry import getEntries

    hasFlags = {
        "finance": c._hasFinance,
        "panel": c._hasPanel,
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
async def apiDataPreview(
    code: str,
    module: str,
    maxRows: int = Query(50, ge=1, le=500, alias="max_rows"),
    maxRowsCompat: int | None = Query(None, ge=1, le=500, alias="maxRows"),
):
    """데이터 미리보기 — 모듈 데이터를 JSON으로 반환 (테이블/텍스트)."""
    rowLimit = maxRowsCompat if maxRowsCompat is not None and maxRows == 50 else maxRows
    try:
        c = await asyncio.to_thread(Company, code)
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))

    from dartlab.core.registry import getEntry

    entry = getEntry(module)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"모듈 '{module}'을 찾을 수 없습니다")

    import polars as pl

    try:
        data = await asyncio.to_thread(_resolveModuleData, c, entry)
    except (AttributeError, ValueError, OSError, KeyError, TypeError) as e:
        raise HTTPException(status_code=404, detail=f"데이터를 가져올 수 없습니다: {e}")

    if data is None:
        raise HTTPException(status_code=404, detail="데이터가 없습니다")

    if isinstance(data, pl.DataFrame):
        if "year" in data.columns:
            data = data.sort("year")
        serialized = serializePayload(data, maxRows=rowLimit)
        result: dict[str, Any] = {
            **serialized,
            "module": module,
            "label": entry.label,
            "unit": entry.unit,
        }
        financeMeta = _buildFinanceMeta(module)
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
def apiDataStats():
    """로컬 데이터 현황 — panel/재무 파일 수, dartlab 버전."""
    from dartlab.core.dataLoader import _dataDir

    stats: dict[str, Any] = {
        "version": _packageVersion(),
    }
    for category in ("panel", "finance"):
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
def apiSpec():
    """시스템 스펙 조회 — LLM/MCP/외부 클라이언트용 (deprecated)."""
    raise HTTPException(
        status_code=501,
        detail="스펙 조회 API는 현재 사용할 수 없습니다 (ai.spec 모듈 제거됨)",
    )


# ── Export ──


@router.get("/api/export/modules/{code}")
async def apiExportModules(code: str):
    """Excel 내보내기 가능한 모듈 목록."""
    try:
        c = await asyncio.to_thread(Company, code)
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))

    from dartlab.viz.export.excel import listAvailableModules

    modules = await asyncio.to_thread(listAvailableModules, c)
    return {
        "stockCode": c.stockCode,
        "corpName": c.corpName,
        "modules": modules,
    }


@router.get("/api/export/sources/{code}")
async def apiExportSources(code: str):
    """데이터 소스 디스커버리 — registry 기반 전체 소스 트리."""
    try:
        c = await asyncio.to_thread(Company, code)
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))

    from dartlab.viz.export.sources import discoverSources

    tree = await asyncio.to_thread(discoverSources, c)
    return tree.toDict()


@router.get("/api/export/templates")
def apiExportTemplates():
    """저장된 템플릿 목록 (프리셋 포함)."""
    from dartlab.viz.export.store import TemplateStore

    store = TemplateStore()
    templates = store.list()
    return {
        "templates": [t.toDict() for t in templates],
    }


@router.get("/api/export/templates/{template_id}")
def apiExportTemplateGet(template_id: str):
    """단일 템플릿 조회."""
    from dartlab.viz.export.store import TemplateStore

    store = TemplateStore()
    t = store.get(template_id)
    if t is None:
        raise HTTPException(status_code=404, detail=f"템플릿 '{template_id}'을 찾을 수 없습니다")
    return t.toDict()


@router.post("/api/export/templates")
def apiExportTemplateSave(req: dict):
    """템플릿 저장 (신규 or 업데이트)."""
    from dartlab.viz.export.store import TemplateStore
    from dartlab.viz.export.template import ExcelTemplate

    store = TemplateStore()
    t = ExcelTemplate.fromDict(req)
    tid = store.save(t)
    return {"ok": True, "templateId": tid}


@router.delete("/api/export/templates/{template_id}")
def apiExportTemplateDelete(template_id: str):
    """템플릿 삭제."""
    from dartlab.viz.export.store import TemplateStore

    store = TemplateStore()
    deleted = store.delete(template_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="프리셋 템플릿은 삭제할 수 없습니다")
    return {"ok": True}


@router.get("/api/export/excel/{code}")
async def apiExportExcel(
    code: str,
    modules: str | None = Query(None, description="쉼표 구분 모듈: IS,BS,CF,ratios,dividend,employee"),
    templateId: str | None = Query(None, description="템플릿 ID (preset_full, preset_summary 등)"),
):
    """Excel 파일 내보내기 — .xlsx 다운로드."""
    import tempfile

    try:
        c = await asyncio.to_thread(Company, code)
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))

    tmpDir = Path(tempfile.gettempdir())
    safeName = c.corpName.replace("/", "_").replace("\\", "_")

    if templateId:
        from dartlab.viz.export.excel import exportWithTemplate
        from dartlab.viz.export.store import TemplateStore

        store = TemplateStore()
        tmpl = store.get(templateId)
        if tmpl is None:
            raise HTTPException(status_code=404, detail=f"템플릿 '{templateId}'을 찾을 수 없습니다")
        templateSafe = tmpl.name.replace("/", "_").replace("\\", "_")
        outPath = tmpDir / f"{c.stockCode}_{safeName}_{templateSafe}.xlsx"
        try:
            await asyncio.to_thread(exportWithTemplate, c, tmpl, outPath)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=guideDetail(e))
        return FileResponse(
            path=str(outPath),
            filename=f"{c.stockCode}_{safeName}_{templateSafe}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    modList = [m.strip() for m in modules.split(",")] if modules else None
    outPath = tmpDir / f"{c.stockCode}_{safeName}.xlsx"

    try:
        from dartlab.viz.export.excel import exportToExcel

        await asyncio.to_thread(exportToExcel, c, outputPath=outPath, modules=modList)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=guideDetail(e))

    return FileResponse(
        path=str(outPath),
        filename=f"{c.stockCode}_{safeName}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


_XLSX_MEDIA = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.post("/api/export/excel")
async def apiExportExcelSelection(req: dict):
    """선택(selection) → 임시 ExcelTemplate → .xlsx 다운로드 (저장 없이).

    뷰어가 고른 시트/공시 표 selection 을 임시 양식으로 받아 즉시 .xlsx 생성. ``templateId``
    없이 selection→``ExcelTemplate`` 직변환 — store 에 저장하지 않는다. source 는 문자열
    (ModuleSource 정규화) 또는 ``{"kind":"panelTable", ...}`` dict 둘 다 허용 (fromDict 흡수).

    요청 본문::

        {"code": "005930",
         "template": {"name": "선택", "sheets": [{"source": "IS"},
                      {"source": {"kind": "panelTable", "chapter": "...", ...}}]}}
    """
    import tempfile

    from dartlab.viz.export.excel import exportWithTemplate
    from dartlab.viz.export.template import ExcelTemplate

    code = str(req.get("code") or "").strip()
    templateReq = req.get("template")
    if not code or not isinstance(templateReq, dict):
        raise HTTPException(status_code=400, detail="code 와 template(dict) 이 필요합니다")

    try:
        tmpl = ExcelTemplate.fromDict(templateReq)
    except (KeyError, TypeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"template 형식 오류: {e}")

    try:
        c = await asyncio.to_thread(Company, code)
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))

    tmpDir = Path(tempfile.gettempdir())
    safeName = c.corpName.replace("/", "_").replace("\\", "_")
    templateSafe = tmpl.name.replace("/", "_").replace("\\", "_")
    outPath = tmpDir / f"{c.stockCode}_{safeName}_{templateSafe}.xlsx"
    try:
        await asyncio.to_thread(exportWithTemplate, c, tmpl, outPath)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=guideDetail(e))
    finally:
        del c
    return FileResponse(
        path=str(outPath),
        filename=f"{outPath.name}",
        media_type=_XLSX_MEDIA,
    )


def _batchExportToZip(codes: list[str], templateDict: dict, zipPath: Path) -> tuple[int, list[str]]:
    """codes → 회사당 개별 .xlsx → ZIP (순차, 회사당 ``del c`` flush). OOM 규율 (01 §6).

    한 워크북에 N사 누적 금지 (openpyxl 전사 메모리 = Rust 힙 OOM). 회사당 개별 워크북 →
    즉시 임시 .xlsx flush → ZIP 에 디스크 레벨 추가 → ``del c``. 실패 회사는 skip + 기록.

    Args:
        codes: 종목코드 리스트.
        templateDict: ExcelTemplate.fromDict 입력 (selection 또는 저장 양식 dict).
        zipPath: 결과 ZIP 경로.

    Returns:
        ``(성공 회사 수, 실패 코드 리스트)``.

    Example:
        >>> n, failed = _batchExportToZip(["005930"], {"name": "x", "sheets": [{"source": "IS"}]}, Path("/tmp/o.zip"))  # doctest: +SKIP

    Raises:
        없음 — 회사별 실패는 흡수(skip), 전체 0 성공이어도 빈 ZIP 반환.
    """
    import tempfile
    import zipfile

    from dartlab.viz.export.excel import exportWithTemplate
    from dartlab.viz.export.template import ExcelTemplate

    ok = 0
    failed: list[str] = []
    with zipfile.ZipFile(str(zipPath), "w", zipfile.ZIP_DEFLATED) as zf:
        for code in codes:
            tmpXlsx = None
            try:
                # with Company → __exit__ 가 다음 회사 전 자동 cleanup (룰 11, OOM 규율).
                with Company(code) as c:
                    tmpl = ExcelTemplate.fromDict(templateDict)
                    safeName = c.corpName.replace("/", "_").replace("\\", "_")
                    tmpXlsx = Path(tempfile.gettempdir()) / f"_batch_{c.stockCode}_{safeName}.xlsx"
                    exportWithTemplate(c, tmpl, tmpXlsx)
                    zf.write(str(tmpXlsx), arcname=f"{c.stockCode}_{safeName}.xlsx")
                    ok += 1
            except (ValueError, OSError, KeyError, TypeError):
                failed.append(code)
            finally:
                if tmpXlsx is not None and tmpXlsx.exists():
                    try:
                        tmpXlsx.unlink()
                    except OSError:
                        pass
    return ok, failed


@router.post("/api/export/excel/batch")
async def apiExportExcelBatch(req: dict):
    """코드 리스트 + 양식 → 회사당 .xlsx → ZIP FileResponse (순차, 동시 ≤2, 회사당 flush).

    회사 간 양식 이식 (00 §3-b). OOM 규율 (01 §6): 회사당 개별 워크북·즉시 flush·``del c``.
    ``asyncio.to_thread`` 로 단일 스레드 직렬화 (동시 ≤2 절대 — 병렬 폭주 = Rust 힙 OOM).

    요청 본문::

        {"codes": ["005930", "000660"],
         "template": {"name": "선택", "sheets": [...]}}   # 또는
        {"codes": [...], "templateId": "preset_summary"}
    """
    import tempfile

    codes = req.get("codes")
    if not isinstance(codes, list) or not codes:
        raise HTTPException(status_code=400, detail="codes(list) 가 필요합니다")
    codes = [str(x).strip() for x in codes if str(x).strip()]
    if not codes:
        raise HTTPException(status_code=400, detail="유효한 code 가 없습니다")
    if len(codes) > 50:
        raise HTTPException(status_code=400, detail="일괄 내보내기는 최대 50개까지 가능합니다")

    templateDict = req.get("template")
    templateId = req.get("templateId")
    if templateDict is None and templateId:
        from dartlab.viz.export.store import TemplateStore

        store = TemplateStore()
        tmpl = store.get(templateId)
        if tmpl is None:
            raise HTTPException(status_code=404, detail=f"템플릿 '{templateId}'을 찾을 수 없습니다")
        templateDict = tmpl.toDict()
    if not isinstance(templateDict, dict):
        raise HTTPException(status_code=400, detail="template(dict) 또는 templateId 가 필요합니다")

    zipPath = Path(tempfile.gettempdir()) / f"_batch_export_{abs(hash(tuple(codes))) & 0xFFFFFF:06x}.zip"
    # 단일 스레드 직렬화 — 회사당 순차 로드/flush (동시 ≤2 보장).
    ok, failed = await asyncio.to_thread(_batchExportToZip, codes, templateDict, zipPath)
    if ok == 0:
        raise HTTPException(status_code=400, detail=f"내보낼 데이터 없음 (실패: {failed})")
    return FileResponse(
        path=str(zipPath),
        filename="dartlab_export.zip",
        media_type="application/zip",
        headers={"X-Export-Ok": str(ok), "X-Export-Failed": ",".join(failed)},
    )


# ── Internal Helpers ──


def _resolveModuleData(c: Company, entry) -> Any:
    """registry entry에서 실제 데이터를 추출한다."""
    import dataclasses
    import enum

    import polars as pl

    name = entry.name

    if name.startswith("annual.") or name.startswith("timeseries."):
        prefix, stmt = name.split(".", 1)
        freq = "Y" if prefix == "annual" else "Q"
        return _resolveFinancePanel(c, stmt, freq=freq)

    if name == "ratios":
        return _resolveFinancePanel(c, "ratios")

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


def _resolveFinancePanel(c: Company, topic: str, *, freq: str | None = None) -> Any:
    """Company.panel finance 표면에서 preview용 데이터를 조회한다."""
    panel = getattr(c, "panel", None)
    if panel is None or not callable(panel):
        return None
    if freq is None:
        return panel(topic)
    return panel(topic, freq=freq)


def _buildFinanceMeta(moduleName: str) -> dict[str, Any]:
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
