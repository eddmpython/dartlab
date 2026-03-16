"""실험 ID: 063-007
실험명: 다종목 헤더 매칭 검증

목적:
- 006에서 삼성전자 단일 종목으로 헤더 기반 매칭 가능성 확인
- 다종목에서도 같은 헤더 패턴이 반복되는지 확인
- 전 종목 공통 테이블 타입 도출

가설:
1. 주요 topic의 100% 매칭 헤더는 다종목에서도 80%+ 종목이 동일 헤더 보유
2. 상위 20개 헤더 타입으로 전체 테이블의 60%+ 커버 가능

방법:
1. 전 종목 sections의 table 셀에서 서브테이블 분리
2. 각 서브테이블 헤더 정규화
3. (topic, 정규화헤더) 빈도 집계
4. 종목 간 일치율 계산

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-16
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl
from dartlab.engines.dart.docs.sections.pipeline import sections
from dartlab.core.dataLoader import _dataDir


def splitSubtables(md: str) -> list[list[str]]:
    tables: list[list[str]] = []
    current: list[str] = []
    for line in md.strip().split("\n"):
        stripped = line.strip()
        if not stripped.startswith("|"):
            if current:
                tables.append(current)
                current = []
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())
        if isSep and current:
            if len(current) >= 2:
                prev = current[:-1]
                if prev:
                    tables.append(prev)
                current = [current[-1], stripped]
            else:
                current.append(stripped)
        else:
            current.append(stripped)
    if current:
        tables.append(current)
    return tables


def subtableHeader(lines: list[str]) -> str:
    for line in lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())
        if not isSep:
            return " | ".join(c.strip() for c in cells if c.strip())
    return ""


def normalizeHeader(header: str) -> str:
    h = re.sub(r"\d{4}(Q\d)?", "", header)
    h = re.sub(r"제\s*\d+\s*기", "", h)
    h = re.sub(r"\(\s*단위\s*:\s*[^)]+\)", "", h)
    h = re.sub(r"\(\s*기준일\s*:?[^)]*\)", "", h)
    h = re.sub(r"기준일\s*:?[^|]*", "", h)
    h = re.sub(r"\d+\.\d+\.\d+", "", h)
    h = re.sub(r"\s+", " ", h).strip()
    return h


if __name__ == "__main__":
    docsDir = _dataDir("docs")
    codes = sorted(p.stem for p in docsDir.glob("*.parquet"))
    print(f"전체 종목: {len(codes)}")

    skipTopics = {"consolidatedNotes", "financialNotes", "fsSummary"}

    # (topic, normHeader) → 보유 종목 수
    headerStockCount: Counter[tuple[str, str]] = Counter()
    # (topic, normHeader) → 전체 등장 수 (기간 포함)
    headerTotalCount: Counter[tuple[str, str]] = Counter()
    # topic → 종목 수
    topicStockCount: Counter[str] = Counter()

    errors = 0
    processed = 0

    for i, code in enumerate(codes):
        try:
            sec = sections(code)
            if sec is None or "blockType" not in sec.columns:
                continue

            tables = sec.filter(pl.col("blockType") == "table")
            if tables.is_empty():
                continue

            processed += 1
            periods = [c for c in tables.columns if c not in {"chapter", "topic", "blockType"}]
            latestPeriod = periods[-1] if periods else None
            if not latestPeriod:
                continue

            stockHeaders: set[tuple[str, str]] = set()

            for row in tables.iter_rows(named=True):
                topic = row["topic"]
                if topic in skipTopics:
                    continue
                topicStockCount[topic] += 1

                content = row.get(latestPeriod)
                if content is None:
                    continue

                subs = splitSubtables(str(content))
                for sub in subs:
                    header = normalizeHeader(subtableHeader(sub))
                    if not header or len(header) < 3:
                        continue
                    key = (topic, header)
                    headerTotalCount[key] += 1
                    stockHeaders.add(key)

            for key in stockHeaders:
                headerStockCount[key] += 1

        except (KeyError, ValueError, TypeError) as e:
            errors += 1
            if errors <= 3:
                print(f"  ERROR {code}: {e}")

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(codes)} 처리됨 (에러: {errors})")

    print(f"\n처리: {processed}/{len(codes)} (에러: {errors})")
    print(f"고유 (topic, header): {len(headerStockCount)}")

    # 종목 보유율 상위 50
    print("\n=== 종목 보유율 상위 50 (topic | header | 보유종목수/전체) ===")
    for (topic, header), count in headerStockCount.most_common(50):
        topicTotal = topicStockCount[topic]
        pct = count / topicTotal * 100 if topicTotal else 0
        print(f"  [{count:3d}/{topicTotal:3d} {pct:5.1f}%] {topic:30s} | {header[:60]}")

    # topic별 가장 보편적인 헤더
    print("\n=== topic별 최다 보유 헤더 (상위 20 topic) ===")
    topTopics = topicStockCount.most_common(20)
    for topic, stockCount in topTopics:
        # 이 topic의 헤더 중 가장 많은 종목이 보유한 것
        topHeaders = [
            (h, c) for (t, h), c in headerStockCount.items()
            if t == topic
        ]
        topHeaders.sort(key=lambda x: -x[1])
        best = topHeaders[0] if topHeaders else ("", 0)
        pct = best[1] / stockCount * 100 if stockCount else 0
        print(f"  {topic:30s} [{best[1]:3d}/{stockCount:3d} {pct:5.1f}%] {best[0][:50]}")
