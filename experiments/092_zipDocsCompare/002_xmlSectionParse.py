"""실험 ID: 002
실험명: DART XML 본체의 섹션 구조 파싱 가능성 확인

목적:
- 001에서 ZIP 안에 XML 파일이 있음을 확인
- XML 본체(가장 큰 파일)의 내부 구조를 파악
- SECTION, TITLE, TABLE 등 태그로 섹션 분리가 가능한지 확인
- collector의 section_order, section_title과 매핑 가능한지 판단

가설:
1. XML 내부에 섹션 경계를 나타내는 태그가 있을 것이다
2. 해당 태그에서 section_title과 section_order를 추출할 수 있을 것이다

방법:
1. 삼성전자 사업보고서 ZIP의 본체 XML을 파싱
2. XML 태그 구조 분석 (depth 1~2 레벨)
3. 섹션 경계 태그 식별
4. 기존 collector 결과의 section_title과 비교

결과 (실험 후 작성):
- (실행 후 채울 것)

결론:
- (실행 후 채울 것)

실험일: 2026-03-24
"""

from __future__ import annotations

import io
import re
import zipfile
from collections import Counter

from dartlab.providers.dart.openapi.client import DartClient


def main():
    client = DartClient()

    # ZIP 다운로드
    rceptNo = "20260310002820"  # 삼성전자 사업보고서 2025.12
    raw = client.getBytes("document.xml", {"rcept_no": rceptNo})
    zf = zipfile.ZipFile(io.BytesIO(raw))

    # 본체 XML (가장 큰 파일)
    names = zf.namelist()
    largest = max(names, key=lambda n: zf.getinfo(n).file_size)
    content = zf.read(largest).decode("utf-8")

    print(f"파일: {largest}")
    print(f"크기: {len(content):,}자")

    # 1. 최상위 태그 구조 (depth 1~2)
    print("\n" + "=" * 60)
    print("1. XML 최상위 태그 구조")
    print("=" * 60)

    # 태그 이름만 추출 (closing 태그 제외)
    topTags = re.findall(r"<([A-Z][A-Z0-9_-]*)", content[:5000])
    tagCount = Counter(topTags)
    for tag, count in tagCount.most_common(20):
        print(f"  {tag}: {count}회")

    # 2. SECTION 관련 태그 찾기
    print("\n" + "=" * 60)
    print("2. SECTION 관련 태그 검색")
    print("=" * 60)

    sectionTags = re.findall(r"<(SECTION[^>]*?)>", content, re.IGNORECASE)
    print(f"SECTION 태그 수: {len(sectionTags)}")
    for tag in sectionTags[:20]:
        print(f"  <{tag}>")

    # 3. TITLE 태그 검색
    print("\n" + "=" * 60)
    print("3. TITLE 태그 내용")
    print("=" * 60)

    titles = re.findall(r"<TITLE[^>]*>(.*?)</TITLE>", content, re.IGNORECASE | re.DOTALL)
    print(f"TITLE 태그 수: {len(titles)}")
    for i, t in enumerate(titles[:30]):
        cleanTitle = re.sub(r"<[^>]+>", "", t).strip()
        cleanTitle = re.sub(r"\s+", " ", cleanTitle)
        if cleanTitle:
            print(f"  [{i}] {cleanTitle[:100]}")

    # 4. TOC (목차) 구조 확인
    print("\n" + "=" * 60)
    print("4. 목차(TOC) 구조 확인")
    print("=" * 60)

    tocMatch = re.search(r"<TOC[^>]*>(.*?)</TOC>", content, re.IGNORECASE | re.DOTALL)
    if tocMatch:
        tocContent = tocMatch.group(1)
        print(f"TOC 크기: {len(tocContent):,}자")
        # TOC 안의 항목들
        tocItems = re.findall(r"<P[^>]*>(.*?)</P>", tocContent[:3000], re.IGNORECASE | re.DOTALL)
        for i, item in enumerate(tocItems[:20]):
            cleanItem = re.sub(r"<[^>]+>", "", item).strip()
            cleanItem = re.sub(r"\s+", " ", cleanItem)
            if cleanItem:
                print(f"  [{i}] {cleanItem[:100]}")
    else:
        print("TOC 태그 없음")

    # 5. SECTION-1, SECTION-2 등 depth별 구조
    print("\n" + "=" * 60)
    print("5. SECTION depth별 구조")
    print("=" * 60)

    for depth in range(1, 5):
        tag = f"SECTION-{depth}"
        matches = re.findall(rf"<{tag}[^>]*>", content, re.IGNORECASE)
        if matches:
            print(f"\n  {tag}: {len(matches)}개")
            # 각 섹션의 첫 TITLE 추출
            pattern = rf"<{tag}[^>]*>\s*<TITLE[^>]*>(.*?)</TITLE>"
            sectionTitles = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for i, t in enumerate(sectionTitles[:15]):
                cleanTitle = re.sub(r"<[^>]+>", "", t).strip()
                cleanTitle = re.sub(r"\s+", " ", cleanTitle)
                if cleanTitle:
                    print(f"    [{i}] {cleanTitle[:100]}")

    # 6. 전체 태그 통계 (상위 30개)
    print("\n" + "=" * 60)
    print("6. 전체 태그 통계 (상위 30개)")
    print("=" * 60)

    allTags = re.findall(r"<([A-Z][A-Z0-9_-]*)", content)
    allTagCount = Counter(allTags)
    for tag, count in allTagCount.most_common(30):
        print(f"  {tag}: {count:,}회")

    # 7. BODY vs SUMMARY 구조
    print("\n" + "=" * 60)
    print("7. 문서 구조 (BODY, SUMMARY, DOCUMENT-NAME)")
    print("=" * 60)

    docNames = re.findall(r"<DOCUMENT-NAME[^>]*>(.*?)</DOCUMENT-NAME>", content, re.IGNORECASE)
    print(f"DOCUMENT-NAME: {docNames}")

    bodyStart = content.find("<BODY")
    bodyEnd = content.find("</BODY>")
    if bodyStart >= 0:
        print(f"BODY 시작: {bodyStart:,}자 위치")
        print(f"BODY 끝: {bodyEnd:,}자 위치")
        print(f"BODY 크기: {bodyEnd - bodyStart:,}자")

    # 8. 기존 collector 결과의 section_title 목록 (비교용)
    print("\n" + "=" * 60)
    print("8. 기존 collector section_title 목록 (비교용, 유사 rcept_no)")
    print("=" * 60)

    import polars as pl

    from dartlab.core.dataLoader import loadData

    docsParquet = loadData("005930", category="docs")
    if docsParquet is not None:
        # 최근 사업보고서 1건 찾기
        annualDocs = docsParquet.filter(pl.col("report_type").str.contains("사업보고서"))
        if annualDocs.height > 0:
            latestRcept = annualDocs.sort("rcept_date", descending=True)["rcept_no"][0]
            sections = docsParquet.filter(pl.col("rcept_no") == latestRcept)
            print(f"비교 대상: rcept_no={latestRcept}")
            print(f"섹션 수: {sections.height}")
            for row in sections.sort("section_order").iter_rows(named=True):
                print(f"  [{row['section_order']:2d}] {row['section_title']}")


if __name__ == "__main__":
    main()
