"""실험 ID: 063-002
실험명: topic별 테이블 헤더 패턴 분석

목적:
- 각 topic에 속한 테이블의 헤더 패턴을 분류
- 하나의 topic 안에 서로 다른 의미의 테이블이 몇 개인지 확인
- 독립 topic명 후보 결정

가설:
1. 대부분의 topic은 테이블 1~3종류로 수렴한다
2. topic 내 테이블의 의미가 다르면 독립 topic으로 분리 가능

방법:
1. 상위 15개 topic에 대해 테이블 헤더 상세 분석
2. 각 topic 내 테이블이 몇 종류인지, 어떤 의미인지 분류

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-14
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab.core.dataLoader import _dataDir
from dartlab.providers.dart.docs.sections.pipeline import sections


def listCodes() -> list[str]:
    docsDir = _dataDir("docs")
    return sorted(p.stem for p in docsDir.glob("*.parquet"))


def extractAllHeaders(content: str) -> list[str]:
    """테이블에서 헤더 행(--- 직전의 | 행)과 독립 테이블의 첫 행을 모두 추출."""
    lines = content.split("\n")
    headers = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if "---" in stripped:
            continue
        # 이 행이 헤더인지: 다음 행이 --- 구분자이거나, 이전 행이 비어있거나 | 아닌 행
        isHeader = False
        if i + 1 < len(lines) and "---" in lines[i + 1]:
            isHeader = True
        elif i == 0 or not lines[i - 1].strip().startswith("|"):
            isHeader = True
        if isHeader:
            cells = [c.strip() for c in stripped.split("|") if c.strip()]
            # 연도/기준일 등 노이즈 제거
            cleaned = []
            for c in cells:
                c2 = re.sub(r"\d{4}(Q\d)?", "", c)
                c2 = re.sub(r"제\s*\d+\s*기", "", c2)
                c2 = re.sub(r"\(\s*단위\s*:\s*[^)]+\)", "", c2)
                c2 = c2.strip()
                if c2 and c2 != "---":
                    cleaned.append(c2)
            if cleaned:
                headers.append(" | ".join(cleaned))
    return headers


TARGET_TOPICS = [
    "companyOverview", "businessOverview", "productService",
    "financialStatements", "employee", "audit", "majorHolder",
    "dividend", "shareCapital", "boardOfDirectors",
    "executivePay", "stockPriceTrend", "subsidiaryDetail",
    "companyHistory", "rawMaterial",
]

if __name__ == "__main__":
    codes = listCodes()
    print(f"종목 수: {len(codes)}")

    # topic → {헤더패턴: 빈도}
    topicHeaders: dict[str, Counter[str]] = defaultdict(Counter)

    for i, code in enumerate(codes):
        try:
            s = sections(code)
            if s is None or "blockType" not in s.columns:
                continue
            tables = s.filter(s["blockType"] == "table")
            if tables.is_empty():
                continue

            periodCols = [c for c in tables.columns if c not in {"chapter", "topic", "blockType"}]
            if not periodCols:
                continue
            latestPeriod = periodCols[0]

            for row in tables.iter_rows(named=True):
                topic = row["topic"]
                if topic not in TARGET_TOPICS:
                    continue
                content = row.get(latestPeriod)
                if not content:
                    continue
                for header in extractAllHeaders(str(content)):
                    topicHeaders[topic][header] += 1
        except (KeyError, ValueError, TypeError):
            pass

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(codes)}")

    print("\n" + "=" * 80)
    for topic in TARGET_TOPICS:
        headers = topicHeaders.get(topic)
        if not headers:
            print(f"\n### {topic}: 테이블 없음")
            continue
        print(f"\n### {topic}: 고유 헤더 {len(headers)}종")
        for header, count in headers.most_common(10):
            print(f"  [{count:3d}] {header}")
