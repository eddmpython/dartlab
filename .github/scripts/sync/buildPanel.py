"""sync stage 의 panel(공시 수평화) artifact 빌더 CLI entry.

plan snazzy-wibbling-origami P6. 로컬 DART zip(``data/original/dart/docs/{code}``)으로부터
period-sharded panel artifact(14-col) + slim ``_index.parquet`` 를 빌드해 HF push 를 준비한다.
일일 sync 흐름:

    원본 zip 수집 → 변경 종목 list → buildPanel (본 entry) → uploadData (SYNC_CATEGORY=panel)

본 entry 는 network 0 — 로컬 zip 만 소비한다 (zip 수집은 별도 DART 수집기 선행). build 본체는
``dartlab.providers.dart.panel.build.buildPanelAll`` (zip→14col, multiprocessing). 본 파일은
CI 진입(코드 해석 + changed list 작성)만 담당. _index/_label 은 PRD jazzy-napping-seal 에서
폐기 (cross·라벨검색 표면 제거) — panel artifact 는 ``{code}/{period}.parquet`` 단일.

사용법:
    # 변경 종목만 (dist/changed_panel.txt 또는 dist/changed.txt 기반)
    python .github/scripts/sync/buildPanel.py

    # 특정 종목 list
    python .github/scripts/sync/buildPanel.py --codes 005930,000660

    # 전체 종목 재빌드 (multiprocessing, ~2.6h)
    python .github/scripts/sync/buildPanel.py --all

환경변수:
    DARTLAB_DATA_DIR: 데이터 저장 경로 (기본: ./data)
    PANEL_WORKERS: build multiprocessing workers (기본 8)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _resolveChangedCodes() -> list[str]:
    """dist/changed_panel.txt 또는 dist/changed.txt 에서 변경된 panel 종목 추출."""
    for p in (Path("dist/changed_panel.txt"), Path("dist/changed.txt")):
        if not p.exists():
            continue
        names = [n.strip() for n in p.read_text(encoding="utf-8").splitlines() if n.strip()]
        codes = [Path(n).stem for n in names]
        return [c for c in codes if c.isdigit() and len(c) == 6]
    return []


def _resolveAllCodes(dataDir: str) -> list[str]:
    """data/original/dart/docs/{code} 의 모든 종목코드 (panel zip 원본 디렉터리)."""
    zipBase = Path(dataDir) / "original" / "dart" / "docs"
    if not zipBase.exists():
        return []
    return sorted(d.name for d in zipBase.iterdir() if d.is_dir() and d.name.isdigit() and len(d.name) == 6)


def _writeChangedPanel(codes: list[str], dataDir: str) -> None:
    """uploadData(SYNC_CATEGORY=panel) 가 증분 업로드 시 참고할 changed list.

    양식 — 종목별 period 파일 상대경로 ``{code}/{period}.parquet``. 경로는 ``data/dart/panel``
    (localDir) 기준 상대. (_index/_label 은 PRD jazzy-napping-seal 에서 폐기 — panel artifact 는
    ``{code}/{period}.parquet`` 단일.)
    """
    panelBase = Path(dataDir) / "dart" / "panel"
    lines: list[str] = []
    for code in codes:
        d = panelBase / code
        if not d.exists():
            continue
        for p in sorted(d.glob("*.parquet")):
            lines.append(f"{code}/{p.name}")

    distDir = Path("dist")
    distDir.mkdir(exist_ok=True)
    target = distDir / "changed_panel.txt"
    target.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    print(f"[buildPanel] dist/changed_panel.txt: {len(lines)} entries")


def main() -> int:
    parser = argparse.ArgumentParser(description="panel SSOT artifact 빌더")
    parser.add_argument("--codes", help="쉼표 구분 종목 코드 list (예: 005930,000660)")
    parser.add_argument("--all", action="store_true", help="data/original/dart/docs/ 의 모든 종목 빌드")
    parser.add_argument("--changed", action="store_true", help="dist/changed_panel.txt 또는 dist/changed.txt 기반")
    args = parser.parse_args()

    if "DARTLAB_DATA_DIR" not in os.environ:
        os.environ["DARTLAB_DATA_DIR"] = os.path.join(os.getcwd(), "data")
    dataDir = os.environ["DARTLAB_DATA_DIR"]
    numWorkers = int(os.environ.get("PANEL_WORKERS", "2"))

    if args.codes:
        codes: list[str] | None = [c.strip() for c in args.codes.split(",") if c.strip()]
    elif args.all:
        codes = _resolveAllCodes(dataDir)
    else:
        codes = _resolveChangedCodes()

    if not codes:
        print("[buildPanel] 빌드 대상 0 종목 — 종료")
        _writeChangedPanel([], dataDir)
        return 0

    print(f"[buildPanel] 대상 {len(codes)} 종목 — workers={numWorkers}")
    from dartlab.providers.dart.panel.build import buildPanelAll, panelXbrlRefPath

    # onlinePanel 과 동형 가드: ref 부재로 빌드하면 부분 panel 이 정상 HF panel 을 덮어쓸 위험 →
    # HF seed 선행 강제(fail-fast). ref 없으면 cryptic 다운스트림 실패 대신 명확히 중단한다.
    refPath = panelXbrlRefPath()
    if not refPath.exists():
        print(f"[buildPanel] panelXbrlRef 없음: {refPath} — HF seed 선행 필요(부분 panel 덮어쓰기 차단)")
        return 1

    panelBase = Path(dataDir) / "dart" / "panel"
    out = buildPanelAll(
        refPath=str(refPath),
        outBaseDir=str(panelBase),
        codes=codes,
        numWorkers=numWorkers,
        verbose=True,
    )
    built = sum(1 for _code, stats in out.items() if stats and stats[1] > 0)
    print(f"[buildPanel] 완료: build codes={built}/{len(codes)}")

    _writeChangedPanel(codes, dataDir)
    return 0 if built else 1


if __name__ == "__main__":
    sys.exit(main())
