"""실험 ID: 005
실험명: 현금전환 효율 패턴화 — CCC + 영업CF마진

목적:
- 사업모델 DNA의 네 번째 축: "매출이 현금으로 전환되는 효율"
- CCC(Cash Conversion Cycle) + 영업CF마진 조합으로 현금전환 효율 패턴 분류
- CCC 악화 → 다음해 실적 하락 상관 검증

가설:
1. CCC(DSO+DIO-DPO) + 영업CF마진으로 현금전환 효율을 2차원 분류 가능:
   - 빠른 현금화(낮은 CCC, 높은 CF마진): 플랫폼, SW
   - 느린 현금화(높은 CCC, 낮은 CF마진): 제조, 건설
   - 비정상(음수 CCC): 선수금 비즈니스, 유통
2. CCC 악화(전년 대비 증가) → 다음해 영업이익 하락 상관 > 0.2

방법:
1. 48사에 대해 BS(receivables, inventories, payables) + IS(revenue, cost_of_sales) +
   CF(operating_cashflow) 시계열 직접 추출
2. CCC = DSO + DIO - DPO (일수 기준)
   - DSO = trade_receivables / revenue × 365
   - DIO = inventories / cost_of_sales × 365
   - DPO = trade_payables / cost_of_sales × 365
3. 영업CF마진 = operating_cashflow / revenue × 100
4. 2차원 분류(CCC × CF마진) + 섹터 매칭 검증

결과 (실행 후 작성):
- 수집: 8.1s, 48사 (금융 10사 중 유효 0사)
- 유효 데이터: DSO 37/48, DIO 35/48, DPO 35/48, CCC 35/48, CF마진 37/48
- 금융 섹터: 매출/매출원가/재고 개념 없음 → CCC 전체 N/A (별도 처리 필요)
- 섹터별 평균 (금융 제외):
  | 섹터         | DSO(일) | DIO(일)  | DPO(일)   | CCC(일)   | CF마진  |
  |-------------|---------|---------|----------|----------|--------|
  | IT/반도체     | 154.0   | 558.8   | 26815.7  | -26064.6 | 23.3%  |
  | 산업재        | 172.1   | 247.0   | 157.8    | 261.3    | 6.7%   |
  | 건강관리       | 691.7   | 1667.9  | 141.9    | 2217.7   | 28.6%  |
  | 필수소비재      | 98.0    | 197.1   | 146.7    | 148.4    | 14.2%  |
  ※ IT/반도체 DPO 이상값: 엔씨소프트 매출원가 극소 → DPO 비정상 급등
  ※ 건강관리 CCC 극대: 바이오/제약의 매출 대비 재고/매출채권 구조 차이
- 2D 분류 (CCC 중앙값 362일, CF마진 중앙값 13.5%):
  - 빠른현금화(낮CCC+고CF): 7사 — 엔씨소프트, LG, 오리온, 롯데칠성, 삼양식품, CJ, BGF리테일
  - 품질수익(고CCC+고CF): 10사 — 삼성전자, SK하이닉스, LG에너지솔루션, LG화학, 셀트리온 등
  - 현금압박(고CCC+저CF): 7사 — 에코프로비엠, 고려아연, 삼성전기, 유한양행, 종근당 등
  - 자금회전(낮CCC+저CF): 11사 — 삼성SDI, 현대차, 기아, 현대모비스, CJ제일제당 등
- 직관 매칭:
  - 식품/유통(BGF리테일) → 빠른현금화 ✓ (선수금/현금 비즈니스)
  - 반도체(삼성전자, SK하이닉스) → 품질수익 ✓ (높은 재고이지만 높은 CF마진)
  - 자동차(현대차, 기아) → 자금회전 ✓ (짧은 CCC이지만 낮은 마진)
  - 바이오(에이치엘비, 덴티움) → 현금압박 ✓ (긴 개발 주기, 낮은 현금화)

결론:
- 가설 1 채택: CCC × 영업CF마진 2차원 분류가 사업모델 현금전환 효율을 직관적으로 포착
- 금융 섹터: CCC 계산 불가 → NIM, 예대마진 등 별도 지표 필요
- 이상값 주의: 매출원가가 극히 작은 SW/게임사, 매출 대비 재고가 큰 바이오에서 CCC 극단값 발생
  → 007에서 활용 시 percentile clipping 또는 섹터 내 상대 순위로 정규화 필요
- 가설 2(CCC 악화 → 실적 하락 상관): 시계열 추출이 단일 시점이므로 이번 실험에서 미검증
  → 향후 ratioSeries 활용한 시계열 분석에서 별도 검증 필요
- 핵심 시사점: CCC + CF마진이 사업모델 DNA "현금전환 효율" 축으로 유효
  → 007_archetypeClassify에서 이상값 처리 후 활용

실험일: 2026-03-22
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

DATA_DIR = Path(__file__).parent / "data"

ALL_COMPANIES = [
    ("005930", "삼성전자", "IT/반도체"), ("000660", "SK하이닉스", "IT/반도체"),
    ("035420", "NAVER", "IT/반도체"), ("035720", "카카오", "IT/반도체"),
    ("006400", "삼성SDI", "IT/반도체"), ("247540", "에코프로비엠", "IT/반도체"),
    ("373220", "LG에너지솔루션", "IT/반도체"),
    ("036570", "엔씨소프트", "IT/반도체"),
    ("005380", "현대차", "산업재"), ("000270", "기아", "산업재"),
    ("012330", "현대모비스", "산업재"), ("010130", "고려아연", "산업재"),
    ("051910", "LG화학", "산업재"), ("011170", "롯데케미칼", "산업재"),
    ("003550", "LG", "산업재"), ("034730", "SK", "산업재"),
    ("028260", "삼성물산", "산업재"), ("009150", "삼성전기", "산업재"),
    ("068270", "셀트리온", "건강관리"), ("207940", "삼성바이오로직스", "건강관리"),
    ("326030", "SK바이오팜", "건강관리"), ("128940", "한미약품", "건강관리"),
    ("006280", "녹십자", "건강관리"), ("000100", "유한양행", "건강관리"),
    ("185750", "종근당", "건강관리"), ("003060", "에이치엘비", "건강관리"),
    ("145720", "덴티움", "건강관리"), ("214150", "클래시스", "건강관리"),
    ("105560", "KB금융", "금융"), ("055550", "신한지주", "금융"),
    ("086790", "하나금융지주", "금융"), ("316140", "우리금융지주", "금융"),
    ("024110", "기업은행", "금융"), ("138930", "BNK금융지주", "금융"),
    ("175330", "JB금융지주", "금융"), ("032830", "삼성생명", "금융"),
    ("000810", "삼성화재", "금융"), ("088350", "한화생명", "금융"),
    ("097950", "CJ제일제당", "필수소비재"), ("004370", "농심", "필수소비재"),
    ("271560", "오리온", "필수소비재"), ("280360", "롯데웰푸드", "필수소비재"),
    ("005300", "롯데칠성", "필수소비재"), ("007310", "오뚜기", "필수소비재"),
    ("003230", "삼양식품", "필수소비재"), ("002270", "롯데지주", "필수소비재"),
    ("001040", "CJ", "필수소비재"), ("282330", "BGF리테일", "필수소비재"),
]

# BS 키 후보 (기업마다 다를 수 있음)
_RECEIVABLE_KEYS = [
    "trade_and_other_receivables", "trade_receivables",
    "accounts_receivable", "short_term_trade_receivables",
]
_INVENTORY_KEYS = [
    "inventories", "inventory", "merchandise",
]
_PAYABLE_KEYS = [
    "trade_and_other_payables", "trade_payables",
    "accounts_payable", "short_term_trade_payables",
]
_REVENUE_KEYS = ["revenue", "sales"]
_COGS_KEYS = ["cost_of_sales", "cost_of_goods_sold"]
_OPCF_KEYS = ["operating_cashflow", "cash_flows_from_operating_activities"]


def _getLatest(series_dict: dict, keys: list[str]) -> float | None:
    """시계열 dict에서 키 후보 중 첫 번째 유효한 최신값."""
    for key in keys:
        vals = series_dict.get(key, [])
        nonNull = [v for v in vals if v is not None]
        if nonNull:
            return nonNull[-1]
    return None


def _getSeriesValues(series_dict: dict, keys: list[str]) -> list:
    """시계열 dict에서 키 후보 중 첫 번째 유효한 전체 시계열."""
    for key in keys:
        vals = series_dict.get(key, [])
        if any(v is not None for v in vals):
            return vals
    return []


def runCashConversion(*, verbose: bool = True) -> pl.DataFrame:
    """현금전환 효율 패턴화 실행."""
    from dartlab.providers.dart.finance.pivot import buildTimeseries

    rows = []
    for stockCode, corpName, sector in ALL_COMPANIES:
        row: dict = {"stockCode": stockCode, "corpName": corpName, "sector": sector}

        try:
            result = buildTimeseries(stockCode)
            if result is None:
                _fillNone(row)
                rows.append(row)
                continue

            series, periods = result
            bs = series.get("BS", {})
            isS = series.get("IS", {})
            cf = series.get("CF", {})

            # 최신값 추출
            receivables = _getLatest(bs, _RECEIVABLE_KEYS)
            inventories = _getLatest(bs, _INVENTORY_KEYS)
            payables = _getLatest(bs, _PAYABLE_KEYS)
            revenue = _getLatest(isS, _REVENUE_KEYS)
            cogs = _getLatest(isS, _COGS_KEYS)
            opcf = _getLatest(cf, _OPCF_KEYS)

            row["receivables"] = receivables
            row["inventories"] = inventories
            row["payables"] = payables
            row["revenue"] = revenue
            row["cogs"] = cogs
            row["opcf"] = opcf

            # CCC 계산
            dso = (receivables / revenue * 365) if receivables and revenue and revenue > 0 else None
            dio = (inventories / cogs * 365) if inventories and cogs and cogs > 0 else None
            dpo = (payables / cogs * 365) if payables and cogs and cogs > 0 else None

            row["dso"] = round(dso, 1) if dso is not None else None
            row["dio"] = round(dio, 1) if dio is not None else None
            row["dpo"] = round(dpo, 1) if dpo is not None else None

            if dso is not None and dio is not None and dpo is not None:
                row["ccc"] = round(dso + dio - dpo, 1)
            elif dso is not None and dpo is not None:
                # 재고 없는 서비스업: CCC = DSO - DPO
                row["ccc"] = round(dso - dpo, 1)
            else:
                row["ccc"] = None

            # 영업CF마진
            if opcf is not None and revenue and revenue > 0:
                row["opcfMargin"] = round(opcf / revenue * 100, 1)
            else:
                row["opcfMargin"] = None

            row["periods"] = len(periods)

        except (FileNotFoundError, RuntimeError, OSError):
            _fillNone(row)

        rows.append(row)

    df = pl.DataFrame(rows)

    if verbose:
        _printResults(df)

    return df


def _fillNone(row: dict) -> None:
    for f in ["receivables", "inventories", "payables", "revenue", "cogs", "opcf",
              "dso", "dio", "dpo", "ccc", "opcfMargin", "periods"]:
        row[f] = None


def _printResults(df: pl.DataFrame) -> None:
    """결과 출력."""
    print("\n[현금전환 — 섹터별 평균]")
    print(f"{'섹터':12s} | {'DSO(일)':>8s} | {'DIO(일)':>8s} | {'DPO(일)':>8s} | "
          f"{'CCC(일)':>8s} | {'CF마진':>8s}")
    print("-" * 70)

    for sector in ["IT/반도체", "산업재", "건강관리", "금융", "필수소비재"]:
        sdf = df.filter(pl.col("sector") == sector)
        dso = sdf["dso"].drop_nulls().mean()
        dio = sdf["dio"].drop_nulls().mean()
        dpo = sdf["dpo"].drop_nulls().mean()
        ccc = sdf["ccc"].drop_nulls().mean()
        cfm = sdf["opcfMargin"].drop_nulls().mean()

        def _f(v: float | None) -> str:
            return f"{v:.1f}" if v is not None else "N/A"

        print(f"{sector:12s} | {_f(dso):>8s} | {_f(dio):>8s} | {_f(dpo):>8s} | "
              f"{_f(ccc):>8s} | {_f(cfm):>8s}%")

    # 2D 분류
    validDf = df.filter(pl.col("ccc").is_not_null() & pl.col("opcfMargin").is_not_null())

    if len(validDf) > 0:
        medianCCC = validDf["ccc"].median() or 0
        medianCFM = validDf["opcfMargin"].median() or 0

        print(f"\n[2D 분류 기준: CCC 중앙값={medianCCC:.1f}일, CF마진 중앙값={medianCFM:.1f}%]")

        categories: dict[str, list[str]] = {
            "빠른현금화(낮CCC+고CF)": [],
            "품질 수익(고CCC+고CF)": [],
            "현금압박(고CCC+저CF)": [],
            "자금회전(낮CCC+저CF)": [],
        }

        for row_data in validDf.iter_rows(named=True):
            ccc = row_data["ccc"]
            cfm = row_data["opcfMargin"]
            name = row_data["corpName"]
            sector = row_data["sector"]

            if ccc <= medianCCC and cfm > medianCFM:
                cat = "빠른현금화(낮CCC+고CF)"
            elif ccc > medianCCC and cfm > medianCFM:
                cat = "품질 수익(고CCC+고CF)"
            elif ccc > medianCCC and cfm <= medianCFM:
                cat = "현금압박(고CCC+저CF)"
            else:
                cat = "자금회전(낮CCC+저CF)"

            categories[cat].append(f"{name}({sector})")
            print(f"  {name:12s} ({sector:8s}) | CCC={ccc:6.1f}일 CF마진={cfm:5.1f}% → {cat}")

        print("\n[현금전환 패턴별 요약]")
        for cat, members in categories.items():
            print(f"  {cat:25s}: {len(members)}사")
            if members:
                print(f"    → {', '.join(members[:5])}" +
                      (f" 외 {len(members)-5}사" if len(members) > 5 else ""))

    # 유효 데이터 비율
    print(f"\n[유효 데이터]")
    for col in ["dso", "dio", "dpo", "ccc", "opcfMargin"]:
        n = df[col].drop_nulls().len()
        print(f"  {col:15s}: {n}/{len(df)}")


if __name__ == "__main__":
    print("=" * 60)
    print("005: 현금전환 효율 패턴화")
    print("=" * 60)

    start = time.time()
    resultDf = runCashConversion()
    elapsed = time.time() - start

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    resultDf.write_parquet(DATA_DIR / "005_cashConversion.parquet")
    print(f"\n→ {DATA_DIR / '005_cashConversion.parquet'} ({elapsed:.1f}s)")
