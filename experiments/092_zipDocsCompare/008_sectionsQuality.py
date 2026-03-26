"""실험 ID: 008
실험명: collector vs ZIP content 질적 비교 (sections 입력 품질)

목적:
- collector.parquet / zip.parquet의 section_content를 직접 비교
- sections 파이프라인에 들어가는 원본 텍스트 품질 자체를 판정
- topic 매핑, 블록 분해(_splitContentBlocks), heading 구조 파싱 결과 비교

가설:
1. 소분류(SECTION-2) content는 ZIP이 collector와 동등하거나 더 나을 것이다
2. 대분류(SECTION-1) content 0자는 sections 품질에 영향을 줄 수 있다
3. table markdown 변환 품질은 동일할 것이다 (같은 _tableToMarkdown 로직)

방법:
1. 동일 section_title 행끼리 매칭
2. content 길이, 텍스트/테이블 블록 수, heading 구조 비교
3. 실제 content 샘플 나란히 비교

결과 (실험 후 작성):
- (실행 후 채울 것)

결론:
- (실행 후 채울 것)

실험일: 2026-03-24
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path

import polars as pl

from dartlab.providers.dart.docs.sections.mapper import mapSectionTitle
from dartlab.providers.dart.docs.sections.pipeline import _splitContentBlocks

TEMP_DIR = Path(__file__).parent / "temp"


def _normalizeTitle(t: str) -> str:
    return re.sub(r"\s+", "", t).strip()


def _countBlocks(content: str) -> dict:
    """content → text/table 블록 통계."""
    if not content:
        return {"textBlocks": 0, "tableBlocks": 0, "textChars": 0, "tableChars": 0, "headings": 0}
    blocks = _splitContentBlocks(content)
    textBlocks = [b for b in blocks if b[0] == "text"]
    tableBlocks = [b for b in blocks if b[0] == "table"]
    textChars = sum(len(b[1]) for b in textBlocks)
    tableChars = sum(len(b[1]) for b in tableBlocks)

    # heading 수 (가. 나. 다. / 1. 2. 3. / (1) (2) 등)
    headingPattern = re.compile(r"^(?:[가-힣]\.|[0-9]+\.\s|\([0-9]+\)\s|[①-⑳])", re.MULTILINE)
    headings = len(headingPattern.findall(content))

    return {
        "textBlocks": len(textBlocks),
        "tableBlocks": len(tableBlocks),
        "textChars": textChars,
        "tableChars": tableChars,
        "headings": headings,
    }


def main():
    collPath = TEMP_DIR / "collector.parquet"
    zipPath = TEMP_DIR / "zip.parquet"

    if not collPath.exists() or not zipPath.exists():
        print("temp/ 파일 없음. 007 먼저 실행")
        return

    collDf = pl.read_parquet(collPath)
    zipDf = pl.read_parquet(zipPath)

    print("=" * 100)
    print("collector vs ZIP — section_content 질적 비교")
    print("=" * 100)

    # title 정규화해서 매칭
    collRows = list(collDf.iter_rows(named=True))
    zipRows = list(zipDf.iter_rows(named=True))

    collByTitle = {}
    for r in collRows:
        key = _normalizeTitle(r["section_title"])
        collByTitle[key] = r

    zipByTitle = {}
    for r in zipRows:
        key = _normalizeTitle(r["section_title"])
        zipByTitle[key] = r

    matched = []
    for key in collByTitle:
        if key in zipByTitle:
            matched.append(key)

    # ── 1. 매칭된 섹션별 content 비교 ──
    print(f"\n매칭된 섹션: {len(matched)}개 (collector {len(collRows)}, ZIP {len(zipRows)})")

    print(f"\n{'섹션 제목':35s} | {'topic':25s} | {'coll':>7s} {'zip':>7s} {'유사도':>5s} | {'cTxt':>3s} {'cTbl':>3s} {'zTxt':>3s} {'zTbl':>3s} | 판정")
    print("-" * 130)

    totalSim = 0
    simCount = 0
    zipWins = 0
    collWins = 0
    ties = 0

    for key in matched:
        cr = collByTitle[key]
        zr = zipByTitle[key]

        cContent = cr["section_content"] or ""
        zContent = zr["section_content"] or ""
        cLen = len(cContent)
        zLen = len(zContent)

        # topic 매핑
        topic = mapSectionTitle(cr["section_title"])

        # 유사도
        if cLen > 0 and zLen > 0:
            sim = SequenceMatcher(None, cContent[:3000], zContent[:3000]).ratio()
            totalSim += sim
            simCount += 1
        elif cLen == 0 and zLen == 0:
            sim = 1.0
            totalSim += sim
            simCount += 1
        else:
            sim = 0.0
            simCount += 1

        # 블록 분석
        cStats = _countBlocks(cContent)
        zStats = _countBlocks(zContent)

        # 판정
        if abs(cLen - zLen) < 50:
            verdict = "동등"
            ties += 1
        elif cLen > zLen and zLen == 0:
            verdict = "coll>>(ZIP 0자)"
            collWins += 1
        elif zLen > cLen and cLen == 0:
            verdict = "ZIP>>(coll 0자)"
            zipWins += 1
        elif cLen > zLen:
            verdict = f"coll+{cLen - zLen}"
            collWins += 1
        else:
            verdict = f"ZIP+{zLen - cLen}"
            zipWins += 1

        title = cr["section_title"][:35]
        print(
            f"{title:35s} | {topic[:25]:25s} | "
            f"{cLen:>7,} {zLen:>7,} {sim:>5.1%} | "
            f"{cStats['textBlocks']:>3d} {cStats['tableBlocks']:>3d} "
            f"{zStats['textBlocks']:>3d} {zStats['tableBlocks']:>3d} | {verdict}"
        )

    avgSim = totalSim / simCount if simCount else 0
    print(f"\n평균 유사도: {avgSim:.1%}")
    print(f"collector 우위: {collWins}, ZIP 우위: {zipWins}, 동등: {ties}")

    # ── 2. 대분류 content 상세 ──
    print("\n" + "=" * 100)
    print("2. 대분류(로마숫자) content 상세")
    print("=" * 100)

    romanPattern = re.compile(r"^[IVX]+\.\s")
    for key in matched:
        cr = collByTitle[key]
        title = cr["section_title"].strip()
        if not romanPattern.match(title):
            continue

        cLen = len(cr["section_content"] or "")
        zLen = len(zipByTitle[key]["section_content"] or "")

        print(f"\n  {title}")
        print(f"    collector: {cLen:>10,}자")
        print(f"    ZIP:       {zLen:>10,}자")
        if cLen > 0 and zLen == 0:
            print("    → collector는 하위 전체 합산, ZIP은 직접 content만 (0자)")
            print("      sections 영향: 대분류 content는 소분류에서 재구성하므로 실질 영향 없음")

    # ── 3. 소분류 content 샘플 (앞 300자) ──
    print("\n" + "=" * 100)
    print("3. 소분류 content 앞 300자 나란히 비교")
    print("=" * 100)

    sampleTitles = [
        "1. 회사의 개요", "2. 회사의 연혁", "1. 사업의 개요",
        "1. 요약재무정보", "3. 연결재무제표 주석",
    ]
    for sTitle in sampleTitles:
        key = _normalizeTitle(sTitle)
        if key not in collByTitle or key not in zipByTitle:
            continue

        cContent = (collByTitle[key]["section_content"] or "")[:300]
        zContent = (zipByTitle[key]["section_content"] or "")[:300]

        print(f"\n  [{sTitle}]")
        print(f"    coll: {cContent[:150].replace(chr(10), ' ')}")
        print(f"    zip:  {zContent[:150].replace(chr(10), ' ')}")

        if cContent == zContent:
            print("    → 완전 일치")
        else:
            sim = SequenceMatcher(None, cContent, zContent).ratio()
            print(f"    → 유사도 {sim:.1%}")

    # ── 4. table markdown 비교 ──
    print("\n" + "=" * 100)
    print("4. Table markdown 샘플 비교")
    print("=" * 100)

    for key in matched:
        cr = collByTitle[key]
        cContent = cr["section_content"] or ""
        zContent = (zipByTitle[key]["section_content"] or "")

        cBlocks = _splitContentBlocks(cContent)
        zBlocks = _splitContentBlocks(zContent)

        cTables = [b[1] for b in cBlocks if b[0] == "table"]
        zTables = [b[1] for b in zBlocks if b[0] == "table"]

        if cTables and zTables:
            print(f"\n  [{cr['section_title'][:40]}]")
            # 첫 테이블의 첫 3줄 비교
            cFirst = "\n".join(cTables[0].splitlines()[:3])
            zFirst = "\n".join(zTables[0].splitlines()[:3])
            print(f"    coll: {cFirst}")
            print(f"    zip:  {zFirst}")
            sim = SequenceMatcher(None, cTables[0][:500], zTables[0][:500]).ratio()
            print(f"    → 테이블 유사도: {sim:.1%}")
            break  # 1개만

    # ── 5. ZIP에만 있는 섹션 ──
    print("\n" + "=" * 100)
    print("5. ZIP에만 있는 섹션")
    print("=" * 100)
    zipOnlyKeys = set(zipByTitle.keys()) - set(collByTitle.keys())
    for key in sorted(zipOnlyKeys):
        zr = zipByTitle[key]
        topic = mapSectionTitle(zr["section_title"])
        zLen = len(zr["section_content"] or "")
        print(f"  + {zr['section_title'][:50]} → topic={topic}, {zLen:,}자")

    collOnlyKeys = set(collByTitle.keys()) - set(zipByTitle.keys())
    if collOnlyKeys:
        print("\n  collector에만 있는 섹션:")
        for key in sorted(collOnlyKeys):
            cr = collByTitle[key]
            topic = mapSectionTitle(cr["section_title"])
            cLen = len(cr["section_content"] or "")
            print(f"  - {cr['section_title'][:50]} → topic={topic}, {cLen:,}자")

    # ── 최종 판정 ──
    print("\n" + "=" * 100)
    print("최종 판정")
    print("=" * 100)
    print(f"  소분류 content 평균 유사도: {avgSim:.1%}")
    print(f"  collector 우위: {collWins}개 (주로 대분류 합산 content)")
    print(f"  ZIP 우위: {zipWins}개")
    print(f"  동등: {ties}개")


if __name__ == "__main__":
    main()
