"""실험 ID: 063-001
실험명: 전종목 테이블 헤더 패턴 수집

목적:
- sections의 blockType=table인 행에서 테이블 헤더(첫 행) 패턴을 전종목 수집
- 빈도 높은 공통 테이블 패턴을 식별하여 독립 topic명 후보 도출
- finance accountMappings.json과 동일한 학습 방식의 기초 데이터

가설:
1. 전종목에 걸쳐 반복되는 테이블 헤더 패턴이 100개 이내로 수렴한다
2. 상위 30개 패턴이 전체 테이블의 80%+ 를 커버한다

방법:
1. 전종목 sections() 호출
2. blockType=table인 행의 content에서 첫 번째 헤더 행 추출
3. 헤더 패턴을 정규화 (공백 제거, 정렬)
4. (원본 topic, 정규화 헤더, 빈도) 집계

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-14
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

# dartlab import
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab.core.dataLoader import _dataDir
from dartlab.providers.dart.docs.sections.pipeline import sections


def listAvailableStockCodes() -> list[str]:
    """로컬 docs 데이터에서 종목코드 목록 추출."""
    docsDir = _dataDir("docs")
    return sorted(p.stem for p in docsDir.glob("*.parquet"))


def extractTableHeader(content: str) -> str | None:
    """테이블 content에서 첫 번째 헤더 행(| col1 | col2 | ...) 추출."""
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("|") and "---" not in stripped:
            # 정규화: 양쪽 |  제거, 셀별 strip, 정렬
            cells = [c.strip() for c in stripped.split("|") if c.strip()]
            return " | ".join(cells)
    return None


def normalizeHeader(header: str) -> str:
    """헤더 정규화 — 숫자/연도 제거, 공백 통일."""
    import re
    # 연도/분기 패턴 제거 (2024, 2023Q1, 제XX기 등)
    header = re.sub(r"\d{4}(Q\d)?", "", header)
    header = re.sub(r"제\s*\d+\s*기", "", header)
    header = re.sub(r"\(\s*단위\s*:\s*[^)]+\)", "", header)
    header = re.sub(r"\s+", " ", header).strip()
    return header


if __name__ == "__main__":
    codes = listAvailableStockCodes()
    print(f"전체 종목 수: {len(codes)}")

    # (원본topic, 정규화헤더) → 빈도
    headerCounter: Counter[tuple[str, str]] = Counter()
    # 정규화헤더만의 빈도
    rawHeaderCounter: Counter[str] = Counter()
    # topic별 테이블 수
    topicTableCount: Counter[str] = Counter()

    errors = 0
    processed = 0

    for i, code in enumerate(codes):
        try:
            s = sections(code)
            if s is None:
                continue
            if "blockType" not in s.columns:
                continue
            tables = s.filter(s["blockType"] == "table")
            if tables.is_empty():
                continue

            processed += 1
            # 최신 기간의 content만 사용 (첫 번째 period 컬럼)
            periodCols = [c for c in tables.columns if c not in {"chapter", "topic", "blockType"}]
            if not periodCols:
                continue

            latestPeriod = periodCols[0]  # 이미 최신순 정렬

            for row in tables.iter_rows(named=True):
                topic = row["topic"]
                content = row.get(latestPeriod)
                if content is None:
                    continue
                header = extractTableHeader(str(content))
                if header is None:
                    continue
                normalized = normalizeHeader(header)
                if not normalized:
                    continue
                headerCounter[(topic, normalized)] += 1
                rawHeaderCounter[normalized] += 1
                topicTableCount[topic] += 1

        except (KeyError, ValueError, TypeError) as e:
            errors += 1
            if errors <= 5:
                print(f"  ERROR {code}: {e}")

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(codes)} 처리됨 (에러: {errors})")

    print(f"\n처리 완료: {processed}/{len(codes)} (에러: {errors})")
    print(f"고유 정규화 헤더 수: {len(rawHeaderCounter)}")
    print(f"고유 (topic, 헤더) 조합 수: {len(headerCounter)}")

    print("\n=== 상위 50 정규화 헤더 (빈도순) ===")
    for header, count in rawHeaderCounter.most_common(50):
        print(f"  [{count:4d}] {header}")

    print("\n=== topic별 테이블 수 (상위 30) ===")
    for topic, count in topicTableCount.most_common(30):
        print(f"  [{count:4d}] {topic}")

    # 커버리지 계산
    total = sum(rawHeaderCounter.values())
    cumulative = 0
    for i, (_, count) in enumerate(rawHeaderCounter.most_common()):
        cumulative += count
        if cumulative >= total * 0.8:
            print(f"\n80% 커버리지: 상위 {i+1}개 헤더")
            break
