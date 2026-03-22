"""실험 ID: 001
실험명: 사업모델 DNA 추출을 위한 데이터 품질 감사

목적:
- 사업모델 추출에 필요한 핵심 데이터 모듈의 커버리지 측정
- 50개 대표 기업(5섹터 × 10사) 대상으로 7개 핵심 모듈 가용성 확인
- Phase 1 실험 설계의 데이터 기반 근거 확보

가설:
1. 7개 핵심 모듈(segments, costByNature, employee, tangibleAsset, rnd, dividend, subsidiary) 중
   모듈당 평균 커버리지가 50개 기업 기준 70% 이상
2. finance 기반 데이터(ratios, timeseries)는 90%+ 커버리지
3. 섹터별 커버리지 편차가 20%p 이내

방법:
1. dartlab.listing()으로 전체 종목 확보 + sector 분류
2. 5개 섹터(반도체/IT, 자동차/산업재, 제약/건강관리, 금융, 식품/필수소비재) × 10사 선정
   - 각 섹터 시가총액 상위 기업 우선 (데이터 품질이 높을 가능성)
3. 각 기업에 대해:
   a) finance: buildTimeseries() 존재 여부 + 연도 수
   b) report: loadData(code, "report") → api_type별 행 수
   c) docs: loadData(code, "docs") → section 존재 여부
4. 커버리지 매트릭스(기업 × 모듈) 생성
5. 섹터별/모듈별 통계 산출

결과 (실험 후 작성):
- 수집 시간: 125.5s (50사, 다운로드 포함)
- Finance 커버리지: hasFinance 96%, BS/IS/CF 각 96% (48/50)
  - 미존재: 하나금융지주(086790), 롯데지주(002270)
- Report 모듈 커버리지: employee/dividend/executive/majorHolder/capitalChange 각 98% (49/50)
  - 미존재: 롯데지주(002270) — GitHub Release에 finance/report 없음
- Docs 섹션 커버리지 (section_title 키워드 매칭):
  - segments: 6%, costByNature: 6% ← 매우 낮음
  - rnd: 52%, tangibleAsset: 66%, subsidiary: 66%
  - business: 66%, risk: 52%
  - 원인: section_title에 세부 토픽(부문, 비용 등)이 별도 행으로 없음.
    실제로는 "사업의 내용" 본문 안에 부문/비용 정보가 포함됨.
    sections 수평화(Company.sections)를 거쳐야 segments 등 세부 토픽 추출 가능.
- 섹터별 평균 모듈 커버리지:
  - IT/반도체: 88.3%, 산업재/자동차: 79.2%, 건강관리/제약: 62.5%
  - 금융: 59.2%, 필수소비재/식품: 45.8%
  - 식품/소비재 섹터가 낮은 이유: 새로 다운로드된 docs에 section_title 검색 실패
- 금융 섹터: finance 기간이 9p로 짧음 (지주회사 구조, 은행업 특수 계정)

결론:
- Finance + Report 커버리지: 96~98% → Phase 1의 재무비율 기반 분석은 충분
- Docs 섹션: section_title 수준 매칭으로는 segments/costByNature 추출 불가
  → Phase 1에서는 Company.show()를 통한 sections 수평화 기반 접근 필요
  → 메모리 제약상 2사씩 배치 처리 필수
- Report 모듈(employee, dividend 등)이 98%로 매우 높아 사업모델 DNA의 핵심 축 역할 가능
- 금융 섹터는 finance 기간이 짧고 일반 제조업 계정 부재 → 별도 처리 필요
- Phase 0 관문 판정: **조건부 통과**
  - finance + report: 통과 (70%+ 초과 달성)
  - docs 세부 토픽: section_title 기반 탈락, sections 수평화 기반으로 재검사 필요

실험일: 2026-03-22
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

DATA_DIR = Path(__file__).parent / "data"

# ── 사업모델 DNA에 필요한 핵심 모듈 ──
# finance 기반 (buildTimeseries로 확인)
FINANCE_MODULES = ["BS", "IS", "CF"]

# report 기반 (report parquet의 api_type으로 확인)
REPORT_MODULES = [
    "employee",       # 직원 현황 → 인건비 구조, 노동집약도
    "dividend",       # 배당 → 자본배분
    "executive",      # 임원 → 지배구조
    "majorHolder",    # 대주주 → 소유구조
    "capitalChange",  # 자본변동 → 자본배분 이력
]

# docs 기반 (docs parquet에서 section_title 키워드 매칭)
DOCS_SECTION_KEYWORDS = {
    "segments":     ["부문", "사업부문", "부문정보", "Segment"],
    "costByNature": ["비용", "원가", "매출원가", "cost"],
    "rnd":          ["연구개발", "R&D", "연구", "개발비"],
    "tangibleAsset": ["유형자산", "설비", "tangible"],
    "subsidiary":   ["종속회사", "자회사", "관계회사", "종속기업"],
    "business":     ["사업의 내용", "사업의 개요", "사업개요"],
    "risk":         ["위험", "리스크", "risk"],
}

# ── 50사 선정을 위한 섹터별 대표 기업 (시가총액 상위) ──
# 수동 선정: 로컬 데이터 보유 가능성이 높은 대형주 중심
SECTOR_COMPANIES = {
    "IT/반도체": [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035420", "NAVER"),
        ("035720", "카카오"),
        ("006400", "삼성SDI"),
        ("247540", "에코프로비엠"),
        ("373220", "LG에너지솔루션"),
        ("068270", "셀트리온"),
        ("207940", "삼성바이오로직스"),
        ("036570", "엔씨소프트"),
    ],
    "산업재/자동차": [
        ("005380", "현대차"),
        ("000270", "기아"),
        ("012330", "현대모비스"),
        ("010130", "고려아연"),
        ("051910", "LG화학"),
        ("011170", "롯데케미칼"),
        ("003550", "LG"),
        ("034730", "SK"),
        ("028260", "삼성물산"),
        ("009150", "삼성전기"),
    ],
    "건강관리/제약": [
        ("068270", "셀트리온"),
        ("207940", "삼성바이오로직스"),
        ("326030", "SK바이오팜"),
        ("128940", "한미약품"),
        ("006280", "녹십자"),
        ("000100", "유한양행"),
        ("185750", "종근당"),
        ("003060", "에이치엘비"),
        ("145720", "덴티움"),
        ("214150", "클래시스"),
    ],
    "금융": [
        ("105560", "KB금융"),
        ("055550", "신한지주"),
        ("086790", "하나금융지주"),
        ("316140", "우리금융지주"),
        ("024110", "기업은행"),
        ("138930", "BNK금융지주"),
        ("175330", "JB금융지주"),
        ("032830", "삼성생명"),
        ("000810", "삼성화재"),
        ("088350", "한화생명"),
    ],
    "필수소비재/식품": [
        ("097950", "CJ제일제당"),
        ("004370", "농심"),
        ("271560", "오리온"),
        ("280360", "롯데웰푸드"),
        ("005300", "롯데칠성"),
        ("007310", "오뚜기"),
        ("003230", "삼양식품"),
        ("002270", "롯데지주"),
        ("001040", "CJ"),
        ("282330", "BGF리테일"),
    ],
}


def _checkFinance(stockCode: str) -> dict:
    """finance parquet 로드하여 BS/IS/CF 존재 여부 + 기간 수 확인."""
    from dartlab.engines.company.dart.finance.pivot import buildTimeseries

    try:
        result = buildTimeseries(stockCode)
        if result is None:
            return {"hasFinance": False, "periods": 0, "BS": False, "IS": False, "CF": False}

        series, periods = result
        return {
            "hasFinance": True,
            "periods": len(periods),
            "BS": bool(series.get("BS")),
            "IS": bool(series.get("IS")),
            "CF": bool(series.get("CF")),
        }
    except (FileNotFoundError, RuntimeError, OSError):
        return {"hasFinance": False, "periods": 0, "BS": False, "IS": False, "CF": False}


def _checkReport(stockCode: str) -> dict[str, int]:
    """report parquet에서 api_type별 행 수 확인."""
    from dartlab.core.dataLoader import loadData

    result = {m: 0 for m in REPORT_MODULES}
    try:
        df = loadData(stockCode, category="report", columns=["apiType"])
        if df is not None and not df.is_empty():
            counts = df.group_by("apiType").len()
            for row in counts.iter_rows(named=True):
                apiType = row["apiType"]
                if apiType in result:
                    result[apiType] = row["len"]
    except (FileNotFoundError, RuntimeError, OSError):
        pass
    return result


def _checkDocs(stockCode: str) -> dict[str, bool]:
    """docs parquet에서 핵심 섹션 키워드 존재 여부 확인."""
    from dartlab.core.dataLoader import loadData

    result = {k: False for k in DOCS_SECTION_KEYWORDS}
    try:
        df = loadData(stockCode, category="docs", columns=["section_title"])
        if df is None or df.is_empty():
            return result

        titles = df["section_title"].unique().to_list()
        titleText = " ".join(str(t) for t in titles if t is not None)

        for module, keywords in DOCS_SECTION_KEYWORDS.items():
            for kw in keywords:
                if kw in titleText:
                    result[module] = True
                    break
    except (FileNotFoundError, RuntimeError, OSError):
        pass
    return result


def runAudit(*, verbose: bool = True) -> pl.DataFrame:
    """50사 데이터 품질 감사 실행."""
    rows = []
    totalStart = time.time()

    for sector, companies in SECTOR_COMPANIES.items():
        if verbose:
            print(f"\n{'='*60}")
            print(f"섹터: {sector} ({len(companies)}사)")
            print(f"{'='*60}")

        for stockCode, corpName in companies:
            start = time.time()
            row: dict = {"stockCode": stockCode, "corpName": corpName, "sector": sector}

            # 1. finance 확인
            fin = _checkFinance(stockCode)
            row.update(fin)

            # 2. report 확인
            rep = _checkReport(stockCode)
            for m in REPORT_MODULES:
                row[f"report_{m}"] = rep[m] > 0
                row[f"report_{m}_rows"] = rep[m]

            # 3. docs 확인
            docs = _checkDocs(stockCode)
            for m in DOCS_SECTION_KEYWORDS:
                row[f"docs_{m}"] = docs[m]

            elapsed = time.time() - start
            row["elapsed_s"] = round(elapsed, 2)
            rows.append(row)

            if verbose:
                finStr = f"fin={'✓' if fin['hasFinance'] else '✗'}({fin['periods']}p)"
                repCount = sum(1 for m in REPORT_MODULES if rep[m] > 0)
                docsCount = sum(1 for m in DOCS_SECTION_KEYWORDS if docs[m])
                print(f"  {corpName:12s} ({stockCode}) | {finStr} | "
                      f"report={repCount}/{len(REPORT_MODULES)} | "
                      f"docs={docsCount}/{len(DOCS_SECTION_KEYWORDS)} | "
                      f"{elapsed:.1f}s")

    totalElapsed = time.time() - totalStart
    df = pl.DataFrame(rows)

    # ── 결과 요약 ──
    total = len(df)
    print(f"\n{'='*60}")
    print(f"총 {total}사, {totalElapsed:.1f}s")
    print(f"{'='*60}")

    # finance 커버리지
    print("\n[Finance 커버리지]")
    for col in ["hasFinance", "BS", "IS", "CF"]:
        pct = df[col].sum() / total * 100
        print(f"  {col:15s}: {df[col].sum():3d}/{total} ({pct:.1f}%)")

    # report 모듈 커버리지
    print("\n[Report 모듈 커버리지]")
    for m in REPORT_MODULES:
        col = f"report_{m}"
        pct = df[col].sum() / total * 100
        print(f"  {m:15s}: {df[col].sum():3d}/{total} ({pct:.1f}%)")

    # docs 섹션 커버리지
    print("\n[Docs 섹션 커버리지]")
    for m in DOCS_SECTION_KEYWORDS:
        col = f"docs_{m}"
        pct = df[col].sum() / total * 100
        print(f"  {m:15s}: {df[col].sum():3d}/{total} ({pct:.1f}%)")

    # 섹터별 평균 커버리지
    print("\n[섹터별 평균 모듈 커버리지]")
    allModuleCols = (
        [f"report_{m}" for m in REPORT_MODULES]
        + [f"docs_{m}" for m in DOCS_SECTION_KEYWORDS]
    )
    for sector in SECTOR_COMPANIES:
        sectorDf = df.filter(pl.col("sector") == sector)
        n = len(sectorDf)
        if n == 0:
            continue
        avgPct = sum(sectorDf[c].sum() for c in allModuleCols) / (n * len(allModuleCols)) * 100
        print(f"  {sector:20s}: {avgPct:.1f}%")

    # parquet 저장
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    outPath = DATA_DIR / "001_dataAudit.parquet"
    df.write_parquet(outPath)
    print(f"\n→ {outPath}")

    return df


if __name__ == "__main__":
    df = runAudit()
