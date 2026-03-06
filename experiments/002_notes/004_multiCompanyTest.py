"""다수 기업 세그먼트 파싱 검증.

002_segmentParse.py의 개선된 mergeHeaders를 적용하여
9개 기업에서 파싱 결과를 확인한다.
"""

import sys
from pathlib import Path

# 002_segmentParse 모듈 임포트
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib
sp = importlib.import_module("002_segmentParse")

DATA_DIR = Path("data/docsData")
OUT = Path("experiments/002_notes/output")
OUT.mkdir(exist_ok=True)

COMPANIES = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("005380", "현대차"),
    ("066570", "LG전자"),
    ("035420", "네이버"),
    ("035720", "카카오"),
    ("005490", "POSCO홀딩스"),
    ("006400", "삼성SDI"),
    ("373220", "LG에너지솔루션"),
]


def main():
    import polars as pl

    out = []

    def p(s=""):
        out.append(s)

    p("=" * 80)
    p("다수 기업 세그먼트 파싱 검증")
    p("=" * 80)

    summary = []

    for code, name in COMPANIES:
        path = DATA_DIR / f"{code}.parquet"
        if not path.exists():
            p(f"\n  {name}({code}): 데이터 없음")
            continue

        df = pl.read_parquet(str(path))
        years = sorted(df["year"].unique().to_list(), reverse=True)

        p(f"\n{'=' * 60}")
        p(f"  {name} ({code})")
        p(f"{'=' * 60}")

        alignedCount = 0
        misalignedCount = 0

        for year in years[:5]:  # 최근 5년
            contents = sp.extractNotes(df, year)
            if not contents:
                continue

            segment = sp.findSegmentSection(contents)
            if segment is None:
                continue

            tables = sp.parseSegmentTables(segment)

            for t in tables:
                flag = "" if t["aligned"] else " [MISALIGNED]"
                if t["aligned"]:
                    alignedCount += 1
                else:
                    misalignedCount += 1

                p(f"\n  {year} [{t['period']}] {t['type']}{flag}")
                p(f"    columns({len(t['columns'])}): {t['columns']}")
                for rname in t["order"]:
                    vals = t["rows"][rname]
                    p(f"      {rname}({len(vals)}): {vals[:3]}{'...' if len(vals) > 3 else ''}")

        total = alignedCount + misalignedCount
        rate = alignedCount / total * 100 if total > 0 else 0
        summary.append((name, code, alignedCount, misalignedCount, total, rate))

    p(f"\n\n{'=' * 80}")
    p("요약")
    p("=" * 80)
    p(f"{'기업':<15} {'aligned':>8} {'misaligned':>10} {'total':>6} {'rate':>8}")
    p("-" * 50)
    for name, code, a, m, t, r in summary:
        p(f"{name:<15} {a:>8} {m:>10} {t:>6} {r:>7.1f}%")

    totalA = sum(s[2] for s in summary)
    totalM = sum(s[3] for s in summary)
    totalT = totalA + totalM
    totalR = totalA / totalT * 100 if totalT > 0 else 0
    p("-" * 50)
    p(f"{'전체':<15} {totalA:>8} {totalM:>10} {totalT:>6} {totalR:>7.1f}%")

    outPath = OUT / "multi_company_test.txt"
    outPath.write_text("\n".join(out), encoding="utf-8")
    print(f"결과 저장: {outPath}")
    print(f"전체: {totalA}/{totalT} aligned ({totalR:.1f}%)")


if __name__ == "__main__":
    main()
