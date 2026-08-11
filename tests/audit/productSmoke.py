"""사용자 공개 API 제품 스모크.

각 시나리오를 독립 Python 프로세스에서 실행해 Polars/Rust allocator 누적을
격리하고, elapsed/RSS delta/RSS peak 예산을 함께 검증한다.
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "tests" / "audit" / "publicApiScenarios.yml"
BUDGET_PATH = REPO_ROOT / "tests" / "audit" / "resourceBudgets.json"
SAMSUNG = "005930"
_FIXTURE_FILE_PATHS: tuple[str, ...] = (
    "dart/finance/005930.parquet",
    "dart/finance/005930.parquet.etag",
    "dart/panel/005930.parquet",
    "dart/panel/005930.parquet.etag",
    "dart/report/005930.parquet",
    "dart/report/005930.parquet.etag",
    "kindList/corpList.parquet",
)
_SCAN_FIXTURE_COMPANY_COUNT = 1200


class _ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.wintypes.DWORD),
        ("PageFaultCount", ctypes.wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


_winReader: tuple[Any, Any] | None = None


def _winMemoryReader() -> tuple[Any, Any] | None:
    """psapi 호출 준비를 한 번만 한다. 준비 못 하면 None.

    `ctypes.windll` 은 프로세스 전역 캐시라 거기 붙은 함수의 `argtypes` 를 여기서 정하면
    측정 대상인 dartlab 까지 같이 끌려간다. 실제로 그렇게 해서 `company.story` 가
    ArgumentError 로 죽었다. 하니스가 대상을 망가뜨리면 그 측정은 측정이 아니다.
    자기 handle 을 열어 남과 떨어뜨린다.
    """
    global _winReader

    if _winReader is None:
        try:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            psapi = ctypes.WinDLL("psapi", use_last_error=True)
            getCurrentProcess = kernel32.GetCurrentProcess
            getCurrentProcess.argtypes = []
            getCurrentProcess.restype = ctypes.wintypes.HANDLE
            getProcessMemoryInfo = psapi.GetProcessMemoryInfo
            getProcessMemoryInfo.argtypes = [
                ctypes.wintypes.HANDLE,
                ctypes.POINTER(_ProcessMemoryCounters),
                ctypes.wintypes.DWORD,
            ]
            getProcessMemoryInfo.restype = ctypes.wintypes.BOOL
        except (AttributeError, OSError):
            return None
        _winReader = (getCurrentProcess, getProcessMemoryInfo)
    return _winReader


def _rssMb() -> float:
    if os.name == "nt":
        reader = _winMemoryReader()
        if reader is None:
            return -1.0
        getCurrentProcess, getProcessMemoryInfo = reader
        try:
            pmc = _ProcessMemoryCounters()
            pmc.cb = ctypes.sizeof(_ProcessMemoryCounters)
            if getProcessMemoryInfo(getCurrentProcess(), ctypes.byref(pmc), pmc.cb):
                return pmc.WorkingSetSize / (1024 * 1024)
        except (AttributeError, OSError, ValueError):
            return -1.0
    try:
        with open(f"/proc/{os.getpid()}/status", encoding="utf-8") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except (FileNotFoundError, PermissionError):
        return -1.0
    return -1.0


def _loadYaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise SystemExit(f"YAML 형식 오류: {path}")
    return data


def _loadBudgets(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise SystemExit(f"JSON 형식 오류: {path}")
    return data


def _scenarioIds(manifest: dict[str, Any], suite: str, requested: list[str] | None = None) -> list[str]:
    scenarios = manifest.get("scenarios", {})
    ids = requested or list(scenarios)
    selected: list[str] = []
    for scenarioId in ids:
        scenario = scenarios.get(scenarioId)
        if scenario is None:
            raise SystemExit(f"알 수 없는 product smoke scenario: {scenarioId}")
        suites = scenario.get("suites", [])
        if suite in suites:
            selected.append(scenarioId)
    return selected


def _budgetFor(scenarioId: str, manifest: dict[str, Any], budgets: dict[str, Any]) -> dict[str, float]:
    scenario = manifest["scenarios"][scenarioId]
    budgetKey = scenario.get("budget", scenarioId)
    raw = dict(budgets.get("default", {}))
    raw.update(budgets.get("scenarios", {}).get(budgetKey, {}))
    return {k: float(v) for k, v in raw.items()}


def _height(result: Any) -> int | None:
    if hasattr(result, "height"):
        return int(result.height)
    if isinstance(result, dict):
        return len(result)
    if isinstance(result, (list, tuple, set)):
        return len(result)
    if isinstance(result, str):
        return len(result)
    return None


def _ensureNonEmpty(name: str, result: Any, *, minHeight: int = 1) -> dict[str, Any]:
    if result is None:
        raise AssertionError(f"{name}: result is None")
    height = _height(result)
    if height is not None and height < minHeight:
        raise AssertionError(f"{name}: empty result height={height}, min={minHeight}")
    cols = list(getattr(result, "columns", []) or [])
    return {
        "type": type(result).__name__,
        "height": height,
        "width": len(cols) if cols else None,
        "columns": cols[:12],
    }


def _packageInfo() -> dict[str, str]:
    import dartlab

    return {
        "version": str(getattr(dartlab, "__version__", "")),
        "file": str(Path(dartlab.__file__).resolve()),
    }


def _assertImportMode(importMode: str) -> dict[str, str]:
    info = _packageInfo()
    packageFile = Path(info["file"])
    repoSrc = (REPO_ROOT / "src" / "dartlab").resolve()
    try:
        underRepoSrc = packageFile.is_relative_to(repoSrc)
    except AttributeError:
        underRepoSrc = str(packageFile).startswith(str(repoSrc))
    if importMode == "installed" and underRepoSrc:
        raise AssertionError(f"installed smoke 가 source tree 를 import 함: {packageFile}")
    if importMode == "source" and not underRepoSrc:
        raise AssertionError(f"source smoke 가 source tree 밖 패키지를 import 함: {packageFile}")
    return info


def _company():
    import dartlab

    return dartlab.Company(SAMSUNG)


def _publicAccessAll() -> dict[str, Any]:
    import dartlab
    import dartlab.api as dartlabApi

    manifest = _loadYaml(MANIFEST_PATH)
    public = manifest["public_api"]
    touched: list[str] = []
    for name in public["dartlab_symbols"]:
        value = getattr(dartlab, name)
        if value is None and name != "reloadPlugins":
            raise AssertionError(f"dartlab.{name} is None")
        touched.append(f"dartlab.{name}")
    for name in public["dartlab_api_symbols"]:
        value = getattr(dartlabApi, name)
        if value is None:
            raise AssertionError(f"dartlab.api.{name} is None")
        touched.append(f"dartlab.api.{name}")
    return {"type": "public-access", "height": len(touched), "symbols": touched[:10]}


def _scanAxis(axis: str) -> dict[str, Any]:
    import dartlab

    result = dartlab.scan(axis)
    return _ensureNonEmpty(f"scan.{axis}", result)


def _runScenario(scenarioId: str) -> dict[str, Any]:
    if scenarioId == "public.access.all":
        return _publicAccessAll()
    if scenarioId == "capabilities.index":
        import dartlab

        return _ensureNonEmpty("capabilities", dartlab.capabilities(), minHeight=10)
    if scenarioId == "search.name.samsung":
        import dartlab

        return _ensureNonEmpty("searchName", dartlab.searchName("삼성"), minHeight=1)
    if scenarioId == "scan.guide":
        import dartlab

        result = dartlab.scan()
        return _ensureNonEmpty("scan.guide", result, minHeight=10)
    if scenarioId == "scan.account.sales":
        import dartlab

        result = dartlab.scan("account", "매출액")
        info = _ensureNonEmpty("scan.account.sales", result, minHeight=1000)
        periodCols = [col for col in getattr(result, "columns", []) if str(col)[:4].isdigit()]
        if not periodCols:
            raise AssertionError("scan.account.sales: 기간 컬럼 없음")
        info["periodColumns"] = periodCols[:6]
        return info
    if scenarioId == "scan.ratio.roe":
        import dartlab

        result = dartlab.scan("ratio", "roe")
        info = _ensureNonEmpty("scan.ratio.roe", result, minHeight=1000)
        periodCols = [col for col in getattr(result, "columns", []) if str(col)[:4].isdigit()]
        if not periodCols:
            raise AssertionError("scan.ratio.roe: 기간 컬럼 없음")
        info["periodColumns"] = periodCols[:6]
        return info
    if scenarioId == "scan.valuation":
        import dartlab

        return _ensureNonEmpty("scan.valuation", dartlab.scan("valuation"), minHeight=100)
    if scenarioId.startswith("scan.axis."):
        return _scanAxis(scenarioId.removeprefix("scan.axis."))
    if scenarioId == "company.create":
        company = _company()
        return {"type": type(company).__name__, "height": 1}
    if scenarioId == "company.show.IS":
        # 공개 show 은퇴 → panel 단일 표면 (finance facade). 시나리오 ID 는 호환 위해 유지.
        return _ensureNonEmpty("company.show.IS", _company().panel("IS"), minHeight=1)
    if scenarioId == "company.show.BS":
        return _ensureNonEmpty("company.show.BS", _company().panel("BS"), minHeight=1)
    if scenarioId == "company.show.ratios":
        return _ensureNonEmpty("company.show.ratios", _company().panel("ratios"), minHeight=1)
    if scenarioId == "company.topics":
        return _ensureNonEmpty("company.topics", _company().topics, minHeight=1)
    if scenarioId == "company.select.IS":
        result = _company().select("IS")
        rendered = result.render("html") if hasattr(result, "render") else str(result)
        if not rendered:
            raise AssertionError("company.select.IS: render 결과 없음")
        return {"type": type(result).__name__, "height": len(rendered)}
    if scenarioId == "company.analysis.valuation":
        return _ensureNonEmpty("company.analysis.valuation", _company().analysis("가치평가"), minHeight=1)
    if scenarioId == "company.credit":
        return _ensureNonEmpty("company.credit", _company().credit(), minHeight=1)
    if scenarioId == "company.quant":
        return _ensureNonEmpty("company.quant", _company().quant(), minHeight=1)
    if scenarioId == "company.macro":
        return _ensureNonEmpty("company.macro", _company().macro(), minHeight=1)
    if scenarioId == "company.industry":
        return _ensureNonEmpty("company.industry", _company().industry(), minHeight=1)
    if scenarioId == "company.story":
        return _ensureNonEmpty("company.story", _company().story(), minHeight=1)
    raise AssertionError(f"scenario 구현 없음: {scenarioId}")


def _childMain(args: argparse.Namespace) -> int:
    peak = _rssMb()
    stop = threading.Event()

    def sampleLoop() -> None:
        nonlocal peak
        while not stop.is_set():
            rss = _rssMb()
            if rss > peak:
                peak = rss
            stop.wait(0.05)

    sampler = threading.Thread(target=sampleLoop, daemon=True)
    sampler.start()
    before = _rssMb()
    started = time.monotonic()
    payload: dict[str, Any] = {"scenario": args.run_scenario, "ok": False}
    try:
        payload["package"] = _assertImportMode(args.import_mode)
        _enforceScenarioIsolation()
        details = _runScenario(args.run_scenario)
        payload.update({"ok": True, "details": details})
    except BaseException as exc:
        payload.update(
            {
                "ok": False,
                "errorType": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
    finally:
        elapsed = time.monotonic() - started
        after = _rssMb()
        stop.set()
        sampler.join(timeout=1)
        payload.update(
            {
                "elapsedSec": round(elapsed, 3),
                "rssBeforeMb": round(before, 1),
                "rssAfterMb": round(after, 1),
                "rssDeltaMb": round(after - before, 1),
                "rssPeakMb": round(max(peak, before, after), 1),
            }
        )
    print(json.dumps(payload, ensure_ascii=False), flush=True)
    return 0 if payload["ok"] else 1


def _writeScanFixtures(dataRoot: Path) -> None:
    """clean checkout에서도 공개 scan API를 검증할 수 있는 소형 prebuild를 만든다."""
    import polars as pl

    scanDir = dataRoot / "dart" / "scan"
    scanDir.mkdir(parents=True, exist_ok=True)
    codes = [f"{index:06d}" for index in range(100_000, 100_000 + _SCAN_FIXTURE_COMPANY_COUNT)]

    financeRows: list[dict[str, str | None]] = []
    for index, stockCode in enumerate(codes):
        common = {
            "stockCode": stockCode,
            "bsns_year": "2025",
            "reprt_nm": "4분기",
            "fs_nm": "연결재무제표",
            "thstrm_add_amount": None,
        }
        financeRows.extend(
            (
                {
                    **common,
                    "sj_div": "IS",
                    "account_id": "ifrs-full_Revenue",
                    "account_nm": "매출액",
                    "thstrm_amount": str(1_000_000_000 + index * 1_000_000),
                },
                {
                    **common,
                    "sj_div": "IS",
                    "account_id": "ifrs-full_ProfitLoss",
                    "account_nm": "당기순이익",
                    "thstrm_amount": str(100_000_000 + index * 100_000),
                },
                {
                    **common,
                    "sj_div": "BS",
                    "account_id": "ifrs-full_Equity",
                    "account_nm": "자본총계",
                    "thstrm_amount": str(500_000_000 + index * 500_000),
                },
            )
        )
        prior = {**common, "bsns_year": "2024"}
        financeRows.extend(
            (
                {
                    **prior,
                    "sj_div": "IS",
                    "account_id": "ifrs-full_Revenue",
                    "account_nm": "매출액",
                    "thstrm_amount": str(900_000_000 + index * 900_000),
                },
                {
                    **prior,
                    "sj_div": "IS",
                    "account_id": "ifrs-full_ProfitLoss",
                    "account_nm": "당기순이익",
                    "thstrm_amount": str(90_000_000 + index * 90_000),
                },
                {
                    **prior,
                    "sj_div": "BS",
                    "account_id": "ifrs-full_Equity",
                    "account_nm": "자본총계",
                    "thstrm_amount": str(450_000_000 + index * 450_000),
                },
            )
        )
    pl.DataFrame(financeRows).write_parquet(scanDir / "finance.parquet")

    pl.DataFrame(
        schema={
            "fromPeriod": pl.Utf8,
            "toPeriod": pl.Utf8,
            "sectionTitle": pl.Utf8,
            "changeType": pl.Utf8,
            "sizeA": pl.UInt32,
            "sizeB": pl.UInt32,
            "sizeDelta": pl.Int64,
            "preview": pl.Utf8,
            "stockCode": pl.Utf8,
        }
    ).write_parquet(scanDir / "changes.parquet")
    pl.DataFrame(
        {
            "stock_code": [codes[0]],
            "outstandingShares": [1_000_000],
        },
        schema={"stock_code": pl.Utf8, "outstandingShares": pl.Int64},
    ).write_parquet(scanDir / "sharesOutstanding.parquet")
    pl.DataFrame(
        {
            "stockCode": codes,
            "marketCap": [float(10_000_000_000 + index * 1_000_000) for index in range(len(codes))],
            "per": [10.0] * len(codes),
            "pbr": [1.0] * len(codes),
            "dividendYield": [2.0] * len(codes),
            "current": [10_000] * len(codes),
            "snapshotAt": [datetime(2026, 1, 1)] * len(codes),
        }
    ).write_parquet(scanDir / "valuation.parquet")


def _prepareFixtureData(tmp: tempfile.TemporaryDirectory[str]) -> Path:
    """추적 fixture만 임시 루트에 복사하고 합성 scan prebuild를 더한다."""
    sourceRoot = REPO_ROOT / "tests" / "fixtures"
    dataRoot = Path(tmp.name) / "data"
    for relative in _FIXTURE_FILE_PATHS:
        source = sourceRoot / relative
        if not source.is_file():
            raise RuntimeError(f"product smoke fixture 누락: {source}")
        destination = dataRoot / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    _writeScanFixtures(dataRoot)
    return dataRoot


def _dataEnv(dataMode: str, tmp: tempfile.TemporaryDirectory[str] | None) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("DARTLAB_PRODUCT_SMOKE_OFFLINE", None)
    env.pop("DARTLAB_NO_REFRESH", None)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    if dataMode == "fixtures":
        if tmp is None:
            raise RuntimeError("fixtures data mode requires temp directory")
        env["DARTLAB_DATA_DIR"] = str(_prepareFixtureData(tmp))
        env["DARTLAB_PRODUCT_SMOKE_OFFLINE"] = "1"
        env["DARTLAB_NO_REFRESH"] = "1"
    elif dataMode == "empty":
        if tmp is None:
            raise RuntimeError("empty data mode requires temp directory")
        env["DARTLAB_DATA_DIR"] = str(Path(tmp.name) / "data")
    return env


def _enforceScenarioIsolation() -> bool:
    """고정 데이터 smoke가 외부 네트워크 상태에 의존하지 않게 한다."""
    if os.environ.get("DARTLAB_PRODUCT_SMOKE_OFFLINE") != "1":
        return False
    from dartlab.core.offlineGuard import enforceOffline

    enforceOffline(strict=True)
    return True


def _runChild(
    scenarioId: str,
    env: dict[str, str],
    timeoutSec: float,
    *,
    importMode: str,
    runCwd: Path,
) -> dict[str, Any]:
    cmd = [
        sys.executable,
        "-X",
        "utf8",
        str(Path(__file__).resolve()),
        "--run-scenario",
        scenarioId,
        "--import-mode",
        importMode,
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(runCwd),
        env=env,
        text=True,
        capture_output=True,
        timeout=max(int(timeoutSec) + 30, 60),
        check=False,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    try:
        payload = json.loads(lines[-1]) if lines else {}
    except json.JSONDecodeError:
        payload = {}
    if not payload:
        payload = {"scenario": scenarioId, "ok": False, "errorType": "NoJson", "error": proc.stdout[-2000:]}
    payload["returnCode"] = proc.returncode
    if proc.stderr.strip():
        payload["stderrTail"] = proc.stderr[-2000:]
    if proc.returncode != 0:
        payload["ok"] = False
    return payload


def _checkBudget(result: dict[str, Any], budget: dict[str, float]) -> list[str]:
    failures: list[str] = []
    if not result.get("ok"):
        failures.append(f"{result.get('errorType', 'FAIL')}: {result.get('error', '')}")
    elapsed = float(result.get("elapsedSec", 0))
    delta = float(result.get("rssDeltaMb", 0))
    peak = float(result.get("rssPeakMb", 0))
    if elapsed > budget.get("maxElapsedSec", float("inf")):
        failures.append(f"elapsed {elapsed:.1f}s > {budget['maxElapsedSec']:.0f}s")
    if delta > budget.get("maxRssDeltaMb", float("inf")):
        failures.append(f"RSS delta {delta:.0f}MB > {budget['maxRssDeltaMb']:.0f}MB")
    if peak > budget.get("maxRssPeakMb", float("inf")):
        failures.append(f"RSS peak {peak:.0f}MB > {budget['maxRssPeakMb']:.0f}MB")
    return failures


def runSuite(args: argparse.Namespace) -> int:
    manifest = _loadYaml(args.manifest)
    budgets = _loadBudgets(args.budgets)
    scenarioIds = _scenarioIds(manifest, args.suite, args.scenario)
    if args.list:
        for scenarioId in scenarioIds:
            print(scenarioId)
        return 0

    results: list[dict[str, Any]] = []
    failures: list[str] = []
    tmpCtx: tempfile.TemporaryDirectory[str] | None = None
    cwdCtx: tempfile.TemporaryDirectory[str] | None = None
    if args.data_mode in {"fixtures", "empty"}:
        tmpCtx = tempfile.TemporaryDirectory(prefix="dartlab-product-smoke-")
    if args.cwd_mode == "temp":
        cwdCtx = tempfile.TemporaryDirectory(prefix="dartlab-product-cwd-")
    try:
        env = _dataEnv(args.data_mode, tmpCtx)
        runCwd = Path(cwdCtx.name) if cwdCtx is not None else REPO_ROOT
        for scenarioId in scenarioIds:
            budget = _budgetFor(scenarioId, manifest, budgets)
            result = _runChild(
                scenarioId,
                env,
                budget.get("maxElapsedSec", 60),
                importMode=args.import_mode,
                runCwd=runCwd,
            )
            result["budget"] = budget
            result["dataMode"] = args.data_mode
            result["cwdMode"] = args.cwd_mode
            result["importMode"] = args.import_mode
            results.append(result)
            budgetFailures = _checkBudget(result, budget)
            mark = "OK" if not budgetFailures else "FAIL"
            print(
                f"[{mark}] {scenarioId} "
                f"elapsed={result.get('elapsedSec')}s "
                f"delta={result.get('rssDeltaMb')}MB "
                f"peak={result.get('rssPeakMb')}MB"
            )
            if budgetFailures:
                failures.append(f"{scenarioId}: " + "; ".join(budgetFailures))
    finally:
        if cwdCtx is not None:
            cwdCtx.cleanup()
        if tmpCtx is not None:
            tmpCtx.cleanup()

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        with args.json_out.open("w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    if failures:
        print("\n[product-smoke] 실패", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print(f"[product-smoke] OK scenarios={len(results)} suite={args.suite} dataMode={args.data_mode}")
    return 0


def buildParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--budgets", type=Path, default=BUDGET_PATH)
    parser.add_argument("--suite", choices=["quick", "release", "nightly"], default="quick")
    parser.add_argument("--scenario", action="append", help="특정 scenario id만 실행. 여러 번 지정 가능")
    parser.add_argument("--data-mode", choices=["existing", "fixtures", "empty"], default="existing")
    parser.add_argument(
        "--import-mode",
        choices=["any", "source", "installed"],
        default="any",
        help="source tree 또는 설치된 wheel 중 어느 패키지를 import 해야 하는지 검증",
    )
    parser.add_argument(
        "--cwd-mode",
        choices=["temp", "repo"],
        default="temp",
        help="사용자 실행처럼 repo 밖 임시 cwd 에서 child scenario 를 실행",
    )
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--run-scenario", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = buildParser()
    args = parser.parse_args(argv)
    if args.run_scenario:
        return _childMain(args)
    return runSuite(args)


if __name__ == "__main__":
    raise SystemExit(main())
