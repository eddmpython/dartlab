"""헤더 병합 v5 — 그룹/리프 판별 기반.

핵심 통찰:
  각 헤더 행의 비어있지 않은 셀은 두 종류:
  1. 리프 라벨: 자기 다음 위치에 또 다른 비어있지않은 셀이 있거나, 빈 셀이 0개
  2. 그룹 라벨: 자기 다음 위치부터 빈 셀이 1개 이상 (colspan의 흔적)

  그룹 라벨의 위치에 있는 하위 행의 셀은 그룹의 서브 라벨.
  리프 라벨의 위치에 있는 하위 행의 셀은 colspan 시프트된 것 → 빈 위치로 이동해야 함.

  → 각 위치별로 상위 행이 그룹인지 리프인지 판별하고,
    그룹 위치의 하위 셀은 상위를 대체 (refinement),
    리프 위치의 하위 셀은 빈 위치로 밀어넣기 (shift correction)
"""

import re
from pathlib import Path

import polars as pl

DATA_DIR = Path("data/docsData")
OUT = Path("experiments/002_notes/output")
OUT.mkdir(exist_ok=True)


def extractNotes(df: pl.DataFrame, year: str) -> list[str]:
    notes = df.filter(
        (pl.col("year") == year)
        & pl.col("section_title").str.contains("연결재무제표")
        & pl.col("section_title").str.contains("주석")
    )
    return notes["section_content"].to_list()


def findSegmentSection(contents: list[str]) -> str | None:
    for content in contents:
        lines = content.split("\n")
        startIdx = None
        endIdx = None
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("|"):
                continue
            m = re.match(r"^(\d{1,2})\.\s+(.+)", s)
            if m:
                title = m.group(2).strip()
                if "부문" in title:
                    startIdx = i
                elif startIdx is not None and endIdx is None:
                    endIdx = i
                    break
        if startIdx is not None:
            if endIdx is None:
                endIdx = len(lines)
            return "\n".join(lines[startIdx:endIdx])
    return None


def isDataRow(cells: list[str]) -> bool:
    numCount = 0
    for c in cells[1:]:
        s = c.strip().replace(",", "").replace("(", "").replace(")", "")
        if s and s.replace("-", "").replace(".", "").isdigit():
            numCount += 1
    return numCount >= 1


def isHeaderRow(cells: list[str]) -> bool:
    nonEmpty = [c.strip() for c in cells if c.strip()]
    if len(nonEmpty) < 2:
        return False
    for c in nonEmpty:
        s = c.replace(",", "").replace("(", "").replace(")", "").replace("-", "")
        if s.isdigit():
            return False
    return True


def parseCells(line: str) -> list[str]:
    cells = [c.strip() for c in line.split("|")]
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


# ── V5 병합 전략 ──────────────────────────────────────────


def classifyCells(row: list[str]) -> list[str]:
    """각 위치를 'group' / 'leaf' / 'empty'로 분류.

    비어있지 않은 셀 다음에 빈 셀이 있으면 그룹 (colspan 흔적),
    다음에 비어있지 않은 셀이 있거나 행 끝이면 리프.
    """
    result = []
    for i, cell in enumerate(row):
        if not cell:
            result.append("empty")
        else:
            # 다음 위치가 비어있는가?
            nextEmpty = False
            if i + 1 < len(row) and not row[i + 1]:
                nextEmpty = True
            result.append("group" if nextEmpty else "leaf")
    return result


def mergeHeadersV5(headers: list[list[str]]) -> list[str]:
    """멀티행 헤더를 그룹/리프 판별 기반으로 병합.

    알고리즘:
    1) 첫 행을 기준으로 시작
    2) 각 하위 행에 대해:
       a) 현재 merged의 각 위치를 group/leaf/empty 분류
       b) 하위 행의 비어있지 않은 셀을 순서대로 처리:
          - 현재 위치가 group → 이 셀은 그룹의 서브라벨이므로 밀어넣기 대상
          - 현재 위치가 leaf → 이미 의미 있는 라벨이 있으므로 이 셀도 밀어넣기
          - 밀어넣기 대상들은 merged의 빈 위치에 왼쪽부터 삽입
       c) 하위 행의 비어있지 않은 셀 중 위치가 group인 곳의 셀은 group 대체
    """
    if len(headers) == 1:
        return list(headers[0])

    maxLen = max(len(h) for h in headers)
    padded = [h + [""] * (maxLen - len(h)) for h in headers]

    merged = list(padded[0])

    for h in padded[1:]:
        types = classifyCells(merged)
        displaced = []  # 밀어넣기할 셀들

        for i, cell in enumerate(h):
            if not cell:
                continue
            if types[i] == "group":
                # 그룹 위치 → 하위 셀로 대체 (refinement)
                merged[i] = cell
            elif types[i] == "leaf":
                # 리프 위치 → 이미 리프가 있으므로 이 셀은 shift된 것
                displaced.append(cell)
            else:
                # 빈 위치 → 직접 삽입
                merged[i] = cell

        # displaced 셀들을 남은 빈 위치에 삽입
        emptyIdx = [i for i, cell in enumerate(merged) if not cell]
        for i, idx in enumerate(emptyIdx):
            if i < len(displaced):
                merged[idx] = displaced[i]

    return merged


def analyzeTableBlocks(text: str) -> list[dict]:
    lines = text.split("\n")
    blocks = []
    currentPeriod = ""
    pendingHeaders: list[list[str]] = []
    dataRows: list[tuple[str, list[str]]] = []
    hasData = False

    def flush():
        nonlocal pendingHeaders, dataRows, hasData
        if pendingHeaders and dataRows:
            blocks.append({
                "period": currentPeriod,
                "headers": list(pendingHeaders),
                "dataRows": list(dataRows),
            })
        pendingHeaders = []
        dataRows = []
        hasData = False

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            if not s:
                continue
            if "당기" in s or "전기" in s:
                flush()
                currentPeriod = "당기" if "당기" in s else "전기"
            elif hasData:
                flush()
            continue

        cells = parseCells(s)
        if all(re.match(r"^-+$", c) for c in cells if c):
            continue
        nonEmpty = [c for c in cells if c]
        if not nonEmpty:
            flush()
            continue
        if len(nonEmpty) == 1 and "단위" in nonEmpty[0]:
            continue
        if len(nonEmpty) <= 2 and any("당기" in c or "전기" in c for c in nonEmpty):
            flush()
            for c in nonEmpty:
                if "당기" in c:
                    currentPeriod = "당기"
                elif "전기" in c:
                    currentPeriod = "전기"
            continue
        if len(nonEmpty) == 1 and len(nonEmpty[0]) > 20:
            continue

        if isDataRow(cells):
            name = cells[0].strip()
            if not name:
                continue
            cleanName = re.sub(r"\(\*\d*\)", "", name).strip()
            if not cleanName or cleanName.startswith("("):
                continue
            hasData = True
            dataRows.append((cleanName, cells))
        elif isHeaderRow(cells):
            if not hasData:
                pendingHeaders.append(cells)

    flush()
    return blocks


def main():
    path = DATA_DIR / "005930.parquet"
    df = pl.read_parquet(str(path))
    years = sorted(df["year"].unique().to_list(), reverse=True)

    out = []

    def p(s=""):
        out.append(s)

    p("=" * 80)
    p("V5 그룹/리프 판별 기반 병합")
    p("=" * 80)

    allGood = True
    total = 0
    ok = 0

    for year in years[:10]:
        contents = extractNotes(df, year)
        if not contents:
            continue
        segment = findSegmentSection(contents)
        if segment is None:
            continue

        blocks = analyzeTableBlocks(segment)

        for bi, block in enumerate(blocks):
            merged = mergeHeadersV5(block["headers"])
            dataLen = len(block["dataRows"][0][1]) if block["dataRows"] else 0
            nHeaders = len(block["headers"])
            total += 1

            match = len(merged) == dataLen
            if match:
                ok += 1
            else:
                allGood = False

            mark = "OK" if match else "FAIL"
            p(f"\n  {year} Block{bi} [{block['period']}] HDR={nHeaders} merged={len(merged)} data={dataLen} [{mark}]")

            # 상세 출력 (멀티헤더 또는 실패)
            if nHeaders >= 2 or not match:
                types0 = classifyCells(padded0 := block["headers"][0] + [""] * (max(len(h) for h in block["headers"]) - len(block["headers"][0])))
                for hi, h in enumerate(block["headers"]):
                    p(f"    HDR{hi}: {h}")
                p(f"    TYPE0: {types0}")
                p(f"    MERGED: {merged}")
                if block["dataRows"]:
                    name, cells = block["dataRows"][0]
                    p(f"    DATA:   {cells}")
                    # 매핑
                    p(f"    매핑:")
                    for i in range(min(len(merged), len(cells))):
                        label = merged[i] or "(empty)"
                        val = cells[i]
                        p(f"      [{i}] {label} = {val}")

    p(f"\n{'=' * 40}")
    p(f"  전체: {ok}/{total} OK {'(ALL OK)' if allGood else '(SOME FAILED)'}")
    p(f"{'=' * 40}")

    outPath = OUT / "header_merge_v5.txt"
    outPath.write_text("\n".join(out), encoding="utf-8")
    print(f"결과 저장: {outPath}")
    print(f"전체: {ok}/{total} OK {'(ALL OK)' if allGood else '(SOME FAILED)'}")


if __name__ == "__main__":
    main()
