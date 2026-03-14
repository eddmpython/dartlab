"""
실험 ID: 060-003
실험명: sections DataFrame 위에서 기간간 diff 가능성 검증

목적:
- sections 수평화 DataFrame(topic × period)만으로 기간간 텍스트 변화 감지
- 개별 파서 호출 없이 diff가 가능한지 확인
- diff 연산 속도 측정

가설:
1. sections DataFrame의 인접 기간 셀을 비교하면 텍스트 변화 감지 가능
2. diff 연산은 수백ms 이내 (sections 로드 0.7초 + diff 0.3초 = 총 1초)
3. 변화율(changed periods / total periods)로 topic별 안정성 파악 가능

방법:
1. c.docs.sections 로드
2. 각 topic의 인접 기간 텍스트 비교 (hash 기반 빠른 비교)
3. 변화가 있는 지점 목록 생성
4. topic별 변화율 계산

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-14
"""

import hashlib
import time
import sys
sys.path.insert(0, "src")


def computeDiff(sections):
    """sections DataFrame에서 기간간 변화 감지."""
    periodCols = [col for col in sections.columns if col != "topic"]
    if len(periodCols) < 2:
        return []

    changes = []
    for row in sections.iter_rows(named=True):
        topic = row["topic"]
        prevHash = None
        prevPeriod = None
        topicChanges = 0
        topicPeriods = 0

        for period in periodCols:
            text = row.get(period)
            if text is None:
                continue
            topicPeriods += 1
            curHash = hashlib.md5(str(text).encode()).hexdigest()[:8]

            if prevHash is not None and curHash != prevHash:
                topicChanges += 1
                changes.append({
                    "topic": topic,
                    "from": prevPeriod,
                    "to": period,
                    "prevLen": len(str(row.get(prevPeriod, ""))),
                    "curLen": len(str(text)),
                })

            prevHash = curHash
            prevPeriod = period

        if topicPeriods > 1:
            changes.append({
                "topic": topic,
                "from": "__summary__",
                "to": "__summary__",
                "prevLen": topicChanges,
                "curLen": topicPeriods,
            })

    return changes


def main():
    from dartlab.engines.dart.company import Company
    import polars as pl

    c = Company("005930")

    t0 = time.perf_counter()
    sec = c.docs.sections
    t1 = time.perf_counter()
    print(f"sections 로드: {t1 - t0:.3f}s  shape={sec.shape}")

    t2 = time.perf_counter()
    changes = computeDiff(sec)
    t3 = time.perf_counter()
    print(f"diff 연산: {t3 - t2:.3f}s")
    print(f"총 소요: {t3 - t0:.3f}s")

    summaries = [c for c in changes if c["from"] == "__summary__"]
    details = [c for c in changes if c["from"] != "__summary__"]

    print(f"\ntopic {len(summaries)}개, 변화 지점 {len(details)}개")

    print(f"\n{'topic':<40} {'changes':>8} {'periods':>8} {'rate':>8}")
    print("=" * 70)
    summaries.sort(key=lambda x: x["prevLen"] / max(x["curLen"], 1), reverse=True)
    for s in summaries[:20]:
        rate = s["prevLen"] / max(s["curLen"], 1) * 100
        bar = "#" * int(rate / 5)
        print(f"{s['topic']:<40} {s['prevLen']:>8} {s['curLen']:>8} {rate:>7.1f}% {bar}")

    print(f"\n... (총 {len(summaries)}개 topic)")

    print(f"\n가장 자주 변하는 topic Top 10:")
    print("-" * 70)
    for s in summaries[:10]:
        topic = s["topic"]
        topicDetails = [d for d in details if d["topic"] == topic]
        print(f"\n  {topic} ({s['prevLen']}회 변화 / {s['curLen']}개 기간)")
        for d in topicDetails[:5]:
            lenDiff = d["curLen"] - d["prevLen"]
            sign = "+" if lenDiff > 0 else ""
            print(f"    {d['from']} → {d['to']}: {d['prevLen']:,}자 → {d['curLen']:,}자 ({sign}{lenDiff:,})")

    print(f"\n\n안정적인 topic (변화 없음):")
    stable = [s for s in summaries if s["prevLen"] == 0]
    print(f"  {len(stable)}개: {[s['topic'] for s in stable[:10]]}")


if __name__ == "__main__":
    main()
