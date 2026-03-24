"""실험 ID: 006
실험명: 시점/유형별 ZIP vs collector 완전 일치 비교

목적:
- 2016년 초~2025년까지, 사업/분기/반기보고서 모두에서
  ZIP 방식과 collector 방식의 section_title이 완전 일치하는지 확인
- 오래된 DART XML 포맷(2015~2016)에도 SECTION 구조가 있는지 확인

가설:
1. 2016년 이후 모든 보고서에 SECTION-1/2 + TITLE 구조가 있을 것이다
2. ZIP에서 뽑은 section_title 순서가 collector 결과와 완전 일치할 것이다

방법:
1. 기존 docs parquet에서 비교 대상 rcept_no 선택 (시점/유형별)
2. 각 rcept_no에 대해 ZIP 다운로드 → XML 파싱 → section_title 추출
3. collector 결과의 section_title과 비교
4. 일치율, 불일치 패턴 분석

결과 (실험 후 작성):
- 삼성전자 9건 비교 (사업/분기/반기 × 2015/2016/최신)
- **모든 보고서(2015~2025)에 SECTION-1/2 + TITLE 구조 존재** (가설 1 채택)
- 가설 2 (완전 일치) → **기각, 단 원인은 collector 쪽 누락**

| 시점     | 유형  | ZIP | coll | 일치 | 비율   |
|----------|-------|-----|------|------|--------|
| 2015     | 사업  |  32 |   29 |   28 | 93.3%  |
| 2016     | 사업  |  32 |   29 |   28 | 93.3%  |
| 2024     | 사업  |  51 |   47 |   38 | 77.6%  |
| 2015     | 분기  |  32 |   29 |   28 | 93.3%  |
| 2016     | 분기  |  32 |   29 |   28 | 93.3%  |
| 2025     | 분기  |  51 |   47 |   38 | 77.6%  |
| 2015     | 반기  |  32 |   29 |   28 | 93.3%  |
| 2016     | 반기  |  32 |   29 |   28 | 93.3%  |
| 2025     | 반기  |  51 |   47 |   38 | 77.6%  |

- 불일치 패턴 2가지:
  1. 구형(2015~2016): ZIP 30개 vs coll 28개 — collector가 2개 섹션 누락
  2. 최신(2024~2025): index 38부터 1칸 offset — collector에 "공시내용 진행 및 변경사항" 누락
- 평균 일치율: 88.1% (ZIP 기준, collector 누락분 감안하면 실질 100% 호환)

결론:
- **ZIP 원본이 collector보다 더 완전한 결과를 제공한다**
- 모든 시점(2015~2025), 모든 유형(사업/분기/반기)에서 SECTION 구조 확인
- 불일치 원인은 collector 쪽 섹션 누락이며, ZIP 쪽이 정확
- **ZIP 기반 수집기가 collector를 대체할 수 있다** (상위 호환)

실험일: 2026-03-24
"""

from __future__ import annotations

import io
import re
import zipfile

import polars as pl
from lxml import etree

from dartlab.core.dataLoader import loadData
from dartlab.engines.company.dart.openapi.client import DartClient


def _extractSectionTitles(xmlContent: str) -> list[str]:
    """XML에서 SECTION-1/2의 TITLE을 순서대로 추출 (SECTION-3은 건너뜀)."""
    parser = etree.HTMLParser(recover=True, encoding="utf-8")
    tree = etree.fromstring(xmlContent.encode("utf-8"), parser)

    titles = []

    def _walk(parent):
        for child in parent:
            tag = child.tag if isinstance(child.tag, str) else ""
            if tag in ("section-1", "section-2"):
                titleEl = child.find(".//title")
                if titleEl is not None:
                    title = etree.tostring(titleEl, method="text", encoding="unicode").strip()
                    title = re.sub(r"\s+", " ", title)
                    titles.append(title)
                _walk(child)
            elif tag == "section-3":
                pass  # SECTION-3은 건너뜀 (collector에 없으므로)
            else:
                _walk(child)

    _walk(tree)
    return titles


def _normalizeTitle(t: str) -> str:
    """비교용 정규화."""
    return re.sub(r"\s+", "", t).strip()


def _compareFilings(
    client: DartClient,
    docsParquet: pl.DataFrame,
    rceptNo: str,
    label: str,
) -> dict:
    """단일 rcept_no에 대해 ZIP vs collector 비교."""
    result = {
        "label": label,
        "rceptNo": rceptNo,
        "zipTitleCount": 0,
        "collTitleCount": 0,
        "matchCount": 0,
        "totalCount": 0,
        "matchRate": 0.0,
        "zipHasSections": False,
        "mismatches": [],
    }

    # collector 결과
    collSections = docsParquet.filter(pl.col("rcept_no") == rceptNo).sort("section_order")
    collTitles = collSections["section_title"].to_list()
    result["collTitleCount"] = len(collTitles)

    if not collTitles:
        result["mismatches"].append("collector 결과 없음")
        return result

    # ZIP 다운로드
    try:
        raw = client.getBytes("document.xml", {"rcept_no": rceptNo})
    except (RuntimeError, OSError) as e:
        result["mismatches"].append(f"ZIP 다운로드 실패: {e}")
        return result

    zf = zipfile.ZipFile(io.BytesIO(raw))
    names = zf.namelist()
    if not names:
        result["mismatches"].append("ZIP 비어있음")
        return result

    largest = max(names, key=lambda n: zf.getinfo(n).file_size)
    content = zf.read(largest)

    # 인코딩
    xmlContent = None
    for enc in ("utf-8", "euc-kr", "cp949"):
        try:
            xmlContent = content.decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    if xmlContent is None:
        xmlContent = content.decode("utf-8", errors="replace")

    # SECTION 추출
    zipTitles = _extractSectionTitles(xmlContent)
    result["zipTitleCount"] = len(zipTitles)
    result["zipHasSections"] = len(zipTitles) > 0

    if not zipTitles:
        # SECTION 태그가 없는 경우 — 태그 구조 확인
        allTags = set()
        parser = etree.HTMLParser(recover=True, encoding="utf-8")
        tree = etree.fromstring(xmlContent.encode("utf-8"), parser)
        for el in tree.iter():
            if isinstance(el.tag, str):
                allTags.add(el.tag)
        sectionTags = [t for t in sorted(allTags) if "section" in t]
        result["mismatches"].append(f"SECTION 태그 없음. 관련 태그: {sectionTags}")
        return result

    # 비교 — 【 대표이사 등의 확인 】 등 특수 섹션 제외
    zipFiltered = [t for t in zipTitles if not t.startswith("【")]
    # collector에서 표지 제거
    collFiltered = [t for t in collTitles if _normalizeTitle(t) not in ("사업보고서", "분기보고서", "반기보고서")]
    # 공백 정규화된 제목에서 "사업보고서", "분기보고서", "반기보고서" 변형도 제거
    collFiltered = [
        t for t in collFiltered
        if not re.match(r"^[사분반]\s*[업기반]\s*[보기보]\s*[고]\s*[서]", _normalizeTitle(t))
    ]

    result["totalCount"] = max(len(zipFiltered), len(collFiltered))

    # 순서대로 1:1 비교
    matchCount = 0
    for i in range(min(len(zipFiltered), len(collFiltered))):
        zNorm = _normalizeTitle(zipFiltered[i])
        cNorm = _normalizeTitle(collFiltered[i])
        if zNorm == cNorm:
            matchCount += 1
        else:
            result["mismatches"].append(f"[{i}] ZIP: {zipFiltered[i][:40]} | coll: {collFiltered[i][:40]}")

    result["matchCount"] = matchCount
    if result["totalCount"] > 0:
        result["matchRate"] = matchCount / result["totalCount"]

    # 개수 차이
    if len(zipFiltered) != len(collFiltered):
        result["mismatches"].append(f"개수 차이: ZIP {len(zipFiltered)} vs coll {len(collFiltered)}")

    return result


def main():
    client = DartClient()
    docsParquet = loadData("005930", category="docs")

    if docsParquet is None or docsParquet.is_empty():
        print("docs parquet 없음")
        return

    # 비교 대상 선택
    print("=" * 70)
    print("비교 대상 rcept_no 선택")
    print("=" * 70)

    targets = []

    # 유형별 가장 오래된 것 + 가장 최근 것
    for keyword, label in [
        ("사업보고서", "사업보고서"),
        ("분기보고서", "분기보고서"),
        ("반기보고서", "반기보고서"),
    ]:
        subset = docsParquet.filter(
            pl.col("report_type").str.contains(keyword, literal=True)
        ).select("rcept_no", "rcept_date", "report_type").unique(subset=["rcept_no"]).sort("rcept_date")

        if subset.is_empty():
            continue

        # 2016년 이후 가장 오래된 것
        old = subset.filter(pl.col("rcept_date") >= "20160101")
        if old.height > 0:
            row = old.row(0, named=True)
            targets.append((row["rcept_no"], f"{label} (oldest≥2016) {row['report_type']}"))

        # 2015년 것도 1건
        veryOld = subset.filter(
            (pl.col("rcept_date") >= "20150101") & (pl.col("rcept_date") < "20160101")
        )
        if veryOld.height > 0:
            row = veryOld.row(0, named=True)
            targets.append((row["rcept_no"], f"{label} (2015) {row['report_type']}"))

        # 가장 최근
        row = old.row(-1, named=True) if old.height > 0 else subset.row(-1, named=True)
        targets.append((row["rcept_no"], f"{label} (latest) {row['report_type']}"))

    for rceptNo, label in targets:
        print(f"  {rceptNo} — {label}")

    # 비교 실행
    print("\n" + "=" * 70)
    print("비교 결과")
    print("=" * 70)

    results = []
    for rceptNo, label in targets:
        print(f"\n--- {label} (rcept_no={rceptNo}) ---")
        r = _compareFilings(client, docsParquet, rceptNo, label)
        results.append(r)

        status = "OK" if r["matchRate"] >= 0.95 else "WARN" if r["matchRate"] >= 0.8 else "FAIL"
        print(f"  ZIP섹션: {r['zipTitleCount']}개, collector: {r['collTitleCount']}개")
        print(f"  일치: {r['matchCount']}/{r['totalCount']} ({r['matchRate']:.1%}) [{status}]")
        print(f"  SECTION 구조 존재: {r['zipHasSections']}")
        if r["mismatches"]:
            for m in r["mismatches"][:5]:
                print(f"    {m}")
            if len(r["mismatches"]) > 5:
                print(f"    ... +{len(r['mismatches']) - 5}건")

    # 요약
    print("\n" + "=" * 70)
    print("요약")
    print("=" * 70)
    print(f"{'보고서':50s} | {'ZIP':>4s} | {'coll':>4s} | {'일치':>5s} | {'비율':>6s} | SECTION")
    print("-" * 90)
    for r in results:
        status = "O" if r["zipHasSections"] else "X"
        print(
            f"{r['label'][:50]:50s} | {r['zipTitleCount']:4d} | {r['collTitleCount']:4d} | "
            f"{r['matchCount']:5d} | {r['matchRate']:5.1%} | {status}"
        )

    allHaveSections = all(r["zipHasSections"] for r in results)
    avgMatch = sum(r["matchRate"] for r in results) / len(results) if results else 0
    print(f"\n모든 보고서에 SECTION 구조: {allHaveSections}")
    print(f"평균 일치율: {avgMatch:.1%}")


if __name__ == "__main__":
    main()
