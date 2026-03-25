"""실험 ID: 098-006
실험명: 사업보고서에서 수출/원재료 비중 regex 추출

목적:
- sections의 businessOverview/매출현황에서 수출비중, 해외매출비중,
  원재료 수입비중을 regex로 추출할 수 있는지 확인
- 거시경제 시나리오(환율/원자재)의 기업별 감응도 가중치로 활용 가능성

가설:
1. 대형주 30사 중 20사 이상에서 수출/해외 매출 비중 추출 가능 (>65%)
2. 추출된 수출비중의 분포가 합리적 (0~100%, 평균 30~50%)
3. 수출비중이 높은 기업은 실제 환율 민감 업종에 속함

방법:
1. docs parquet에서 "매출 및 수주상황", "사업의 개요" 텍스트 추출
2. 정규식 패턴으로 수출비중, 해외매출비중, 원재료 수입비중 추출
3. 대형주 30사 + 추가 확인용 20사 (총 50사)

결과:
- 수출/해외 비중 추출: 14/48 (29%) — 가설1 기각 (65% 미달)
- 원재료 수입 추출: 0/48 — 패턴 매칭 실패
- 수출비중 분포: 평균 61.6%, 중앙값 66.5% (추출된 14사 기준)
- 올바른 추출: POSCO(49%), S-Oil(42%), 고려아연(87%), 아모레퍼시픽(47%)
- false positive: KB금융(경제보고서 수출 통계를 자사로 오인), HMM(해운 수송비 99.7%)
- 추출 실패 대형주: 삼성전자, LG화학, 현대차, LG전자, 기아, NAVER 등
  → 이들은 "수출 XX%" 직접 패턴 미사용, 테이블 형태로 내수/수출 구분

결론:
- 가설1 기각: 29% 추출률로 대규모 적용 불가
- 가설2 부분 채택: 추출된 값은 합리적이나 false positive 존재
- 가설3 부분 채택: 수출비중 높은 기업은 실제 수출업종 (POSCO, 고려아연)
- **regex 기반 추출은 한국 사업보고서의 비정형 구조에서 한계**
  → 테이블 파싱(내수/수출 비율표) 또는 LLM 추출이 필요
  → segments 내 지역별 매출 테이블에서 추출하는 것이 더 현실적
- 원재료 수입 비중은 regex로 거의 불가능 (서술 방식이 너무 다양)

실험일: 2026-03-25
"""

import re
import time
from pathlib import Path

import polars as pl

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "dart" / "docs"

# 대표 종목 (시가총액 상위 대형주)
TARGET_CODES = [
    ("005930", "삼성전자"), ("000660", "SK하이닉스"), ("005380", "현대자동차"),
    ("005490", "POSCO홀딩스"), ("051910", "LG화학"), ("006400", "삼성SDI"),
    ("035420", "NAVER"), ("000270", "기아"), ("066570", "LG전자"),
    ("105560", "KB금융"), ("055550", "신한지주"), ("035720", "카카오"),
    ("373220", "LG에너지솔루션"), ("012330", "현대모비스"), ("003550", "LG"),
    ("096770", "SK이노베이션"), ("034730", "SK"), ("030200", "KT"),
    ("017670", "SK텔레콤"), ("003670", "포스코퓨처엠"),
    ("032830", "삼성생명"), ("010130", "고려아연"), ("009150", "삼성전기"),
    ("086790", "하나금융지주"), ("018260", "삼성에스디에스"), ("011200", "HMM"),
    ("010950", "S-Oil"), ("034020", "두산에너빌리티"), ("028260", "삼성물산"),
    ("047050", "포스코인터내셔널"), ("009540", "한국조선해양"), ("042660", "한화오션"),
    ("000720", "현대건설"), ("036570", "엔씨소프트"), ("015760", "한국전력"),
    ("010620", "현대미포조선"), ("009830", "한화솔루션"), ("011170", "롯데케미칼"),
    ("004020", "현대제철"), ("267250", "HD현대"), ("329180", "HD현대중공업"),
    ("064350", "현대로템"), ("402340", "SK스퀘어"), ("180640", "한진칼"),
    ("000150", "두산"), ("003490", "대한항공"), ("002790", "아모레퍼시픽"),
    ("079160", "CJ CGV"), ("035250", "강원랜드"), ("069500", "KODEX200"),
]

# 수출/해외매출 비중 추출 패턴
EXPORT_PATTERNS = [
    # "수출 XX.X%", "해외매출 비중 XX%"
    re.compile(r"수출[^0-9]{0,10}(\d{1,3}[\.\d]*)\s*%"),
    re.compile(r"해외[^0-9]{0,20}매출[^0-9]{0,10}(\d{1,3}[\.\d]*)\s*%"),
    re.compile(r"해외매출[^0-9]{0,10}비[^0-9]{0,5}(\d{1,3}[\.\d]*)\s*%"),
    re.compile(r"수출[^0-9]{0,5}비[^0-9]{0,5}(\d{1,3}[\.\d]*)\s*%"),
    re.compile(r"해외[^0-9]{0,5}비중[^0-9]{0,10}(\d{1,3}[\.\d]*)\s*%"),
    re.compile(r"해외\s*(\d{1,3}[\.\d]*)\s*%"),
    # "내수 XX% : 수출 YY%"
    re.compile(r"내수[^0-9]{0,5}\d{1,3}[\.\d]*\s*%[^0-9]{0,10}수출[^0-9]{0,5}(\d{1,3}[\.\d]*)\s*%"),
]

# 원재료 수입 비중 패턴
RAW_MATERIAL_PATTERNS = [
    re.compile(r"원재료[^0-9]{0,20}수입[^0-9]{0,10}(\d{1,3}[\.\d]*)\s*%"),
    re.compile(r"원자재[^0-9]{0,20}해외[^0-9]{0,10}(\d{1,3}[\.\d]*)\s*%"),
    re.compile(r"수입[^0-9]{0,5}비[^0-9]{0,5}(\d{1,3}[\.\d]*)\s*%"),
]


def _extractText(parquetPath: Path) -> str:
    """최신 사업보고서의 관련 section 텍스트를 모두 concat."""
    try:
        df = pl.read_parquet(str(parquetPath), columns=["year", "report_type", "section_title", "section_content"])
    except Exception:
        return ""
    df = df.filter(pl.col("report_type").str.contains("사업"))
    if df.height == 0:
        return ""
    latestYear = df["year"].cast(str).sort(descending=True).first()
    df = df.filter(pl.col("year") == latestYear)

    # 사업 내용 + 매출/수주 관련 section 모두
    relevant = df.filter(
        pl.col("section_title").str.contains("사업|매출|수주|원재료|수출|해외")
    )
    if relevant.height == 0:
        return ""
    texts = relevant["section_content"].drop_nulls().to_list()
    return "\n".join(str(t) for t in texts if t)


def _findExportRatio(text: str) -> list[tuple[float, str]]:
    """수출/해외매출 비중 추출. (값, 매칭 컨텍스트) 리스트 반환."""
    results = []
    for pat in EXPORT_PATTERNS:
        for m in pat.finditer(text):
            val = float(m.group(1))
            if 0 < val <= 100:
                # 매칭 주변 컨텍스트 (±30글자)
                start = max(0, m.start() - 30)
                end = min(len(text), m.end() + 30)
                ctx = text[start:end].replace("\n", " ").strip()
                results.append((val, ctx))
    return results


def _findRawMaterialImport(text: str) -> list[tuple[float, str]]:
    """원재료 수입 비중 추출."""
    results = []
    for pat in RAW_MATERIAL_PATTERNS:
        for m in pat.finditer(text):
            val = float(m.group(1))
            if 0 < val <= 100:
                start = max(0, m.start() - 30)
                end = min(len(text), m.end() + 30)
                ctx = text[start:end].replace("\n", " ").strip()
                results.append((val, ctx))
    return results


def run():
    t0 = time.time()
    print("=" * 70)
    print("  098-006: 사업보고서 수출/원재료 비중 regex 추출")
    print("=" * 70)

    exportFound = 0
    rawFound = 0
    exportValues = []

    for code, name in TARGET_CODES:
        pf = DATA_DIR / f"{code}.parquet"
        if not pf.exists():
            continue

        text = _extractText(pf)
        if not text:
            print(f"\n  {name:15s} ({code}): ❌ 텍스트 없음")
            continue

        exports = _findExportRatio(text)
        raws = _findRawMaterialImport(text)

        exportStr = ""
        if exports:
            exportFound += 1
            # 가장 큰 값을 대표값으로 (보통 전체 수출 비중)
            bestVal = max(exports, key=lambda x: x[0])
            exportValues.append(bestVal[0])
            exportStr = f"수출={bestVal[0]:.1f}%"

        rawStr = ""
        if raws:
            rawFound += 1
            bestVal = max(raws, key=lambda x: x[0])
            rawStr = f"원재료수입={bestVal[0]:.1f}%"

        status = "✅" if exports or raws else "  "
        print(f"\n  {status} {name:15s} ({code}): {exportStr} {rawStr}")
        if exports:
            for val, ctx in exports[:2]:
                print(f"       수출 컨텍스트: \"{ctx[:80]}\"")
        if raws:
            for val, ctx in raws[:1]:
                print(f"       원재료 컨텍스트: \"{ctx[:80]}\"")

    # 요약
    total = len([c for c, _ in TARGET_CODES if (DATA_DIR / f"{c}.parquet").exists()])
    print(f"\n{'=' * 70}")
    print(f"  요약")
    print(f"{'=' * 70}")
    print(f"  대상 종목: {total}개")
    print(f"  수출/해외 비중 추출: {exportFound}/{total} ({exportFound/total:.0%})")
    print(f"  원재료 수입 추출: {rawFound}/{total} ({rawFound/total:.0%})")
    if exportValues:
        import numpy as np
        arr = np.array(exportValues)
        print(f"  수출비중 분포: 평균={arr.mean():.1f}%, 중앙값={np.median(arr):.1f}%, "
              f"범위=[{arr.min():.1f}%, {arr.max():.1f}%]")
    print(f"  소요시간: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    run()
    print("\n실험 완료.")
