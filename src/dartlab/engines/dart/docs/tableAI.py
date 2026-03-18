"""AI 기반 마크다운 테이블 → 구조화 DataFrame 변환.

raw_markdown 블록(수평화 실패한 마크다운 테이블)을
AI를 활용하여 항목×기간 매트릭스로 변환한다.

흐름:
1. 최신 기간의 마크다운 테이블을 AI에게 전달
2. AI가 JSON 형태로 구조화 (행: 항목명, 열: 헤더)
3. 기수→연도 매핑을 AI가 같이 반환
4. 결과를 캐시하여 재요청 시 즉시 반환

비용: gpt-4o-mini 기준 테이블 1개 ~$0.0001
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


_CACHE_DIR = Path.home() / ".dartlab" / "cache" / "table_parse"

_PARSE_PROMPT = """아래는 한국 기업 사업보고서의 마크다운 테이블입니다.
이 테이블을 JSON으로 변환해주세요.

규칙:
1. 헤더에서 "제XX기", "제XX기 반기", "제XX기 3분기" 등의 기수 표현을 찾아주세요
2. 각 데이터 행을 JSON 객체로 변환하세요
3. 숫자에서 쉼표를 제거하고 정수로 변환하세요
4. 빈 셀은 null로 처리하세요

반환 형식 (JSON만, 다른 텍스트 없이):
{
  "headers": ["부문", "매출유형", "품목", "당기", "전기", "전전기"],
  "kisuMap": {"제57기 3분기": "2025Q3", "제56기": "2024", "제55기": "2023"},
  "rows": [
    {"부문": "DX", "매출유형": "제품", "품목": "TV 등", "당기": 1436625, "전기": 1748877, "전전기": 1699923},
    ...
  ],
  "unit": "억원"
}

마크다운 테이블:
"""


async def parseRawMarkdownBlock(
    rawMarkdown: dict[str, str],
    topic: str,
    blockIdx: int,
) -> dict[str, Any]:
    """raw_markdown 블록을 AI로 파싱.

    현재는 마크다운 테이블의 구조를 직접 파싱하는 규칙 기반 방식을 먼저 시도하고,
    실패 시 AI fallback (향후).
    """
    # 최신 기간의 마크다운
    periods = sorted(rawMarkdown.keys())
    if not periods:
        return {"error": "빈 데이터"}

    latestPeriod = periods[-1]
    latestMd = rawMarkdown[latestPeriod]

    # 1차: 규칙 기반 파싱 시도
    parsed = _parseMarkdownTable(latestMd, latestPeriod)
    if parsed is not None:
        return {
            "method": "rule",
            "period": latestPeriod,
            **parsed,
        }

    # 2차: AI 파싱 (향후 구현)
    return {
        "method": "pending",
        "period": latestPeriod,
        "message": "AI 파싱 준비 중",
        "preview": latestMd[:500],
    }


def _parseMarkdownTable(md: str, period: str) -> dict[str, Any] | None:
    """마크다운 테이블을 규칙 기반으로 파싱."""
    lines = md.strip().split("\n")
    if len(lines) < 3:
        return None

    # 단위 추출
    unit = None
    unitMatch = re.search(r"단위\s*[:\s]*([^\)）\]]+)", lines[0])
    if unitMatch:
        unit = unitMatch.group(1).strip()

    # 헤더/separator/데이터 분리
    headerLine = None
    sepLine = None
    dataLines = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]

        # separator 감지
        if all(set(c.strip()) <= {"-", ":", " "} for c in cells if c.strip()):
            sepLine = i
            # separator 바로 위가 헤더
            for j in range(i - 1, -1, -1):
                prevStripped = lines[j].strip()
                if prevStripped.startswith("|"):
                    prevCells = [c.strip() for c in prevStripped.strip("|").split("|")]
                    if not all(set(c.strip()) <= {"-", ":", " "} for c in prevCells if c.strip()):
                        headerLine = prevCells
                        break
            continue

        if sepLine is not None and headerLine is not None:
            dataLines.append(cells)

    if headerLine is None or not dataLines:
        return None

    # 빈 헤더 병합 (단위행 스킵)
    headers = [h for h in headerLine if h]

    # 데이터 행 → dict
    rows = []
    for cells in dataLines:
        # 셀 수를 헤더에 맞춤
        while len(cells) < len(headers):
            cells.append("")
        row = {}
        for hi, h in enumerate(headers):
            val = cells[hi] if hi < len(cells) else ""
            # 숫자 변환
            cleaned = val.replace(",", "").strip()
            try:
                row[h] = int(cleaned)
            except ValueError:
                try:
                    row[h] = float(cleaned)
                except ValueError:
                    row[h] = val if val else None
        rows.append(row)

    if not rows:
        return None

    return {
        "headers": headers,
        "rows": rows,
        "unit": unit,
        "rowCount": len(rows),
    }
