"""실험 ID: 001
실험명: OpenDART document.xml ZIP 원본 구조 확인

목적:
- document.xml API가 반환하는 ZIP 파일의 내부 구조 파악
- 파일 개수, 포맷(XML/HTML), 인코딩, 크기 확인
- 섹션별 파일 분리 여부 확인
- 현재 docs parquet 스키마 재현 가능성 판단

가설:
1. ZIP 안에 여러 XML/HTML 파일이 들어있고, 각 파일이 섹션에 대응할 것이다
2. 파일명이나 구조에서 section_title, section_order를 추출할 수 있을 것이다

방법:
1. 삼성전자(005930) 최근 사업보고서 rcept_no 1건 확인
2. document.xml API로 ZIP 다운로드
3. ZIP 내부 파일 목록, 크기, 포맷 출력
4. 각 파일 내용 샘플 확인 (첫 500자)
5. 기존 collector 결과(docs parquet)와 섹션 구조 비교

결과 (실험 후 작성):
- (실행 후 채울 것)

결론:
- (실행 후 채울 것)

실험일: 2026-03-24
"""

from __future__ import annotations

import io
import zipfile

import polars as pl

from dartlab.providers.dart.openapi.client import DartClient
from dartlab.providers.dart.openapi.disclosure import listFilings


def main():
    client = DartClient()

    # 1. 삼성전자 최근 정기공시 목록
    print("=" * 60)
    print("1. 삼성전자 최근 정기공시 목록 (최근 2건)")
    print("=" * 60)
    filings = listFilings(client, "005930", start="20240101", filingType="A", fetchAll=True)
    if filings.is_empty():
        print("공시 없음")
        return

    print(filings.select("rcept_no", "report_nm", "rcept_dt").head(5))

    # 첫 번째 사업보고서 접수번호
    rceptNo = filings["rcept_no"][0]
    reportNm = filings["report_nm"][0]
    print(f"\n대상: {reportNm} (rcept_no={rceptNo})")

    # 2. document.xml API 호출 → ZIP 다운로드
    print("\n" + "=" * 60)
    print("2. document.xml API → ZIP 다운로드")
    print("=" * 60)
    raw = client.getBytes("document.xml", {"rcept_no": rceptNo})
    print(f"ZIP 크기: {len(raw):,} bytes ({len(raw) / 1024:.1f} KB)")

    zf = zipfile.ZipFile(io.BytesIO(raw))
    names = zf.namelist()
    print(f"ZIP 내 파일 수: {len(names)}")

    # 3. 파일 목록 상세
    print("\n" + "=" * 60)
    print("3. ZIP 내부 파일 목록")
    print("=" * 60)
    for i, name in enumerate(names):
        info = zf.getinfo(name)
        print(f"  [{i}] {name}")
        print(f"      크기: {info.file_size:,} bytes ({info.file_size / 1024:.1f} KB)")
        print(f"      압축: {info.compress_size:,} bytes")

    # 4. 각 파일 내용 샘플 (첫 500자)
    print("\n" + "=" * 60)
    print("4. 각 파일 내용 샘플 (첫 500자)")
    print("=" * 60)
    for i, name in enumerate(names):
        content = zf.read(name)
        # 인코딩 시도
        text = None
        usedEncoding = None
        for enc in ("euc-kr", "utf-8", "cp949"):
            try:
                text = content.decode(enc)
                usedEncoding = enc
                break
            except (UnicodeDecodeError, LookupError):
                continue
        if text is None:
            text = content.decode("utf-8", errors="replace")
            usedEncoding = "utf-8(replace)"

        print(f"\n--- [{i}] {name} (encoding={usedEncoding}) ---")
        print(text[:500])
        print("..." if len(text) > 500 else "")

    # 5. 기존 collector 결과와 비교
    print("\n" + "=" * 60)
    print("5. 기존 docs parquet의 동일 rcept_no 섹션 구조")
    print("=" * 60)
    from dartlab.core.dataLoader import loadData

    docsParquet = loadData("005930", category="docs")
    if docsParquet is not None and not docsParquet.is_empty():
        sections = docsParquet.filter(pl.col("rcept_no") == rceptNo)
        if sections.height > 0:
            print(f"collector 결과 섹션 수: {sections.height}")
            print(
                sections.select("section_order", "section_title", "section_url")
                .sort("section_order")
            )
            # 내용 길이 통계
            contentLens = sections.with_columns(
                pl.col("section_content").str.len_chars().alias("contentLen")
            ).select("section_order", "section_title", "contentLen").sort("section_order")
            print("\n섹션별 내용 길이:")
            print(contentLens)
        else:
            print(f"rcept_no={rceptNo}에 해당하는 collector 결과 없음")
            # 있는 rcept_no 목록 출력
            available = docsParquet.select("rcept_no", "report_type").unique(subset=["rcept_no"]).head(5)
            print("사용 가능한 rcept_no 샘플:")
            print(available)
    else:
        print("docs parquet 없음 (수집 안 됨)")

    # 6. ZIP 파일이 여러개면 각 파일의 구조 분석
    print("\n" + "=" * 60)
    print("6. ZIP 파일 구조 분석 (HTML/XML 태그 확인)")
    print("=" * 60)
    for i, name in enumerate(names):
        content = zf.read(name)
        for enc in ("euc-kr", "utf-8", "cp949"):
            try:
                text = content.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            text = content.decode("utf-8", errors="replace")

        # 파일 형식 판단
        isHtml = "<html" in text.lower()[:200] or "<body" in text.lower()[:500]
        isXml = "<?xml" in text[:100]
        hasTable = "<table" in text.lower()

        # 제목 태그 추출
        import re

        titleMatch = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        title = titleMatch.group(1).strip() if titleMatch else "(no title)"

        # h1/h2 태그 추출
        headings = re.findall(r"<h[12][^>]*>(.*?)</h[12]>", text, re.IGNORECASE | re.DOTALL)
        headings = [re.sub(r"<[^>]+>", "", h).strip() for h in headings[:5]]

        print(f"\n[{i}] {name}")
        print(f"  포맷: {'HTML' if isHtml else 'XML' if isXml else '기타'}")
        print(f"  테이블 포함: {hasTable}")
        print(f"  title: {title}")
        print(f"  headings: {headings[:5]}")
        print(f"  총 길이: {len(text):,}자")


if __name__ == "__main__":
    main()
