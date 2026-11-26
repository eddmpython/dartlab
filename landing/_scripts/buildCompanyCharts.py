"""Company → ChartSpec JSON dump → ``landing/static/charts/{code}/`` 빌드.

dartlab.viz 의 ChartSpec 8 + 6 + 8 종 generator 를 종목 단위로 호출해 정적
JSON 으로 dump 한다. landing/company 페이지가 이 JSON 을 단일
``ChartSpecRenderer`` 로 렌더한다. 이게 viz SSOT 통일 회로의 입구.

출력 구조::

    landing/static/charts/{code}/
        manifest.json                # 차트 목록 + 메타
        narrative/{slug}.json        # 14 종 기존 generator 결과
        statement/{slug}.json        # statement deep-drill (Phase 4)
        peer/{slug}.json             # peer-matrix (Phase 5)

manifest.json 형태::

    {
        "version": "v1",
        "stockCode": "005930",
        "corpName": "삼성전자",
        "generatedAt": "2026-05-07T12:00:00",
        "charts": [
            {"section": "narrative", "key": "revenueTrend",
             "chartType": "combo", "title": "...", "path": "narrative/revenueTrend.json",
             "evidenceBinding": {...}}
        ]
    }

실행::

    uv run python -X utf8 landing/_scripts/buildCompanyCharts.py --code 005930
    uv run python -X utf8 landing/_scripts/buildCompanyCharts.py --code 005930 --code 000660
    uv run python -X utf8 landing/_scripts/buildCompanyCharts.py --top-n 50

메모리 안전: Company 1개 ≈ 200~500MB. 종목당 순차 + 명시적 GC.
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "landing" / "static" / "charts"

# narrative section — 14 종 기존 generator. 각 entry: (slug, generator_fn).
# hero/statement/peer section 은 Phase 3+ 에서 채운다.
_NARRATIVE_SLUGS: list[tuple[str, str]] = [
    ("revenueTrend", "spec_revenue_trend"),
    ("balanceSheet", "spec_balance_sheet"),
    ("profitability", "spec_profitability"),
    ("cashflowWaterfall", "spec_cashflow_waterfall"),
    ("dividend", "spec_dividend"),
    ("insightRadar", "spec_insight_radar"),
    ("ratioSparklines", "spec_ratio_sparklines"),
    ("diffHeatmap", "spec_diff_heatmap"),
]


def _writeJson(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    path.write_text(text, encoding="utf-8")


def _summarizeForManifest(section: str, slug: str, spec: dict) -> dict[str, Any]:
    return {
        "section": section,
        "key": slug,
        "path": f"{section}/{slug}.json",
        "chartType": spec.get("chartType", ""),
        "title": spec.get("title", ""),
        "purpose": spec.get("purpose", ""),
        "evidenceBinding": spec.get("evidenceBinding", {}),
        "evidenceIds": spec.get("evidenceIds", []),
    }


def buildForCode(code: str, *, force: bool = False) -> dict[str, Any]:
    """단일 종목의 ChartSpec 전부를 dump 하고 manifest 를 반환."""
    from dartlab import Company  # lazy import — module load 비용 회피
    from dartlab.viz import generators as _gen

    started = time.time()
    out_dir = OUT_ROOT / code
    if out_dir.exists() and not force:
        # 기존 dump 가 있고 force 가 아니면 manifest 만 갱신 — 차트 파일은 재기록.
        pass

    c = Company(code)
    corpName = getattr(c, "corpName", "")
    manifest_charts: list[dict[str, Any]] = []
    skipped: list[str] = []

    # narrative — 14 종 기존 generator
    for slug, fn_name in _NARRATIVE_SLUGS:
        fn = getattr(_gen, fn_name, None)
        if fn is None:
            skipped.append(f"{slug}:not_registered")
            continue
        try:
            spec = fn(c)
        except (AttributeError, KeyError, OSError, TypeError, ValueError) as e:
            skipped.append(f"{slug}:{type(e).__name__}")
            continue
        if spec is None:
            skipped.append(f"{slug}:no_data")
            continue
        spec_path = out_dir / "narrative" / f"{slug}.json"
        _writeJson(spec_path, spec)
        manifest_charts.append(_summarizeForManifest("narrative", slug, spec))

    # peer — industry.peers + spec_peer_matrix
    try:
        from dartlab.industry.calcs.peers import industryPeerMetricKeys, industryPeers
        from dartlab.viz import specPeerMatrix

        peer_rows = industryPeers(code, n=10)
        if peer_rows:
            metrics = industryPeerMetricKeys(peer_rows) or ["매출(억)"]
            peer_spec = specPeerMatrix(
                rows=[r.asDict() for r in peer_rows],
                metrics=metrics,
                stockCode=code,
                corpName=corpName,
            )
        else:
            peer_spec = None
    except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError) as e:
        peer_spec = None
        skipped.append(f"peerMatrix:{type(e).__name__}")
    if peer_spec is not None:
        spec_path = out_dir / "peer" / "peerMatrix.json"
        _writeJson(spec_path, peer_spec)
        manifest_charts.append(_summarizeForManifest("peer", "peerMatrix", peer_spec))
    else:
        skipped.append("peerMatrix:no_data")

    # Phase 4 의 statement 는 별도 builder 가 채울 자리.

    manifest = {
        "version": "v1",
        "stockCode": code,
        "corpName": corpName,
        "generatedAt": datetime.now(UTC).isoformat(timespec="seconds"),
        "charts": manifest_charts,
        "skipped": skipped,
        "elapsedSec": round(time.time() - started, 2),
    }
    _writeJson(out_dir / "manifest.json", manifest)

    # 메모리 회수 — Polars 네이티브 힙은 gc 로 회수 안 되지만 Company 그래프
    # 레퍼런스는 풀어준다. 다음 종목 builder 가 새로 로드.
    del c
    gc.collect()

    return manifest


def buildForCodes(codes: list[str], *, force: bool = False) -> list[dict[str, Any]]:
    results = []
    for i, code in enumerate(codes, 1):
        print(f"[{i}/{len(codes)}] {code}", flush=True)
        try:
            m = buildForCode(code, force=force)
            print(
                f"  ✓ {len(m['charts'])} charts, {len(m['skipped'])} skipped, {m['elapsedSec']}s",
                flush=True,
            )
            results.append(m)
        except (OSError, RuntimeError, ValueError) as e:
            print(f"  ✗ {type(e).__name__}: {e}", flush=True)
    return results


def _resolveCodes(args: argparse.Namespace) -> list[str]:
    if args.code:
        return list(args.code)
    if args.topN:
        # 시가총액 상위 N — scan 엔진의 marketCap 기반 선택. 빌드 스크립트는
        # 이 경로가 없으면 명시적으로 실패한다 (조용한 fallback 금지).
        try:
            import dartlab

            top = dartlab.scan(metric="marketCap", n=args.topN)
        except (AttributeError, ImportError, OSError, RuntimeError) as e:
            raise SystemExit(f"--top-n {args.topN} 모드는 dartlab.scan 사용 가능 환경에서만 동작: {e}") from e
        return [str(row["stockCode"]) for row in top.iter_rows(named=True)]
    raise SystemExit("--code <코드> 또는 --top-n <N> 중 하나 필수")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n", maxsplit=1)[0])
    p.add_argument("--code", action="append", help="대상 종목코드 (반복 가능)")
    p.add_argument("--top-n", type=int, default=0, help="시가총액 상위 N 종목")
    p.add_argument("--force", action="store_true", help="기존 출력 강제 재기록")
    args = p.parse_args()

    codes = _resolveCodes(args)
    print(f"종목 {len(codes)} 개 빌드 시작 → {OUT_ROOT}")
    results = buildForCodes(codes, force=args.force)

    # 글로벌 인덱스 — 어떤 종목들이 빌드됐는지 한눈에
    index = {
        "version": "v1",
        "generatedAt": datetime.now(UTC).isoformat(timespec="seconds"),
        "companies": [
            {"stockCode": m["stockCode"], "corpName": m["corpName"], "chartCount": len(m["charts"])} for m in results
        ],
    }
    _writeJson(OUT_ROOT / "index.json", index)

    print(f"완료: {len(results)} 종목, 인덱스 → {OUT_ROOT / 'index.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
