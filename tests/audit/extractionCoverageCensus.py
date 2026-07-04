"""추출 커버리지 census: 카탈로그 매니페스트 vs 실제 추출 원장 (성공 TODO).

`dartlab.core.extractionCatalog` 의 각 개념이 실제로 추출되는지 로컬 parquet(dart panel/report,
edgar finance)로 표본 실측한다. Guard Index 형제 감사도구. Company facade 를 안 잡고 폴라스 직독 +
회사당 신호 1회 read + gc 로 OOM 안전(CLAUDE.md Polars Rust 힙 가드).

**성공 정의**: 전 개념 status 가 {parity-ok, honestNull-ok, dartOnly-ok} 안. gap = provider 표면 주장이
있는데 표본 커버리지 0. baseline(`_baselines/extractionCoverage.json`) 은 부채 원장 = 신규 갭 증가만 회귀.

실행::

    uv run python -X utf8 tests/audit/extractionCoverageCensus.py           # 원장 출력
    uv run python -X utf8 tests/audit/extractionCoverageCensus.py --write   # baseline 갱신
"""

from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path

import polars as pl

from dartlab.core.extractionCatalog import (
    DartSource,
    EdgarSource,
    ExtractionConcept,
    HonestNull,
    getExtractionConcepts,
)

PRESENT_THRESHOLD = 0.30  # 표본 30%+ 신호 = 추출가능 실재
_BASELINE = Path(__file__).resolve().parent / "_baselines" / "extractionCoverage.json"

_KR_PREFER = [
    "005930",
    "000660",
    "005380",
    "035420",
    "051910",
    "000270",
    "068270",
    "006400",
    "105560",
    "055550",
    "012330",
    "028260",
    "066570",
    "003550",
    "015760",
    "034730",
    "032830",
    "018260",
    "009150",
    "011200",
    "010950",
    "096770",
    "017670",
    "030200",
]


def _dirs() -> tuple[Path, Path, Path]:
    """dart panel/report + edgar finance 디렉터리를 dataLoader 규약으로 해소."""
    from dartlab.core.dataLoader import _dataDir

    return _dataDir("panel"), _dataDir("report"), _dataDir("edgar")


def krSample(panDir: Path, repDir: Path, n: int) -> list[str]:
    """KR 종목 표본 (대형주 우선, panel+report 둘 다 존재하는 것만)."""
    out = [c for c in _KR_PREFER if (panDir / f"{c}.parquet").exists() and (repDir / f"{c}.parquet").exists()]
    return out[:n]


def usSample(efDir: Path, n: int) -> list[Path]:
    """US 표본 (edgar finance parquet 크기 상위 = 대형 filer 우선, 소형 잡음 회피)."""
    files = list(efDir.glob("*.parquet"))
    files.sort(key=lambda p: p.stat().st_size, reverse=True)
    return files[:n]


def krSignals(code: str, panDir: Path, repDir: Path) -> dict:
    """KR 한 종목 추출 신호 1회 프리로드: panel NT_ 키 집합 + report apiType 집합 + panel 존재."""
    sig: dict = {"notes": set(), "apiTypes": set(), "hasPanel": False}
    pp = panDir / f"{code}.parquet"
    if pp.exists():
        try:
            dk = pl.read_parquet(pp, columns=["disclosureKey"]).get_column("disclosureKey")
            sig["notes"] = {x for x in dk.drop_nulls().to_list() if x}
            sig["hasPanel"] = dk.len() > 0
        except (pl.exceptions.PolarsError, OSError):
            pass
    rp = repDir / f"{code}.parquet"
    if rp.exists():
        try:
            at = pl.read_parquet(rp, columns=["apiType"]).get_column("apiType")
            sig["apiTypes"] = {x for x in at.drop_nulls().to_list() if x}
        except (pl.exceptions.PolarsError, OSError):
            pass
    return sig


def usSignals(path: Path) -> set[str]:
    """US 한 filer 의 us-gaap 태그 집합 1회 프리로드 (10-K/20-F facts)."""
    try:
        df = (
            pl.scan_parquet(path)
            .filter(pl.col("form").is_in(["10-K", "20-F"]))
            .select("tag")
            .collect(engine="streaming")
        )
        return set(df.get_column("tag").drop_nulls().to_list())
    except (pl.exceptions.PolarsError, OSError):
        return set()


def dartHit(concept: ExtractionConcept, sig: dict) -> bool | None:
    """개념의 DART 신호가 이 회사에 있나. None = 자동측정 불가(narrative/segmentTable)."""
    d = concept.dart
    if not isinstance(d, DartSource):
        return None
    if d.surface == "note":
        prefix = d.key[:-1]  # 마지막 scope 숫자 제거로 연결/별도 둘 다 매칭
        return any(k.startswith(prefix) for k in sig["notes"])
    if d.surface == "report":
        return d.key in sig["apiTypes"]
    if d.surface == "statement":
        return sig["hasPanel"]
    return None  # narrative / segmentTable


def edgarHit(concept: ExtractionConcept, tags: set[str]) -> bool | str | None:
    """개념의 EDGAR 신호가 이 filer 에 있나. 'N/A'=HonestNull, None=local 미측정(proxy/item/dera)."""
    e = concept.edgar
    if isinstance(e, HonestNull):
        return "N/A"
    if not isinstance(e, EdgarSource):
        return None
    if e.surface in ("proxy", "item", "deraFacts"):
        return None  # 로컬 edgar/report/DERA 부재로 미측정 (정직)
    return any(t in tags for t in e.keys)  # xbrlTag / statement


def _status(concept: ExtractionConcept, dartCov, edgarCov, isNa: bool) -> str:
    """개념 status 판정."""
    dartOk = dartCov is not None and dartCov >= PRESENT_THRESHOLD
    dartSparse = dartCov is not None and 0 < dartCov < PRESENT_THRESHOLD
    dartGap = dartCov is not None and dartCov == 0
    edgarOk = edgarCov is not None and edgarCov >= PRESENT_THRESHOLD
    edgarGap = edgarCov is not None and edgarCov == 0
    edgarUnmeasured = edgarCov is None and not isNa

    if dartCov is None and concept.category in ("narrative", "segment"):
        return "narrative-P2"  # SPINE 앵커 추출 대상 (raw 신호 미측정)
    if isNa:
        return "honestNull-ok" if dartOk else ("honestNull-dartSparse" if dartSparse else "gap-dart")
    if dartOk and edgarOk:
        return "parity-ok"
    if dartOk and edgarUnmeasured:
        return "dartOnly-ok-edgarUnmeasured"
    if dartOk and edgarGap:
        return "gap-edgar"
    if dartSparse:
        return "sparse"
    if dartGap:
        return "gap-dart"
    if edgarOk and dartCov is None:
        return "edgarOnly-ok"
    return "review"


def uncataloguedSignals(krSigs: dict[str, dict]) -> dict:
    """카탈로그가 놓친 추출 신호(panel NT_ 패밀리 · report apiType)를 탐지한다 = 완전성 측정.

    census 의 생존편향(카탈로그에 넣은 것만 확인)을 깨는 핵심. 표본 panel/report 에 실재하나
    카탈로그가 커버 안 하는 신호를 빈도순으로 드러낸다. "완전 탈탈털기" 를 측정 가능·추적 가능하게.

    Args:
        krSigs: {code: krSignals} 프리로드 신호맵.

    Returns:
        {notePresent, noteCatalogued, noteUncatalogued[(prefix,freq)], apiPresent, apiUncatalogued}.

    Raises:
        없음.

    Example:
        >>> uncataloguedSignals({})  # doctest: +SKIP
    """
    catNote = {
        c.dart.key[:-1] for c in getExtractionConcepts() if isinstance(c.dart, DartSource) and c.dart.surface == "note"
    }
    catApi = {
        c.dart.key for c in getExtractionConcepts() if isinstance(c.dart, DartSource) and c.dart.surface == "report"
    }
    ntFreq: dict[str, int] = {}
    apiFreq: dict[str, int] = {}
    for sig in krSigs.values():
        for k in {x[:-1] for x in sig["notes"] if x.startswith("NT_")}:
            ntFreq[k] = ntFreq.get(k, 0) + 1
        for a in sig["apiTypes"]:
            apiFreq[a] = apiFreq.get(a, 0) + 1
    uncatNt = sorted([(k, n) for k, n in ntFreq.items() if k not in catNote], key=lambda x: -x[1])
    uncatApi = sorted([(a, n) for a, n in apiFreq.items() if a not in catApi], key=lambda x: -x[1])
    return {
        "notePresent": len(ntFreq),
        "noteCatalogued": len(ntFreq) - len(uncatNt),
        "noteUncatalogued": uncatNt,
        "apiPresent": len(apiFreq),
        "apiCatalogued": len(apiFreq) - len(uncatApi),
        "apiUncatalogued": uncatApi,
    }


def run(krN: int = 16, usN: int = 20) -> dict:
    """전 개념 대 표본 커버리지 측정 후 개념별 원장 산출 + 미카탈로그 완전성 측정."""
    panDir, repDir, efDir = _dirs()
    if not panDir.exists() or not efDir.exists():
        return {"error": f"data dir 부재: panel={panDir.exists()} edgar={efDir.exists()}", "ledger": []}

    kr = krSample(panDir, repDir, krN)
    us = usSample(efDir, usN)
    krSigs = {}
    for i, c in enumerate(kr):
        krSigs[c] = krSignals(c, panDir, repDir)
        if (i + 1) % 8 == 0:
            gc.collect()
    usSigs = []
    for i, p in enumerate(us):
        usSigs.append(usSignals(p))
        if (i + 1) % 8 == 0:
            gc.collect()

    completeness = uncataloguedSignals(krSigs)
    ledger = []
    for concept in getExtractionConcepts():
        dHits = [dartHit(concept, krSigs[c]) for c in kr]
        dMeasured = [h for h in dHits if h is not None]
        dartCov = (sum(dMeasured) / len(dMeasured)) if dMeasured else None

        eHits = [edgarHit(concept, s) for s in usSigs]
        eBool = [h for h in eHits if isinstance(h, bool)]
        isNa = any(h == "N/A" for h in eHits)
        edgarCov = (sum(eBool) / len(eBool)) if eBool else None

        ledger.append(
            {
                "conceptId": concept.conceptId,
                "category": concept.category,
                "label": concept.label,
                "dartCov": round(dartCov, 2) if dartCov is not None else None,
                "edgarCov": round(edgarCov, 2) if edgarCov is not None else None,
                "edgarHonestNull": isNa,
                "registered": concept.registered,
                "status": _status(concept, dartCov, edgarCov, isNa),
            }
        )
    return {
        "krSample": kr,
        "usSampleN": len(us),
        "ledger": ledger,
        "rollup": _rollup(ledger),
        "completeness": completeness,
    }


def _rollup(ledger: list[dict]) -> dict:
    """status 분포 집계."""
    out: dict[str, int] = {}
    for row in ledger:
        out[row["status"]] = out.get(row["status"], 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def writeBaseline(result: dict) -> Path:
    """census 원장을 baseline 부채원장으로 저장한다.

    Args:
        result: run() 산출 dict.

    Returns:
        저장 경로.

    Raises:
        없음.

    Example:
        >>> writeBaseline(run())  # doctest: +SKIP
    """
    _BASELINE.parent.mkdir(parents=True, exist_ok=True)
    comp = result.get("completeness", {})
    payload = {
        "note": "추출 커버리지 부채 원장. gap-* status 는 신규 증가 시 회귀. --write 로 갱신.",
        "krSample": result.get("krSample", []),
        "usSampleN": result.get("usSampleN", 0),
        "rollup": result.get("rollup", {}),
        "completeness": {
            "notePresent": comp.get("notePresent", 0),
            "noteCatalogued": comp.get("noteCatalogued", 0),
            "apiPresent": comp.get("apiPresent", 0),
            "apiCatalogued": comp.get("apiCatalogued", 0),
            "noteUncatalogued": comp.get("noteUncatalogued", []),
            "apiUncatalogued": comp.get("apiUncatalogued", []),
        },
        "ledger": result.get("ledger", []),
    }
    _BASELINE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return _BASELINE


def main() -> None:
    """CLI 진입점: census 실행 후 원장 출력 (--write 면 baseline 갱신)."""
    ap = argparse.ArgumentParser(description="추출 커버리지 census")
    ap.add_argument("--write", action="store_true", help="baseline 원장 갱신")
    ap.add_argument("--krN", type=int, default=16)
    ap.add_argument("--usN", type=int, default=20)
    args = ap.parse_args()

    result = run(krN=args.krN, usN=args.usN)
    if result.get("error"):
        print("census 불가:", result["error"])
        return

    print("KR sample:", result["krSample"])
    print("US sample N:", result["usSampleN"])
    comp = result.get("completeness", {})
    print("\n=== 완전성 (미카탈로그 탐지, 생존편향 차단) ===")
    print(
        f"  note 패밀리: 카탈로그 {comp.get('noteCatalogued', 0)} / 표본실재 {comp.get('notePresent', 0)}"
        f"  (미카탈로그 {len(comp.get('noteUncatalogued', []))})"
    )
    print(
        f"  report apiType: 카탈로그 {comp.get('apiCatalogued', 0)} / 표본실재 {comp.get('apiPresent', 0)}"
        f"  (미카탈로그 {len(comp.get('apiUncatalogued', []))})"
    )
    top = comp.get("noteUncatalogued", [])[:10]
    if top:
        print("  미카탈로그 note 상위(빈도):", ", ".join(f"{k}x({n})" for k, n in top))
    if comp.get("apiUncatalogued"):
        print("  미카탈로그 apiType:", ", ".join(f"{a}({n})" for a, n in comp["apiUncatalogued"]))
    print("\n=== rollup ===")
    print(json.dumps(result["rollup"], ensure_ascii=False, indent=2))
    print("\n=== ledger ===")
    hdr = f"{'conceptId':32} {'cat':18} {'dart':>5} {'edgar':>6} {'reg':>4}  status"
    print(hdr)
    print("-" * len(hdr))
    for row in result["ledger"]:
        d = "" if row["dartCov"] is None else f"{row['dartCov']:.2f}"
        e = "N/A" if row["edgarHonestNull"] else ("" if row["edgarCov"] is None else f"{row['edgarCov']:.2f}")
        reg = "Y" if row["registered"] else ""
        print(f"{row['conceptId']:32} {row['category']:18} {d:>5} {e:>6} {reg:>4}  {row['status']}")

    if args.write:
        path = writeBaseline(result)
        print(f"\nbaseline 갱신: {path}")


if __name__ == "__main__":
    main()
