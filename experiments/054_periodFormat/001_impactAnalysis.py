"""
실험 ID: 054-001
실험명: period 포맷 통일 영향 분석

목적:
- DART `2024_Q1` vs EDGAR `2024-Q1` 포맷 차이를 정량적으로 확인
- 포맷 통일 시 변경 범위와 하위호환 영향 측정
- 중국/일본 등 새 시장 추가 시 period 포맷 설계 근거 마련

가설:
1. period 포맷을 참조하는 코드는 dart/finance/pivot.py 내부에 집중됨
2. common/ 레이어는 period 인덱스 기반이라 포맷 무관
3. DART→하이픈 변환은 pivot.py 2줄 + _aggregateAnnual/Cumulative 3줄 수정이면 충분

방법:
1. 양쪽 pivot 출력의 periods 리스트 샘플 비교
2. period 문자열을 직접 파싱하는 코드 위치 전수 조사
3. 하이픈으로 통일 시 변경점 목록 + 하위호환 영향 범위 측정
4. annual 비교 시 period 포맷이 실제로 장벽인지 검증

결과 (실험 후 작성):
- DART period: ['2022_Q1', '2022_Q2', ...] (underscore, 12개)
- EDGAR period: ['2020-Q1', '2020-Q2', ...] (hyphen, 코드 확인)
- common/ 레이어: period 포맷 의존성 0건 (인덱스 기반만)
- annual years: 양쪽 동일 ("2024" = "2024")
- DART 포맷 의존 라인: 5줄 (pivot.py)
- EDGAR 포맷 의존 라인: 14줄 (pivot.py)

결론:
- 채택: 옵션 D (표준 포맷 함수 도입)
- common/finance/period.py에 formatPeriod/parsePeriod 정의
- 하이픈 채택 (YYYY-QN) — ISO-8601 친화적
- DART pivot.py 5줄, EDGAR pivot.py 14줄 → common 함수로 대체
- annual 비교는 이미 포맷 무관하나, 분기 비교 시 통일 필수

실험일: 2026-03-11
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def analyzeFormat():
    """period 포맷 차이 정량 분석."""

    print("=" * 60)
    print("1. DART period 포맷 샘플")
    print("=" * 60)

    from unittest.mock import patch
    import polars as pl

    fixturePath = ROOT / "tests" / "fixtures" / "005930.finance.parquet"
    financeDf = pl.read_parquet(fixturePath)

    from dartlab.engines.dart.finance.pivot import buildTimeseries as dartBuildTs
    with patch("dartlab.core.dataLoader.loadData", return_value=financeDf):
        dartResult = dartBuildTs("005930")

    if dartResult:
        _, dartPeriods = dartResult
        print(f"  periods ({len(dartPeriods)}개): {dartPeriods[:8]}...")
        print(f"  포맷: YYYY_QN (underscore)")
        print(f"  연도 추출: split('_')[0]")
    else:
        print("  DART 데이터 없음")

    print()
    print("=" * 60)
    print("2. EDGAR period 포맷 샘플")
    print("=" * 60)

    edgarDir = Path(ROOT / "data" / "edgar")
    if edgarDir.exists():
        parquets = list(edgarDir.glob("*.parquet"))
        tickers = [p for p in parquets if p.stem != "tickers"]
        if tickers:
            cik = tickers[0].stem
            from dartlab.engines.edgar.finance.pivot import buildTimeseries as edgarBuildTs
            edgarResult = edgarBuildTs(cik, edgarDir=edgarDir)
            if edgarResult:
                _, edgarPeriods = edgarResult
                print(f"  CIK: {cik}")
                print(f"  periods ({len(edgarPeriods)}개): {edgarPeriods[:8]}...")
                print(f"  포맷: YYYY-QN (hyphen)")
                print(f"  연도 추출: split('-')[0]")
            else:
                print(f"  EDGAR 데이터 없음 (CIK: {cik})")
        else:
            print("  EDGAR parquet 없음 (tickers만 존재)")
    else:
        print("  EDGAR 디렉토리 없음 — 포맷은 코드에서 확인")
        print("  코드 기준: f\"{fy}-{fp}\" → '2024-Q1' 형식")

    print()
    print("=" * 60)
    print("3. period 포맷을 직접 파싱하는 코드 위치")
    print("=" * 60)

    srcDir = ROOT / "src" / "dartlab"
    dartPivot = srcDir / "engines" / "dart" / "finance" / "pivot.py"
    edgarPivot = srcDir / "engines" / "edgar" / "finance" / "pivot.py"

    dartLines = _findFormatDependentLines(dartPivot, "_")
    edgarLines = _findFormatDependentLines(edgarPivot, "-")

    print(f"\n  DART pivot.py — underscore 의존 ({len(dartLines)}개 라인):")
    for lineNo, line in dartLines:
        print(f"    L{lineNo}: {line.strip()}")

    print(f"\n  EDGAR pivot.py — hyphen 의존 ({len(edgarLines)}개 라인):")
    for lineNo, line in edgarLines:
        print(f"    L{lineNo}: {line.strip()}")

    print()
    print("=" * 60)
    print("4. common/ 레이어 — period 포맷 의존성")
    print("=" * 60)

    commonDir = srcDir / "engines" / "common"
    commonFiles = list(commonDir.rglob("*.py"))
    commonDeps = []
    for f in commonFiles:
        lines = _findFormatDependentLines(f, "_")
        lines += _findFormatDependentLines(f, "-")
        if lines:
            commonDeps.extend([(f.name, ln, l) for ln, l in lines])

    if commonDeps:
        print(f"  의존 발견 ({len(commonDeps)}건):")
        for fname, lineNo, line in commonDeps:
            print(f"    {fname} L{lineNo}: {line.strip()}")
    else:
        print("  없음 — common/은 인덱스 기반 접근만 사용")

    print()
    print("=" * 60)
    print("5. annual 비교 시 period 포맷 영향")
    print("=" * 60)

    if dartResult:
        from dartlab.engines.dart.finance.pivot import buildAnnual as dartBuildAnnual
        with patch("dartlab.core.dataLoader.loadData", return_value=financeDf):
            dartAnnual = dartBuildAnnual("005930")
        if dartAnnual:
            _, dartYears = dartAnnual
            print(f"  DART annual years: {dartYears}")
            print(f"  EDGAR annual years: ['2020', '2021', ...] (코드 기준)")
            print(f"  → 연도 문자열은 양쪽 동일 (포맷 무관)")

    print()
    print("=" * 60)
    print("6. 통일 시 변경점 요약")
    print("=" * 60)

    print("""
  옵션 A: DART를 하이픈으로 변경 (YYYY-QN)
    변경 파일: dart/finance/pivot.py
    변경 라인: 2줄 (포맷 생성) + 3줄 (split 파싱)
    장점: ISO-8601에 가까움, 국제 표준
    단점: 기존 사용자 하위호환 깨짐 (period 문자열 비교하는 코드)

  옵션 B: EDGAR를 underscore로 변경 (YYYY_QN)
    변경 파일: edgar/finance/pivot.py
    변경 라인: 1줄 (포맷 생성) + 8줄 (split 파싱)
    단점: 비표준, EDGAR 코드 변경량 더 큼

  옵션 C: 현행 유지 (각자 포맷)
    변경: 없음
    장점: 하위호환 유지
    단점: 분기별 cross-market 비교 시 매번 정규화 필요
    현실: annual 비교만 하면 이미 동일 ("2024" = "2024")

  옵션 D: 표준 포맷 함수 도입 (common/)
    formatPeriod(year, quarter) → "YYYY-QN"
    parsePeriod(periodStr) → (year, quarter)
    양쪽 pivot에서 이 함수 사용 → 포맷 단일 진실의 원천
    """)


def _findFormatDependentLines(
    filepath: Path, separator: str
) -> list[tuple[int, str]]:
    """파일에서 period 포맷에 의존하는 라인을 찾는다."""
    if not filepath.exists():
        return []

    results = []
    with open(filepath, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"""'):
                continue
            if f'split("{separator}")' in line:
                results.append((i, line))
            elif f'f"{{' in line and f"{separator}Q" in line:
                results.append((i, line))
            elif f'"{separator}Q' in line and "endswith" in line:
                results.append((i, line))
    return results


if __name__ == "__main__":
    analyzeFormat()
