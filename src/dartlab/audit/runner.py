"""AuditRunner — 기업 순회 + 전체 분석 + 저장."""

from __future__ import annotations

import gc
import logging
import time
from datetime import date
from typing import Any

from dartlab.audit.serializer import serializeCalcResult, toJsonStr
from dartlab.audit.store import AuditStore

logger = logging.getLogger("dartlab.audit")

# ── 15축 목록 (analysis/__init__.py와 동기) ──

ALL_AXES: tuple[str, ...] = (
    "수익구조",
    "자금조달",
    "자산구조",
    "현금흐름",
    "수익성",
    "성장성",
    "안정성",
    "효율성",
    "종합평가",
    "이익품질",
    "비용구조",
    "자본배분",
    "투자효율",
    "재무정합성",
    "가치평가",
)

# ── 추가 분석 기능 (axis 외) ──

_EXTRA_BLOCKS = (
    ("insights", "grades"),
    ("insights", "anomalies"),
    ("insights", "profile"),
    ("insights", "summary"),
    ("valuation", "composite"),
    ("forecast", "predicted"),
    ("ratios", "ratioTable"),
)


def _safeGetAttr(obj: Any, attr: str) -> Any:
    """AttributeError 안전 접근."""
    try:
        return getattr(obj, attr)
    except (AttributeError, TypeError, ValueError, KeyError):
        return None


class AuditRunner:
    """단일/다수 기업 감사 실행기."""

    def __init__(self, store: AuditStore | None = None):
        self._store = store or AuditStore()

    def auditOne(self, stockCode: str, *, runDate: str = "") -> dict[str, Any]:
        """단일 기업 전체 분석 + 저장."""
        from dartlab.company import Company

        if not runDate:
            runDate = date.today().isoformat()

        t0 = time.time()
        logger.info("[audit] %s 시작", stockCode)

        c = Company(stockCode)
        corpName = getattr(c, "corpName", "") or ""
        sector = ""
        try:
            sectorObj = getattr(c, "sector", None)
            if sectorObj is not None:
                sector = str(getattr(sectorObj, "sector", "") or "")
        except (AttributeError, TypeError):
            pass

        engineVersion = ""
        try:
            from dartlab import __version__

            engineVersion = __version__
        except ImportError:
            pass

        rows: list[dict[str, Any]] = []
        issues: list[dict[str, Any]] = []

        # ── 1. 15축 analysis ──
        for axis in ALL_AXES:
            axisT0 = time.time()
            try:
                result = c.analysis(axis)
            except (TypeError, ValueError, KeyError, AttributeError, ArithmeticError) as e:
                result = None
                issues.append(
                    {
                        "category": "calcError",
                        "severity": "critical",
                        "axis": axis,
                        "blockKey": "",
                        "description": f"analysis('{axis}') 실행 실패: {e}",
                    }
                )

            if isinstance(result, dict):
                for blockKey, val in result.items():
                    dMs = int((time.time() - axisT0) * 1000)
                    ser = serializeCalcResult(blockKey, val)
                    rows.append(
                        {
                            "axis": axis,
                            "blockKey": ser["blockKey"],
                            "status": ser["status"],
                            "resultJson": ser["resultJson"],
                            "durationMs": dMs,
                        }
                    )
                    if ser["status"] == "none":
                        issues.append(
                            {
                                "category": "dataMissing",
                                "severity": "warning",
                                "axis": axis,
                                "blockKey": blockKey,
                                "description": f"{axis}/{blockKey} 결과 None",
                            }
                        )
            elif result is None:
                rows.append(
                    {
                        "axis": axis,
                        "blockKey": "",
                        "status": "error",
                        "resultJson": "null",
                        "durationMs": int((time.time() - axisT0) * 1000),
                    }
                )

        # ── 2. insights ──
        try:
            insights = c.insights
            if insights is not None:
                for attr in ("grades", "anomalies", "profile", "summary"):
                    val = _safeGetAttr(insights, attr)
                    ser = serializeCalcResult(attr, val)
                    rows.append(
                        {
                            "axis": "insights",
                            "blockKey": ser["blockKey"],
                            "status": ser["status"],
                            "resultJson": ser["resultJson"],
                            "durationMs": 0,
                        }
                    )
            else:
                rows.append(
                    {
                        "axis": "insights",
                        "blockKey": "",
                        "status": "none",
                        "resultJson": "null",
                        "durationMs": 0,
                    }
                )
        except (TypeError, ValueError, KeyError, AttributeError) as e:
            issues.append(
                {
                    "category": "calcError",
                    "severity": "warning",
                    "axis": "insights",
                    "blockKey": "",
                    "description": f"insights 실패: {e}",
                }
            )

        # ── 3. valuation() (별도 호출 — analysis 가치평가 축과 별개로 통합 결과) ──
        try:
            valResult = c.valuation()
            if valResult is not None:
                ser = serializeCalcResult("valuationResult", valResult)
                rows.append(
                    {
                        "axis": "valuation",
                        "blockKey": "valuationResult",
                        "status": ser["status"],
                        "resultJson": ser["resultJson"],
                        "durationMs": 0,
                    }
                )
        except (TypeError, ValueError, KeyError, AttributeError) as e:
            issues.append(
                {
                    "category": "calcError",
                    "severity": "warning",
                    "axis": "valuation",
                    "blockKey": "valuationResult",
                    "description": f"valuation() 실패: {e}",
                }
            )

        # ── 4. forecast() ──
        try:
            fcResult = c.forecast()
            if fcResult is not None:
                ser = serializeCalcResult("forecastResult", fcResult)
                rows.append(
                    {
                        "axis": "forecast",
                        "blockKey": "forecastResult",
                        "status": ser["status"],
                        "resultJson": ser["resultJson"],
                        "durationMs": 0,
                    }
                )
        except (TypeError, ValueError, KeyError, AttributeError) as e:
            issues.append(
                {
                    "category": "calcError",
                    "severity": "warning",
                    "axis": "forecast",
                    "blockKey": "forecastResult",
                    "description": f"forecast() 실패: {e}",
                }
            )

        # ── 5. ratios ──
        try:
            ratios = c.ratios
            if ratios is not None:
                ser = serializeCalcResult("ratioTable", ratios)
                rows.append(
                    {
                        "axis": "ratios",
                        "blockKey": "ratioTable",
                        "status": ser["status"],
                        "resultJson": ser["resultJson"],
                        "durationMs": 0,
                    }
                )
        except (TypeError, ValueError, KeyError, AttributeError) as e:
            issues.append(
                {
                    "category": "calcError",
                    "severity": "warning",
                    "axis": "ratios",
                    "blockKey": "ratioTable",
                    "description": f"ratios 실패: {e}",
                }
            )

        # ── 6. review ──
        reviewJson = ""
        try:
            review = c.review()
            if review is not None:
                reviewJson = review.toJson()
        except (TypeError, ValueError, KeyError, AttributeError) as e:
            issues.append(
                {
                    "category": "calcError",
                    "severity": "warning",
                    "axis": "review",
                    "blockKey": "",
                    "description": f"review() 실패: {e}",
                }
            )

        # ── 집계 ──
        totalCalcs = len(rows)
        okCalcs = sum(1 for r in rows if r.get("status") == "ok")
        durationSec = time.time() - t0

        # ── 저장 ──
        self._store.saveParquet(
            stockCode=stockCode,
            corpName=corpName,
            runDate=runDate,
            rows=rows,
        )
        if reviewJson:
            self._store.saveReviewJson(
                stockCode=stockCode,
                runDate=runDate,
                reviewJson=reviewJson,
            )
        runId = self._store.saveRun(
            stockCode=stockCode,
            corpName=corpName,
            sector=sector,
            runDate=runDate,
            engineVersion=engineVersion,
            totalCalcs=totalCalcs,
            okCalcs=okCalcs,
            durationSec=durationSec,
        )
        if issues:
            self._store.saveIssues(runId, issues)

        logger.info(
            "[audit] %s 완료 — %d/%d ok (%.1fs)",
            stockCode,
            okCalcs,
            totalCalcs,
            durationSec,
        )

        # ── 메모리 해제 (필수) ──
        del c
        gc.collect()

        return {
            "stockCode": stockCode,
            "corpName": corpName,
            "runId": runId,
            "totalCalcs": totalCalcs,
            "okCalcs": okCalcs,
            "coverageRate": okCalcs / totalCalcs if totalCalcs > 0 else 0.0,
            "durationSec": round(durationSec, 1),
            "issueCount": len(issues),
        }

    def auditBatch(
        self,
        codes: list[str] | None = None,
        *,
        resume: bool = False,
        runDate: str = "",
        onProgress: Any = None,
    ) -> list[dict[str, Any]]:
        """다수 기업 순차 감사.

        Args:
            codes: 종목코드 리스트. None이면 전 기업 (getKindList).
            resume: True면 오늘 날짜 기준 미완료분만.
            runDate: 감사 날짜 (기본 오늘).
            onProgress: 콜백 (stockCode, idx, total, result) -> None.
        """
        if not runDate:
            runDate = date.today().isoformat()

        if codes is None:
            from dartlab.gather.listing import getKindList

            kindDf = getKindList()
            codes = kindDf["종목코드"].to_list()

        if resume:
            done = self._store.completedCodes(runDate)
            codes = [c for c in codes if c not in done]
            logger.info("[audit] resume: %d개 미완료 기업", len(codes))

        results = []
        total = len(codes)
        for idx, stockCode in enumerate(codes):
            try:
                result = self.auditOne(stockCode, runDate=runDate)
                results.append(result)
            except (OSError, RuntimeError, ValueError) as e:
                logger.error("[audit] %s 치명적 오류: %s", stockCode, e)
                results.append(
                    {
                        "stockCode": stockCode,
                        "corpName": "",
                        "runId": -1,
                        "totalCalcs": 0,
                        "okCalcs": 0,
                        "coverageRate": 0.0,
                        "durationSec": 0.0,
                        "issueCount": 0,
                        "error": str(e),
                    }
                )
                gc.collect()

            if onProgress:
                try:
                    onProgress(stockCode, idx + 1, total, results[-1])
                except (TypeError, ValueError):
                    pass

        return results
