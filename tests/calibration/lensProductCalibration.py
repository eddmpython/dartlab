"""다섯 Lens Product의 실제 기업군 제품 성숙도 검증기.

공개 scan과 industry 결과로 산업, 규모, 수익성, 성장, 부채 분포를 덮는
기업군을 자동 선정한다. 각 기업은 별도 프로세스에서 계산해 Polars heap
누적을 막고, 계약 정합성, 결손 정직성, 렌즈별 유용성, 실행비용을 함께 잰다.

실행 예시::

    python -X utf8 tests/calibration/lensProductCalibration.py \
        --select-only --limit 40 --output C:/tmp/dartlab-lens-calibration
    python -X utf8 tests/calibration/lensProductCalibration.py \
        --cohort C:/tmp/dartlab-lens-calibration/cohort.json \
        --output C:/tmp/dartlab-lens-calibration --jobs 2
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "src"))

_ENGINES = ("analysis", "credit", "industry", "quant", "macro")
_SCAN_FIELDS = {
    "profitability": {
        "operatingMargin": "영업이익률",
        "netMargin": "순이익률",
        "roe": "ROE",
    },
    "growth": {
        "revenueCagr": "매출CAGR",
        "growthYears": "years",
    },
    "debt": {
        "debtRatio": "부채비율",
        "interestCoverage": "ICR",
        "totalDebt": "총부채",
    },
    "valuation": {
        "marketCap": "시가총액",
        "per": "PER",
        "pbr": "PBR",
        "dividendYield": "배당수익률",
    },
}
_EXPECTED_METHODS = {
    "analysis": "requiredDomainCoverage",
    "credit": "validAxisWeightCoverage",
    "industry": "mappingConfidenceAndBlockCoverage",
    "quant": "threeBlockCoverageAndSignalClarity",
    "macro": "macroObservationAndCompanyEvidenceCoverage",
}
_UTILITY_FLOORS = {
    "analysis": 0.90,
    "credit": 0.90,
    "industry": 0.85,
    "quant": 0.80,
    "macro": 0.90,
}
_DECISIVENESS_FLOORS = {
    "analysis": 0.80,
    "credit": 0.70,
    "industry": 0.70,
    "quant": 0.25,
    "macro": 0.30,
}
_PERFORMANCE_LIMITS = {"p95Seconds": 180.0, "peakRssMb": 3072.0}
_WORKER_TIMEOUT_SECONDS = 300.0


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _normalizeCode(value: Any) -> str:
    text = str(value or "").strip()
    return text.zfill(6) if text.isdigit() and len(text) <= 6 else text


def _stableRank(value: str) -> int:
    return int(hashlib.sha256(f"dartlab-lens-calibration-v1:{value}".encode()).hexdigest(), 16)


def _writeJson(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def loadCandidateRows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """공개 scan과 industry SSOT에서 자동 표본 후보를 만든다."""
    import dartlab

    candidates: dict[str, dict[str, Any]] = {}
    snapshots: dict[str, Any] = {}
    for axis, fields in _SCAN_FIELDS.items():
        frame = dartlab.scan(axis)
        if frame is None or frame.is_empty():
            raise RuntimeError(f"scan {axis} 결과가 비었습니다.")
        snapshots[axis] = {"rows": frame.height}
        for source in frame.to_dicts():
            code = _normalizeCode(source.get("종목코드") or source.get("stockCode"))
            if not (len(code) == 6 and code.isdigit()):
                continue
            candidate = candidates.setdefault(
                code,
                {
                    "stockCode": code,
                    "name": "",
                    "scanAxes": [],
                    "metrics": {},
                },
            )
            name = str(source.get("종목명") or source.get("name") or "").strip()
            if name:
                candidate["name"] = name
            candidate["scanAxes"].append(axis)
            for targetKey, sourceKey in fields.items():
                value = _number(source.get(sourceKey))
                if value is not None:
                    candidate["metrics"][targetKey] = value
            if axis == "valuation" and source.get("snapshotAt") is not None:
                snapshots[axis]["snapshotAt"] = str(source["snapshotAt"])

    industryGuide = dartlab.industry()
    snapshots["industry"] = {"rows": industryGuide.height}
    industryNames: dict[str, str] = {}
    industryGaps: list[dict[str, str]] = []
    bestIndustry: dict[str, tuple[float, str]] = {}
    for guideRow in industryGuide.to_dicts():
        industryId = str(guideRow.get("산업ID") or "").strip()
        if not industryId:
            continue
        industryNames[industryId] = str(guideRow.get("산업명") or industryId)
        try:
            members = dartlab.industry(industryId)
        except Exception as exc:  # noqa: BLE001, 선정 결손은 숨기지 않고 원장에 남긴다.
            industryGaps.append({"industryId": industryId, "reason": f"{type(exc).__name__}: {exc}"})
            continue
        for member in members.to_dicts():
            code = _normalizeCode(member.get("종목코드") or member.get("stockCode"))
            if code not in candidates:
                continue
            confidence = _number(member.get("신뢰도") or member.get("confidence")) or 0.0
            current = bestIndustry.get(code)
            choice = (confidence, industryId)
            if current is None or choice[0] > current[0] or (choice[0] == current[0] and choice[1] < current[1]):
                bestIndustry[code] = choice

    rows = []
    for code, candidate in candidates.items():
        industryConfidence, industryId = bestIndustry.get(code, (0.0, "unmapped"))
        candidate["scanAxes"] = sorted(set(candidate["scanAxes"]))
        candidate["scanCoverage"] = len(candidate["scanAxes"])
        candidate["industryId"] = industryId
        candidate["industryName"] = industryNames.get(industryId, "미분류")
        candidate["industryConfidence"] = industryConfidence
        rows.append(candidate)

    snapshots["industry"]["gaps"] = industryGaps
    return sorted(rows, key=lambda row: row["stockCode"]), snapshots


def _metricBands(rows: list[dict[str, Any]]) -> dict[str, list[float]]:
    keys = sorted({key for row in rows for key in row.get("metrics", {})})
    return {
        key: sorted(value for row in rows if (value := _number(row.get("metrics", {}).get(key))) is not None)
        for key in keys
    }


def _band(value: float | None, values: list[float]) -> str:
    if value is None or not values:
        return "missing"
    if len(values) == 1:
        return "q3"
    rank = bisect.bisect_right(values, value) - 1
    quantile = min(4, int((rank / (len(values) - 1)) * 5))
    return f"q{quantile + 1}"


def enrichCandidateTags(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """선정 근거를 산업, 데이터 충족도, 지표 오분위 태그로 고정한다."""
    bands = _metricBands(rows)
    enriched = []
    for row in rows:
        metrics = row.get("metrics", {})
        tags = {
            f"industry:{row.get('industryId') or 'unmapped'}",
            f"scanCoverage:{row.get('scanCoverage', 0)}",
        }
        for key, values in bands.items():
            tags.add(f"band:{key}:{_band(_number(metrics.get(key)), values)}")
        enriched.append({**row, "tags": sorted(tags)})
    return enriched


def selectCohort(rows: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    """가중 set cover로 다양성이 높은 기업군을 재현 가능하게 고른다."""
    if limit < 1:
        raise ValueError("limit은 1 이상이어야 합니다.")
    candidates = enrichCandidateTags(rows)
    if len(candidates) < limit:
        raise ValueError(f"후보 {len(candidates)}개보다 limit {limit}이 큽니다.")

    covered: set[str] = set()
    selected: list[dict[str, Any]] = []
    remaining = {row["stockCode"]: row for row in candidates}

    def tagWeight(tag: str) -> int:
        if tag.startswith("industry:"):
            return 8
        if tag.startswith("scanCoverage:"):
            return 3
        return 1

    while len(selected) < limit:

        def rank(row: dict[str, Any]) -> tuple[int, int, int]:
            gain = sum(tagWeight(tag) for tag in row["tags"] if tag not in covered)
            return gain, int(row.get("scanCoverage") or 0), -_stableRank(row["stockCode"])

        winner = max(remaining.values(), key=rank)
        selected.append(winner)
        covered.update(winner["tags"])
        del remaining[winner["stockCode"]]
    return selected


def buildCohort(*, limit: int) -> dict[str, Any]:
    rows, snapshots = loadCandidateRows()
    selected = selectCohort(rows, limit=limit)
    industryCounts = Counter(row["industryId"] for row in selected)
    return {
        "schemaVersion": 1,
        "selectionMethod": "weightedSetCoverIndustryAndMetricQuintiles",
        "generatedAt": datetime.now().astimezone().isoformat(),
        "candidateCount": len(rows),
        "selectedCount": len(selected),
        "sourceSnapshots": snapshots,
        "distribution": {
            "industryCount": len(industryCounts),
            "industries": dict(sorted(industryCounts.items())),
            "scanCoverage": dict(sorted(Counter(str(row["scanCoverage"]) for row in selected).items())),
        },
        "companies": selected,
    }


def _issue(severity: str, rule: str, message: str, *, engine: str | None = None) -> dict[str, str]:
    row = {"severity": severity, "rule": rule, "message": message}
    if engine is not None:
        row["engine"] = engine
    return row


def _expectedStatus(engine: str, product: dict[str, Any]) -> str | None:
    payload = product.get("payload") if isinstance(product.get("payload"), dict) else {}
    evidence = product.get("evidence") if isinstance(product.get("evidence"), list) else []
    if engine == "analysis":
        coverage = payload.get("coverage") if isinstance(payload.get("coverage"), dict) else {}
        observed = int(coverage.get("observedRequiredDomains") or 0)
        return "blocked" if observed == 0 else "partial" if observed < 4 else "usable"
    if engine == "credit":
        coverage = payload.get("coverage") if isinstance(payload.get("coverage"), dict) else {}
        weight = _number(coverage.get("weightCoverage")) or 0.0
        return "blocked" if not evidence else "partial" if weight < 75 else "usable"
    if engine == "industry":
        coverage = payload.get("coverage") if isinstance(payload.get("coverage"), dict) else {}
        blocks = coverage.get("blocks") if isinstance(coverage.get("blocks"), dict) else {}
        observed = int(coverage.get("observedBlocks") or 0)
        return "blocked" if not blocks.get("position") else "usable" if observed >= 4 else "partial"
    if engine == "quant":
        available = len(evidence)
        return "blocked" if available == 0 else "partial" if available < 3 else "usable"
    if engine == "macro":
        edgeCount = int(payload.get("edgeCount") or 0)
        companyEdges = int(payload.get("companyEdgeCount") or 0)
        macroObserved = sum(row.get("kind") == "macroObservation" for row in evidence if isinstance(row, dict))
        companyCoverage = companyEdges / edgeCount if edgeCount else 0.0
        return "blocked" if edgeCount == 0 or macroObserved == 0 else "usable" if companyCoverage >= 0.5 else "partial"
    return None


def auditProduct(engine: str, product: dict[str, Any], bundle: dict[str, Any]) -> list[dict[str, str]]:
    """한 제품의 공통 계약과 엔진 고유 상태 의미를 동시에 검증한다."""
    from dartlab.synth.lensContract import validateLensProduct

    issues: list[dict[str, str]] = []
    try:
        validateLensProduct(product)
    except (TypeError, ValueError) as exc:
        issues.append(_issue("hard", "lensContract", str(exc), engine=engine))
        return issues

    identity = product["identity"]
    status = str(product["status"])
    confidence = product["confidence"]
    evidence = product["evidence"]
    if identity["engine"] != engine:
        issues.append(_issue("hard", "engineIdentity", f"identity.engine={identity['engine']}", engine=engine))
    if identity["target"] != bundle.get("target"):
        issues.append(_issue("hard", "targetIdentity", f"identity.target={identity['target']}", engine=engine))
    if str(identity["market"]).upper() != str(bundle.get("market")).upper():
        issues.append(_issue("hard", "marketIdentity", f"identity.market={identity['market']}", engine=engine))
    if confidence.get("method") != _EXPECTED_METHODS[engine]:
        issues.append(_issue("hard", "confidenceMethod", str(confidence.get("method")), engine=engine))
    if status != "blocked" and not evidence:
        issues.append(_issue("hard", "evidenceFloor", "차단되지 않은 판단에 직접 근거가 없습니다.", engine=engine))
    if status == "usable" and not product.get("falsifiers"):
        issues.append(_issue("hard", "falsifierFloor", "usable 판단에 반증 조건이 없습니다.", engine=engine))
    if status == "blocked" and confidence.get("level") != "blocked":
        issues.append(_issue("hard", "blockedConfidence", str(confidence.get("level")), engine=engine))

    expected = _expectedStatus(engine, product)
    if expected is not None and status != expected:
        issues.append(_issue("hard", "statusHonesty", f"status={status}, expected={expected}", engine=engine))

    score = _number(confidence.get("score"))
    payload = product.get("payload") if isinstance(product.get("payload"), dict) else {}
    if engine == "analysis":
        coverage = payload.get("coverage") if isinstance(payload.get("coverage"), dict) else {}
        expectedScore = round((int(coverage.get("observedRequiredDomains") or 0) / 4) * 100, 1)
        if score != expectedScore:
            issues.append(
                _issue("hard", "analysisCoverageScore", f"score={score}, expected={expectedScore}", engine=engine)
            )
    elif engine == "credit":
        coverage = payload.get("coverage") if isinstance(payload.get("coverage"), dict) else {}
        weightCoverage = _number(coverage.get("weightCoverage"))
        if score != weightCoverage:
            issues.append(
                _issue("hard", "creditCoverageScore", f"score={score}, expected={weightCoverage}", engine=engine)
            )
    elif engine == "industry":
        coverage = payload.get("coverage") if isinstance(payload.get("coverage"), dict) else {}
        total = int(coverage.get("totalBlocks") or 0)
        observed = int(coverage.get("observedBlocks") or 0)
        floor = round((observed / total) * 50, 1) if total else 0.0
        if score is None or score < floor or score > floor + 50.0:
            issues.append(
                _issue(
                    "hard", "industryCoverageScore", f"score={score}, validRange={floor}~{floor + 50}", engine=engine
                )
            )
    elif engine == "quant":
        classification = payload.get("classification")
        if classification == "inconclusive" and score is not None and score > 65:
            issues.append(_issue("hard", "quantClarityCap", f"score={score}", engine=engine))
        assumptions = product.get("assumptions") or []
        if not any(row.get("id") == "expectationMethod" for row in assumptions if isinstance(row, dict)):
            issues.append(_issue("hard", "quantProxyDisclosure", "기대 프록시 가정이 없습니다.", engine=engine))
    elif engine == "macro":
        if payload.get("companyBound") is not True:
            issues.append(
                _issue("hard", "macroCompanyBinding", "Company 경로가 시장 일반론으로 계산됐습니다.", engine=engine)
            )

    return issues


def auditBundle(bundle: dict[str, Any]) -> dict[str, Any]:
    """공개 bundle 전체의 제품 완전성, 의미 계약, 렌즈 간 긴장을 감사한다."""
    issues: list[dict[str, str]] = []
    products = bundle.get("products") if isinstance(bundle.get("products"), dict) else {}
    if bundle.get("noComposite") is not True or "results" in bundle:
        issues.append(_issue("hard", "publicBoundary", "공개 bundle 경계가 깨졌습니다."))
    missing = [engine for engine in _ENGINES if engine not in products]
    for engine in missing:
        issues.append(_issue("hard", "productCompleteness", "대표 제품이 없습니다.", engine=engine))
    for engine, product in products.items():
        if engine in _ENGINES and isinstance(product, dict):
            issues.extend(auditProduct(engine, product, bundle))

    analysis = products.get("analysis") if isinstance(products.get("analysis"), dict) else {}
    credit = products.get("credit") if isinstance(products.get("credit"), dict) else {}
    if analysis.get("status") == "usable" and credit.get("status") in {"partial", "blocked"}:
        issues.append(
            _issue(
                "review",
                "crossLensTension",
                "재무 종합평가는 usable이지만 신용 판단은 결손입니다. 결론 병치가 적절한지 검토해야 합니다.",
            )
        )

    return {
        "target": bundle.get("target"),
        "market": bundle.get("market"),
        "productCount": len(products),
        "statuses": {engine: products.get(engine, {}).get("status") for engine in _ENGINES},
        "issues": issues,
        "hardIssueCount": sum(row["severity"] == "hard" for row in issues),
        "reviewIssueCount": sum(row["severity"] == "review" for row in issues),
    }


def _productReviewRows(bundle: dict[str, Any]) -> dict[str, Any]:
    products = bundle.get("products") if isinstance(bundle.get("products"), dict) else {}
    rows = {}
    for engine in _ENGINES:
        product = products.get(engine)
        if not isinstance(product, dict):
            continue
        conclusion = product.get("conclusion") if isinstance(product.get("conclusion"), dict) else {}
        confidence = product.get("confidence") if isinstance(product.get("confidence"), dict) else {}
        rows[engine] = {
            "status": product.get("status"),
            "label": conclusion.get("label"),
            "summary": conclusion.get("summary"),
            "evidenceCoverage": confidence.get("score"),
            "coverageMethod": confidence.get("method"),
            "drivers": product.get("drivers") or [],
            "evidence": product.get("evidence") or [],
            "gaps": product.get("gaps") or [],
            "falsifiers": product.get("falsifiers") or [],
        }
    return rows


def runWorker(stockCode: str, output: Path) -> int:
    """한 기업만 실제 계산하고 원본 artifact와 감사 결과를 기록한다."""
    started = time.perf_counter()
    try:
        import dartlab
        from dartlab.pipeline.lensArtifacts import buildLensArtifact

        company = dartlab.Company(stockCode)
        bundle = buildLensArtifact(company)
        audit = auditBundle(bundle)
        elapsed = round(time.perf_counter() - started, 3)
        _writeJson(output / "artifacts" / f"{stockCode}.json", bundle)
        _writeJson(
            output / "companies" / f"{stockCode}.json",
            {
                "stockCode": stockCode,
                "state": "calculated",
                "elapsedSeconds": elapsed,
                "audit": audit,
                "review": _productReviewRows(bundle),
            },
        )
        print(
            f"[worker] {stockCode} products={audit['productCount']} hard={audit['hardIssueCount']} "
            f"elapsed={elapsed:.1f}s",
            flush=True,
        )
        return 0
    except Exception as exc:  # noqa: BLE001, 실패 자체가 제품 성숙도 측정값이다.
        elapsed = round(time.perf_counter() - started, 3)
        _writeJson(
            output / "companies" / f"{stockCode}.json",
            {
                "stockCode": stockCode,
                "state": "failed",
                "elapsedSeconds": elapsed,
                "error": f"{type(exc).__name__}: {str(exc)[:1000]}",
            },
        )
        print(f"[worker] {stockCode} FAILED {type(exc).__name__}: {exc}", flush=True)
        return 1


def runEngineWorker(stockCode: str, engine: str, output: Path) -> int:
    """렌즈 하나만 새 Company 프로세스에서 실행해 병목을 분리한다."""
    started = time.perf_counter()
    try:
        import dartlab
        from dartlab.story.lensProducts import collectLensProducts, publicLensBundle

        company = dartlab.Company(stockCode)
        bundle = publicLensBundle(collectLensProducts(company, engines=[engine], refresh=True))
        product = bundle.get("products", {}).get(engine)
        elapsed = round(time.perf_counter() - started, 3)
        _writeJson(
            output / "profiles" / f"{stockCode}-{engine}.json",
            {
                "stockCode": stockCode,
                "engine": engine,
                "state": "calculated" if isinstance(product, dict) else "missing",
                "elapsedSeconds": elapsed,
                "status": product.get("status") if isinstance(product, dict) else None,
                "confidence": product.get("confidence") if isinstance(product, dict) else None,
                "gaps": bundle.get("gaps") or [],
            },
        )
        print(
            f"[engine-worker] {stockCode} {engine} status="
            f"{product.get('status') if isinstance(product, dict) else 'missing'} elapsed={elapsed:.1f}s",
            flush=True,
        )
        return 0 if isinstance(product, dict) else 1
    except Exception as exc:  # noqa: BLE001, 프로파일 실패도 측정값이다.
        elapsed = round(time.perf_counter() - started, 3)
        _writeJson(
            output / "profiles" / f"{stockCode}-{engine}.json",
            {
                "stockCode": stockCode,
                "engine": engine,
                "state": "failed",
                "elapsedSeconds": elapsed,
                "error": f"{type(exc).__name__}: {str(exc)[:1000]}",
            },
        )
        return 1


def _runMonitored(command: list[str], *, logPath: Path | None = None) -> tuple[int, float | None]:
    logHandle = None
    if logPath is not None:
        logPath.parent.mkdir(parents=True, exist_ok=True)
        logHandle = logPath.open("w", encoding="utf-8")
    process = subprocess.Popen(
        command,
        stdout=logHandle if logHandle is not None else None,
        stderr=subprocess.STDOUT if logHandle is not None else None,
    )
    peakRss = 0
    started = time.monotonic()
    try:
        try:
            import psutil

            watched = psutil.Process(process.pid)
            while process.poll() is None:
                try:
                    processes = [watched, *watched.children(recursive=True)]
                    rss = sum(item.memory_info().rss for item in processes if item.is_running())
                    peakRss = max(peakRss, rss)
                except (psutil.Error, OSError):
                    pass
                if time.monotonic() - started > _WORKER_TIMEOUT_SECONDS:
                    children = watched.children(recursive=True)
                    for item in [*children, watched]:
                        try:
                            item.terminate()
                        except psutil.Error:
                            pass
                    _, alive = psutil.wait_procs([*children, watched], timeout=5)
                    for item in alive:
                        try:
                            item.kill()
                        except psutil.Error:
                            pass
                    return 124, round(peakRss / (1024 * 1024), 1) if peakRss else None
                time.sleep(0.25)
        except ImportError:
            process.wait()
        return int(process.wait()), round(peakRss / (1024 * 1024), 1) if peakRss else None
    finally:
        if logHandle is not None:
            logHandle.close()


def _runIsolatedWorker(stockCode: str, output: Path) -> tuple[int, float | None]:
    command = [
        sys.executable,
        "-X",
        "utf8",
        str(Path(__file__).resolve()),
        "--worker",
        stockCode,
        "--output",
        str(output),
    ]
    return _runMonitored(command, logPath=output / "logs" / f"{stockCode}.log")


def profileEngines(stockCode: str, output: Path) -> int:
    records = []
    for engine in _ENGINES:
        print(f"[profile] {stockCode} {engine}", flush=True)
        command = [
            sys.executable,
            "-X",
            "utf8",
            str(Path(__file__).resolve()),
            "--worker",
            stockCode,
            "--engine-worker",
            engine,
            "--output",
            str(output),
        ]
        exitCode, peakRss = _runMonitored(command)
        path = output / "profiles" / f"{stockCode}-{engine}.json"
        if path.exists():
            record = json.loads(path.read_text(encoding="utf-8"))
        else:
            record = {"stockCode": stockCode, "engine": engine, "state": "failed", "error": "결과 파일 없음"}
        record["workerExitCode"] = exitCode
        record["peakRssMb"] = peakRss
        _writeJson(path, record)
        records.append(record)
        print(
            f"  state={record['state']} elapsed={record.get('elapsedSeconds')}s peak={peakRss}MB",
            flush=True,
        )
    _writeJson(output / "profiles" / f"{stockCode}-summary.json", {"stockCode": stockCode, "engines": records})
    return 0 if all(row["state"] == "calculated" for row in records) else 1


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, math.ceil((len(ordered) - 1) * fraction))
    return round(ordered[index], 3)


def summarizeRun(cohort: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    """사전에 고정한 제품 완전성, 유용성, 성능 하한으로 최종 판정한다."""
    expected = len(cohort.get("companies") or [])
    calculated = [row for row in records if row.get("state") == "calculated"]
    failed = [row for row in records if row.get("state") != "calculated"]
    hardIssues = [
        issue
        for row in calculated
        for issue in row.get("audit", {}).get("issues", [])
        if issue.get("severity") == "hard"
    ]
    statusCounts = {engine: Counter() for engine in _ENGINES}
    for row in calculated:
        for engine, status in row.get("audit", {}).get("statuses", {}).items():
            if engine in statusCounts:
                statusCounts[engine][str(status or "missing")] += 1
    utilityRates = {
        engine: round(
            (counts.get("usable", 0) + counts.get("partial", 0)) / expected,
            4,
        )
        if expected
        else 0.0
        for engine, counts in statusCounts.items()
    }
    usableRates = {
        engine: round(counts.get("usable", 0) / expected, 4) if expected else 0.0
        for engine, counts in statusCounts.items()
    }
    elapsed = [float(row["elapsedSeconds"]) for row in calculated if row.get("elapsedSeconds") is not None]
    peaks = [float(row["peakRssMb"]) for row in calculated if row.get("peakRssMb") is not None]
    p95 = _percentile(elapsed, 0.95)
    maxPeak = max(peaks) if peaks else None

    buildPassed = len(calculated) == expected and not failed
    contractPassed = not hardIssues and all(row.get("audit", {}).get("productCount") == 5 for row in calculated)
    utilityPassed = all(utilityRates[engine] >= floor for engine, floor in _UTILITY_FLOORS.items())
    decisivenessPassed = all(usableRates[engine] >= floor for engine, floor in _DECISIVENESS_FLOORS.items())
    latencyPassed = p95 is not None and p95 <= _PERFORMANCE_LIMITS["p95Seconds"]
    memoryPassed = maxPeak is not None and maxPeak <= _PERFORMANCE_LIMITS["peakRssMb"]
    performancePassed = latencyPassed and memoryPassed
    return {
        "schemaVersion": 1,
        "generatedAt": datetime.now().astimezone().isoformat(),
        "expectedCompanies": expected,
        "calculatedCompanies": len(calculated),
        "failedCompanies": len(failed),
        "hardIssueCount": len(hardIssues),
        "reviewIssueCount": sum(row.get("audit", {}).get("reviewIssueCount", 0) for row in calculated),
        "statusCounts": {engine: dict(counts) for engine, counts in statusCounts.items()},
        "utilityRates": utilityRates,
        "usableRates": usableRates,
        "thresholds": {
            "utilityFloors": _UTILITY_FLOORS,
            "decisivenessFloors": _DECISIVENESS_FLOORS,
            "performanceLimits": _PERFORMANCE_LIMITS,
        },
        "performance": {
            "medianSeconds": round(median(elapsed), 3) if elapsed else None,
            "p95Seconds": p95,
            "maxPeakRssMb": maxPeak,
        },
        "gates": {
            "buildPassed": buildPassed,
            "contractPassed": contractPassed,
            "utilityPassed": utilityPassed,
            "decisivenessPassed": decisivenessPassed,
            "latencyPassed": latencyPassed,
            "memoryPassed": memoryPassed,
            "performancePassed": performancePassed,
        },
        "excellent": buildPassed and contractPassed and utilityPassed and decisivenessPassed and performancePassed,
        "failures": failed,
        "hardIssues": hardIssues,
    }


def renderReviewPacket(cohort: dict[str, Any], records: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    companyMeta = {row["stockCode"]: row for row in cohort.get("companies") or []}
    lines = [
        "# Lens Product Calibration Review",
        "",
        f"- 실행 기업: {summary['calculatedCompanies']}/{summary['expectedCompanies']}",
        f"- hard issue: {summary['hardIssueCount']}",
        f"- 최종 excellent gate: {summary['excellent']}",
        "- confidence 숫자는 예측 정확도가 아니라 근거 충족도다.",
        "",
        "## Gate",
        "",
    ]
    for key, value in summary["gates"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Utility", ""])
    for engine in _ENGINES:
        lines.append(
            f"- {engine}: nonblocked {summary['utilityRates'][engine]:.1%}, "
            f"usable {summary['usableRates'][engine]:.1%} "
            f"(floors {_UTILITY_FLOORS[engine]:.0%}/{_DECISIVENESS_FLOORS[engine]:.0%}, "
            f"{summary['statusCounts'][engine]})"
        )
    lines.extend(["", "## Company Review", ""])
    for record in records:
        code = str(record.get("stockCode"))
        meta = companyMeta.get(code, {})
        lines.append(
            f"### {code} {meta.get('name', '')} | {meta.get('industryName', '미분류')} | "
            f"{record.get('elapsedSeconds')}s | peak {record.get('peakRssMb')}MB"
        )
        lines.append("")
        if record.get("state") != "calculated":
            lines.append(f"- FAILED: {record.get('error')}")
            lines.append("")
            continue
        for engine in _ENGINES:
            product = record.get("review", {}).get(engine)
            if not isinstance(product, dict):
                lines.append(f"- {engine}: 제품 없음")
                continue
            lines.append(
                f"- {engine}: {product.get('status')} | {product.get('label')} | "
                f"근거충족도 {product.get('evidenceCoverage')}"
            )
            lines.append(f"  - 판단: {product.get('summary')}")
            if product.get("gaps"):
                reasons = [str(row.get("reason")) for row in product["gaps"][:3] if isinstance(row, dict)]
                lines.append(f"  - 결손: {' / '.join(reasons)}")
        for issue in record.get("audit", {}).get("issues", []):
            lines.append(f"- {issue.get('severity')} {issue.get('rule')}: {issue.get('message')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _calculateCompany(stockCode: str, output: Path) -> dict[str, Any]:
    recordPath = output / "companies" / f"{stockCode}.json"
    exitCode, peakRss = _runIsolatedWorker(stockCode, output)
    if not recordPath.exists():
        _writeJson(
            recordPath,
            {
                "stockCode": stockCode,
                "state": "failed",
                "error": f"worker exit={exitCode}, 결과 파일 없음",
            },
        )
    record = json.loads(recordPath.read_text(encoding="utf-8"))
    record["peakRssMb"] = peakRss
    record["workerExitCode"] = exitCode
    _writeJson(recordPath, record)
    return record


def runCohort(cohort: dict[str, Any], output: Path, *, resume: bool, jobs: int = 1) -> int:
    companies = cohort.get("companies") if isinstance(cohort.get("companies"), list) else []
    recordsByIndex: dict[int, dict[str, Any]] = {}
    pending = {}
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as executor:
        for index, company in enumerate(companies):
            stockCode = _normalizeCode(company.get("stockCode"))
            recordPath = output / "companies" / f"{stockCode}.json"
            if resume and recordPath.exists():
                print(f"[{index + 1}/{len(companies)}] {stockCode} resume", flush=True)
                recordsByIndex[index] = json.loads(recordPath.read_text(encoding="utf-8"))
            else:
                print(f"[{index + 1}/{len(companies)}] {stockCode} isolated worker", flush=True)
                pending[executor.submit(_calculateCompany, stockCode, output)] = (index, stockCode)

        for future in as_completed(pending):
            index, stockCode = pending[future]
            try:
                recordsByIndex[index] = future.result()
            except Exception as exc:  # pragma: no cover - subprocess boundary protection
                record = {
                    "stockCode": stockCode,
                    "state": "failed",
                    "error": f"calibration monitor {type(exc).__name__}: {exc}",
                }
                _writeJson(output / "companies" / f"{stockCode}.json", record)
                recordsByIndex[index] = record

            completedIndices = sorted(recordsByIndex)
            completedCompanies = [companies[item] for item in completedIndices]
            completedRecords = [recordsByIndex[item] for item in completedIndices]
            partial = summarizeRun({**cohort, "companies": completedCompanies}, completedRecords)
            _writeJson(output / "summary.partial.json", partial)
            print(
                f"  progress calculated={partial['calculatedCompanies']}/{len(recordsByIndex)} "
                f"hard={partial['hardIssueCount']}",
                flush=True,
            )

    records = [recordsByIndex[index] for index in range(len(companies))]

    summary = summarizeRun(cohort, records)
    _writeJson(output / "summary.json", summary)
    (output / "review.md").write_text(renderReviewPacket(cohort, records, summary), encoding="utf-8")
    print(
        f"[calibration] excellent={summary['excellent']} calculated={summary['calculatedCompanies']}/"
        f"{summary['expectedCompanies']} hard={summary['hardIssueCount']} output={output}",
        flush=True,
    )
    return 0 if summary["excellent"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", maxsplit=1)[0])
    parser.add_argument("--output", type=Path, default=Path("C:/tmp/dartlab-lens-calibration"))
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--select-only", action="store_true", dest="selectOnly")
    parser.add_argument("--cohort", type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    parser.add_argument("--engine-worker", choices=_ENGINES, dest="engineWorker", help=argparse.SUPPRESS)
    parser.add_argument("--profile-engines", dest="profileEngines")
    args = parser.parse_args()

    output = args.output.resolve()
    if args.worker:
        if args.engineWorker:
            return runEngineWorker(_normalizeCode(args.worker), args.engineWorker, output)
        return runWorker(_normalizeCode(args.worker), output)
    if args.profileEngines:
        return profileEngines(_normalizeCode(args.profileEngines), output)

    if args.cohort:
        cohort = json.loads(args.cohort.read_text(encoding="utf-8"))
        _writeJson(output / "cohort.json", cohort)
    else:
        cohort = buildCohort(limit=args.limit)
        _writeJson(output / "cohort.json", cohort)
    if args.selectOnly:
        print(
            f"[calibration] cohort={cohort['selectedCount']} industries="
            f"{cohort['distribution']['industryCount']} output={output / 'cohort.json'}",
            flush=True,
        )
        return 0
    return runCohort(cohort, output, resume=args.resume, jobs=args.jobs)


if __name__ == "__main__":
    sys.exit(main())
