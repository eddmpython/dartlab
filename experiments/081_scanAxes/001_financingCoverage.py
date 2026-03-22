"""실험 ID: 081-001
실험명: financing 축 후보 coverage 검증

목적:
- financing 축 후보가 실제로 시장에서 쓸 만한 커버리지를 가지는지 확인
- capitalChange / publicOfferingUsage / privateOfferingUsage / stockTotal 네 소스의 최근성, 중복도, 결합 범위를 계량화
- promotion gate의 coverage 조건(60% 이상 또는 1,500사 이상) 충족 여부를 먼저 판정

가설:
1. 최근 자금조달 증거를 만들 수 있는 기업이 1,500사 이상이다
2. capitalChange 단독보다 public/private usage를 결합했을 때 usable coverage가 의미 있게 넓어진다
3. stockTotal 기반 주식수 증가율은 capitalChange가 놓치는 추가 희석 후보를 보완한다

방법:
1. capitalChange, publicOfferingUsage, privateOfferingUsage, stockTotal를 전수 스캔
2. 최근성 기준은 2023년 이상 pay_de / isu_dcrs_de로 통일
3. public/private usage는 (stockCode, pay_de, se_nm) 기준으로 deduplicate
4. stockTotal은 연도별로 합계 > 보통주 우선, 2025 없으면 2024 기준 최신 snapshot을 선택
5. 네 소스를 union하여 company-level financing feature universe를 계산

결과 (실험 후 작성):
- source coverage:
  - capitalChange: 910,971행 / 2,655사, 최근증자 1,239사
  - publicOfferingUsage: 162,737행 / 2,576사, 최근 dedup 1,527이벤트 / 635사
  - privateOfferingUsage: 208,378행 / 2,575사, 최근 dedup 3,475이벤트 / 968사
  - stockTotal: 337,148행 / 2,624사, 주식수 증가율 계산 가능 2,615사 / +5% 이상 817사
- usable financing feature universe: 1,634사
  - capitalChange universe 2,655사 대비 61.5%
  - promotion gate 기준인 1,500사 이상도 동시에 충족
- 결합 후 경로 분포:
  - 사모 628 / 혼합 340 / 증자전용 338 / 공모 295 / 주식수증가전용 33
- sample explainable row:
  - 000040 KR모터스: 혼합, 최근증자=True, 사용근거=True, 사용불일치=True, 대표경로=주주배정후 실권주 일반공모 유상증자

결론:
- 가설1 채택: usable coverage 1,634사로 gate 통과
- 가설2 채택: capitalChange 최근증자 1,239사에서 usage/stockTotal 결합 후 1,634사로 확대 (+395사)
- 가설3 채택: stockTotal만으로 추가 포착되는 주식수증가전용 33사, capitalChange 비포착 +5% 희석 후보 52사를 확보
- financing 축은 coverage 관점에서 실험 지속 가치가 충분하다

실험일: 2026-03-20
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from dartlab.engines.company.dart.scan._helpers import load_listing, parse_date_year, parse_num, scan_parquets
from dartlab.engines.company.dart.scan.capital.scanner import scan_capital_change

SUM_LABEL = "합계"
COMMON_LABEL = "보통주"
LATEST_CANDIDATE_YEARS = ("2025", "2024")
BASE_CANDIDATE_YEARS = ("2022", "2023", "2021")
QUARTER_ORDER = {"4분기": 4, "3분기": 3, "2분기": 2, "1분기": 1}


def nonblank(value: object) -> bool:
    """빈 문자열/하이픈을 제외한 유효 텍스트 여부."""
    if value is None:
        return False
    return str(value).strip() not in {"", "-"}


def _recent_usage(apiType: str, planCols: list[str]) -> tuple[pl.DataFrame, dict[str, dict], pl.DataFrame]:
    """최근 공모/사모 usage raw와 company-level 요약을 만든다."""
    cols = [
        "stockCode",
        "year",
        "quarter",
        "se_nm",
        "pay_de",
        "real_cptal_use_dtls_cn",
        "dffrnc_occrrnc_resn",
        "real_cptal_use_sttus",
        *planCols,
    ]
    raw = scan_parquets(apiType, cols)
    if raw.is_empty():
        return raw, {}, raw

    recent = raw.with_columns(
        pl.col("pay_de").map_elements(parse_date_year, return_dtype=pl.Int32).alias("event_year")
    ).filter(pl.col("event_year").is_not_null() & (pl.col("event_year") >= 2023))

    if recent.is_empty():
        return raw, {}, recent

    recent = recent.unique(subset=["stockCode", "pay_de", "se_nm"], keep="first")

    info: dict[str, dict] = {}
    for key, group in recent.group_by("stockCode"):
        stockCode = key[0]
        labelCounts: Counter[str] = Counter()
        usageDetail = False
        mismatch = False
        status = False
        plan = False
        rows: list[dict[str, object]] = []

        for row in group.iter_rows(named=True):
            label = str(row.get("se_nm") or "").strip()
            if label and label != "-":
                labelCounts[label] += 1

            usageDetail = usageDetail or nonblank(row.get("real_cptal_use_dtls_cn"))
            mismatch = mismatch or nonblank(row.get("dffrnc_occrrnc_resn"))
            status = status or nonblank(row.get("real_cptal_use_sttus"))
            plan = plan or any(nonblank(row.get(col)) for col in planCols)
            rows.append(row)

        info[stockCode] = {
            "events": group.height,
            "topLabel": labelCounts.most_common(1)[0][0] if labelCounts else "",
            "usageDetail": usageDetail,
            "mismatch": mismatch,
            "status": status,
            "plan": plan,
            "rows": rows,
        }

    return raw, info, recent


def _stock_growth_map() -> tuple[pl.DataFrame, dict[str, dict]]:
    """stockTotal에서 최근 3년 내 주식수 증가율을 계산한다."""
    raw = scan_parquets("stockTotal", ["stockCode", "year", "quarter", "se", "istc_totqy"])
    if raw.is_empty():
        return raw, {}

    valid = raw.filter(
        pl.col("se").is_in([SUM_LABEL, COMMON_LABEL])
        & pl.col("istc_totqy").is_not_null()
        & (pl.col("istc_totqy") != "-")
        & (pl.col("istc_totqy") != "")
    )

    history: dict[str, dict[str, dict[str, float | str]]] = {}
    for key, group in valid.group_by(["stockCode", "year"]):
        stockCode, year = key
        candidates: list[tuple[int, int, float, str, str]] = []
        for row in group.iter_rows(named=True):
            qty = parse_num(row.get("istc_totqy"))
            if qty is None:
                continue
            se = str(row.get("se") or "")
            quarter = str(row.get("quarter") or "")
            candidates.append(
                (
                    2 if se == SUM_LABEL else 1,
                    QUARTER_ORDER.get(quarter, 0),
                    qty,
                    quarter,
                    se,
                )
            )

        if not candidates:
            continue

        candidates.sort(reverse=True)
        best = candidates[0]
        history.setdefault(stockCode, {})[str(year)] = {
            "qty": best[2],
            "quarter": best[3],
            "se": best[4],
        }

    growthMap: dict[str, dict] = {}
    for stockCode, years in history.items():
        latestYear = next((y for y in LATEST_CANDIDATE_YEARS if y in years), None)
        if latestYear is None:
            latestYear = max(years)

        baseYear = next((y for y in BASE_CANDIDATE_YEARS if y in years and y < latestYear), None)
        if baseYear is None:
            olderYears = sorted(y for y in years if y < latestYear)
            if not olderYears:
                continue
            baseYear = olderYears[-1]

        latestQty = float(years[latestYear]["qty"])
        baseQty = float(years[baseYear]["qty"])
        if baseQty <= 0:
            continue

        growthPct = (latestQty / baseQty - 1.0) * 100.0
        growthMap[stockCode] = {
            "latestYear": latestYear,
            "baseYear": baseYear,
            "latestQty": latestQty,
            "baseQty": baseQty,
            "growthPct": growthPct,
            "diluted": growthPct >= 5.0,
        }

    return raw, growthMap


def buildFinancingArtifacts() -> dict[str, object]:
    """financing coverage/feature 계산 결과 일괄 생성."""
    _, _, _, listingMeta = load_listing()

    capRaw = scan_parquets("capitalChange", ["stockCode", "isu_dcrs_stle", "isu_dcrs_de"])
    capRecentMap = scan_capital_change()
    capitalRecent = {code for code, value in capRecentMap.items() if next(iter(value.values()))}

    publicRaw, publicInfo, publicRecent = _recent_usage(
        "publicOfferingUsage",
        ["rs_cptal_use_plan_useprps", "on_dclrt_cptal_use_plan"],
    )
    privateRaw, privateInfo, privateRecent = _recent_usage(
        "privateOfferingUsage",
        ["cptal_use_plan"],
    )
    stockRaw, stockGrowth = _stock_growth_map()
    stockDiluted = {code for code, value in stockGrowth.items() if value["diluted"]}

    universe = sorted(set(capitalRecent) | set(publicInfo) | set(privateInfo) | stockDiluted)

    evidenceMap: dict[str, dict] = {}
    featureRows: list[dict[str, object]] = []
    for stockCode in universe:
        public = publicInfo.get(stockCode)
        private = privateInfo.get(stockCode)
        capitalFlag = stockCode in capitalRecent
        shareGrowth = stockGrowth.get(stockCode, {})

        publicFlag = public is not None
        privateFlag = private is not None
        if publicFlag and privateFlag:
            route = "혼합"
        elif publicFlag:
            route = "공모"
        elif privateFlag:
            route = "사모"
        elif capitalFlag:
            route = "증자전용"
        else:
            route = "주식수증가전용"

        usageEvidence = any(info and (info["usageDetail"] or info["status"]) for info in (public, private))
        planPresent = any(info and info["plan"] for info in (public, private))
        mismatchFlag = any(info and info["mismatch"] for info in (public, private))
        dilutionFlag = capitalFlag or stockCode in stockDiluted
        routeHint = (
            public["topLabel"]
            if public and public["topLabel"]
            else private["topLabel"]
            if private and private["topLabel"]
            else ""
        )

        featureRows.append(
            {
                "종목코드": stockCode,
                "회사명": listingMeta.get(stockCode, {}).get("name", ""),
                "최근조달여부": True,
                "조달경로": route,
                "공모조달": publicFlag,
                "사모조달": privateFlag,
                "최근증자": capitalFlag,
                "사용근거": usageEvidence,
                "사용계획": planPresent,
                "사용불일치": mismatchFlag,
                "희석신호": dilutionFlag,
                "주식수증가율_%": round(float(shareGrowth.get("growthPct", 0.0)), 2),
                "대표경로": routeHint,
                "공모이벤트수": public["events"] if public else 0,
                "사모이벤트수": private["events"] if private else 0,
            }
        )

        evidenceMap[stockCode] = {
            "publicRows": public["rows"] if public else [],
            "privateRows": private["rows"] if private else [],
            "capitalRecent": capitalFlag,
            "shareGrowth": shareGrowth,
        }

    features = pl.DataFrame(featureRows).sort(["조달경로", "종목코드"])
    if features.is_empty():
        features = pl.DataFrame(
            schema={
                "종목코드": pl.Utf8,
                "회사명": pl.Utf8,
                "최근조달여부": pl.Boolean,
                "조달경로": pl.Utf8,
                "공모조달": pl.Boolean,
                "사모조달": pl.Boolean,
                "최근증자": pl.Boolean,
                "사용근거": pl.Boolean,
                "사용계획": pl.Boolean,
                "사용불일치": pl.Boolean,
                "희석신호": pl.Boolean,
                "주식수증가율_%": pl.Float64,
                "대표경로": pl.Utf8,
                "공모이벤트수": pl.Int64,
                "사모이벤트수": pl.Int64,
            }
        )

    sourceSummary = pl.DataFrame(
        [
            {
                "source": "capitalChange",
                "rawRows": capRaw.height,
                "rawCompanies": capRaw["stockCode"].n_unique() if not capRaw.is_empty() else 0,
                "recentRows": None,
                "recentCompanies": len(capitalRecent),
            },
            {
                "source": "publicOfferingUsage",
                "rawRows": publicRaw.height,
                "rawCompanies": publicRaw["stockCode"].n_unique() if not publicRaw.is_empty() else 0,
                "recentRows": publicRecent.height,
                "recentCompanies": len(publicInfo),
            },
            {
                "source": "privateOfferingUsage",
                "rawRows": privateRaw.height,
                "rawCompanies": privateRaw["stockCode"].n_unique() if not privateRaw.is_empty() else 0,
                "recentRows": privateRecent.height,
                "recentCompanies": len(privateInfo),
            },
            {
                "source": "stockTotal",
                "rawRows": stockRaw.height,
                "rawCompanies": stockRaw["stockCode"].n_unique() if not stockRaw.is_empty() else 0,
                "recentRows": len(stockGrowth),
                "recentCompanies": len(stockDiluted),
            },
        ]
    )

    routeSummary = (
        features.group_by("조달경로")
        .agg(pl.len().alias("companies"))
        .sort("companies", descending=True)
    )

    coverageSummary = {
        "usableCompanies": features.height,
        "capitalUniverse": capRaw["stockCode"].n_unique() if not capRaw.is_empty() else 0,
        "publicRecentCompanies": len(publicInfo),
        "privateRecentCompanies": len(privateInfo),
        "capitalRecentCompanies": len(capitalRecent),
        "stockGrowthCompanies": len(stockGrowth),
        "stockDilutedCompanies": len(stockDiluted),
        "stockOnlyCompanies": features.filter(pl.col("조달경로") == "주식수증가전용").height,
        "shareGrowthOnlyCompanies": features.filter((pl.col("주식수증가율_%") >= 5.0) & (~pl.col("최근증자"))).height,
        "coveragePct": round(
            features.height / capRaw["stockCode"].n_unique() * 100,
            1,
        )
        if not capRaw.is_empty()
        else 0.0,
    }

    return {
        "features": features,
        "sourceSummary": sourceSummary,
        "routeSummary": routeSummary,
        "coverageSummary": coverageSummary,
        "evidenceMap": evidenceMap,
    }


def buildFinancingClassifier(features: pl.DataFrame) -> pl.DataFrame:
    """feature table 위에 financing 분류 초안을 얹는다."""
    if features.is_empty():
        return features.with_columns(pl.lit(None).alias("분류초안"))

    return features.with_columns(
        pl.when(pl.col("사용불일치"))
        .then(pl.lit("불일치주의형"))
        .when(pl.col("조달경로") == "혼합")
        .then(pl.lit("혼합집행형"))
        .when(pl.col("조달경로") == "공모")
        .then(pl.lit("공모집행형"))
        .when(pl.col("조달경로") == "사모")
        .then(pl.lit("사모집행형"))
        .otherwise(pl.lit("희석주의형"))
        .alias("분류초안")
    )


def _pick_usage_row(rows: list[dict], *, preferMismatch: bool) -> dict | None:
    """수동 explainability용 대표 raw row를 고른다."""
    if not rows:
        return None

    if preferMismatch:
        for row in rows:
            if nonblank(row.get("dffrnc_occrrnc_resn")):
                return row

    return max(rows, key=lambda row: str(row.get("pay_de") or ""))


def _format_usage_row(row: dict | None) -> str:
    """raw row를 한 줄 설명 문자열로 압축한다."""
    if row is None:
        return ""

    parts: list[str] = []
    for key in ("pay_de", "se_nm", "real_cptal_use_dtls_cn", "dffrnc_occrrnc_resn"):
        value = row.get(key)
        if nonblank(value):
            parts.append(str(value).replace("\n", " ").strip())
    return " | ".join(parts)


def buildExplainableSamples(
    classified: pl.DataFrame,
    evidenceMap: dict[str, dict],
    *,
    perClass: int = 2,
) -> pl.DataFrame:
    """분류별 수동 검증용 sample table 생성."""
    rows: list[dict[str, object]] = []
    for label in ["불일치주의형", "혼합집행형", "공모집행형", "사모집행형", "희석주의형"]:
        sub = classified.filter(pl.col("분류초안") == label).sort("종목코드").head(perClass)
        for sample in sub.iter_rows(named=True):
            stockCode = sample["종목코드"]
            evidence = evidenceMap.get(stockCode, {})
            publicRow = _pick_usage_row(evidence.get("publicRows", []), preferMismatch=label == "불일치주의형")
            privateRow = _pick_usage_row(evidence.get("privateRows", []), preferMismatch=label == "불일치주의형")
            shareGrowth = evidence.get("shareGrowth", {})

            rows.append(
                {
                    "종목코드": stockCode,
                    "회사명": sample["회사명"],
                    "분류초안": label,
                    "조달경로": sample["조달경로"],
                    "대표경로": sample["대표경로"],
                    "최근증자": sample["최근증자"],
                    "사용불일치": sample["사용불일치"],
                    "주식수증가율_%": sample["주식수증가율_%"],
                    "공모증거": _format_usage_row(publicRow),
                    "사모증거": _format_usage_row(privateRow),
                    "주식수근거": (
                        f"{shareGrowth['baseYear']}->{shareGrowth['latestYear']} "
                        f"{int(shareGrowth['baseQty']):,}->{int(shareGrowth['latestQty']):,}"
                        if shareGrowth
                        else ""
                    ),
                }
            )

    return pl.DataFrame(rows)


if __name__ == "__main__":
    artifacts = buildFinancingArtifacts()
    features = artifacts["features"]
    coverage = artifacts["coverageSummary"]

    print("=== financing coverage ===")
    print(artifacts["sourceSummary"])
    print()
    print(
        f"usableCompanies={coverage['usableCompanies']} "
        f"coveragePct={coverage['coveragePct']}% "
        f"shareGrowthOnly={coverage['shareGrowthOnlyCompanies']}"
    )
    print()
    print(artifacts["routeSummary"])
    print()
    if not features.is_empty():
        print("sample feature row")
        print(features.filter(pl.col("종목코드") == "000040").head(1))
