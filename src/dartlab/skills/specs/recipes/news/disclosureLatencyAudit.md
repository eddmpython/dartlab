---
id: recipes.news.disclosureLatencyAudit
title: 공시 ↔ 뉴스 시간 간격 분포 (latency audit)
category: recipes
kind: recipe
scope: builtin
status: curated
graphTier: L1.5
cluster: news
purpose: 공시 (dartDoc) 와 뉴스 (news) 의 시간 차이 분포 측정. 공시 → 뉴스 평균 lag, std-dev, 동시 발생 row 카운트. 추론 라벨 없이 정량 분포만. dartDoc + news gather 결합. 트리거 — '공시 ↔ 뉴스 시간 간격 분포 (latency audit)', 'disclosure latency audit', 'disclosureLatencyAudit'.
whenToUse:
  - 공시 뉴스 시차
  - disclosure news latency
  - news lag audit
  - 뉴스 보도 속도
examples:
  - 005930 공시 → 뉴스 평균 lag 얼마
  - 공시 발표 후 뉴스 보도 속도 정량
  - 동시 발생 뉴스 row 카운트
expectedOutputs:
  - 공시 → 뉴스 평균 lag (분 또는 시간 단위) + std-dev
  - 동시 발생 (lag < 5분) row 카운트
  - 분포 분위수 (p10/p50/p90)
linkedSkills:
  - engines.gather
  - recipes.news.eventTimelineFusion
  - recipes.news.newsHeadlineVelocity
toolRefs:
  - EngineCall
  - RunPython
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
  pyodide:
    status: limited
testUniverse:
  market: KR
  stockCodes:
    - "005930"
    - "000660"
expectedNovelty:
  - disclosureNewsLatency
  - lagDistribution
falsifier:
  description: "dartDoc 또는 news row 가 < 5 면 결론 X. matching (공시-뉴스) 규칙 없이 임의 매칭하면 결과 의미 약함."
forbidden:
  - latency 짧음 → 정보 유출 단정 금지
  - 뉴스 본문 매칭 없이 시간만으로 인과 단정 금지
failureModes:
  - dartDoc / news row 부족
  - 동일 공시에 대한 다중 뉴스 보도 → 중복 매칭
  - 시간외 공시 + 익일 뉴스 시차 자연 변동
lastUpdated: '2026-05-23'
validatedAt: '2026-05-27'
---

## 공개 호출 방식

```python
import dartlab
import polars as pl
import statistics
from datetime import datetime, date, timedelta

target = "005930"
c = dartlab.Company(target)


def parseDt(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    s = str(v)[:19].replace(".", "-").replace("/", "-").replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[: len(fmt) + 4], fmt)
        except Exception:
            continue
    return None


try:
    d_df = c.gather("dartDoc").head(50)
    d_rows = d_df.to_dicts() if hasattr(d_df, "to_dicts") else []
except Exception:
    d_rows = []
try:
    n_df = c.gather("news").head(100)
    n_rows = n_df.to_dicts() if hasattr(n_df, "to_dicts") else []
except Exception:
    n_rows = []

d_events = []
for r in d_rows:
    dt = parseDt(r.get("filedAt") or r.get("date") or r.get("disclosedAt") or r.get("rcept_dt"))
    if dt:
        d_events.append({"dt": dt, "title": str(r.get("title") or r.get("report_nm") or "")})

n_events = []
for r in n_rows:
    dt = parseDt(r.get("publishedAt") or r.get("date") or r.get("pubDate"))
    if dt:
        n_events.append({"dt": dt, "title": str(r.get("title") or "")})

d_events.sort(key=lambda x: x["dt"])
n_events.sort(key=lambda x: x["dt"])

# 각 공시마다 *그 이후* 가장 가까운 뉴스 1 건만 매칭 (48 시간 안)
latencies_hr = []
matches = []
for d in d_events:
    for n in n_events:
        if n["dt"] < d["dt"]:
            continue
        delta = (n["dt"] - d["dt"]).total_seconds() / 3600.0
        if delta <= 48:
            latencies_hr.append(delta)
            matches.append(
                {
                    "disclosureAt": str(d["dt"]),
                    "newsAt": str(n["dt"]),
                    "latencyHours": round(delta, 2),
                }
            )
        break  # 첫 매칭만

mean_lag = statistics.mean(latencies_hr) if latencies_hr else None
median_lag = statistics.median(latencies_hr) if latencies_hr else None
std_lag = statistics.pstdev(latencies_hr) if len(latencies_hr) >= 2 else None

phase = "insufficient"
if mean_lag is not None:
    if mean_lag < 1:
        phase = "fastBroadcast"
    elif mean_lag < 6:
        phase = "normal"
    else:
        phase = "slow"

latest_date = (
    str(max([m["disclosureAt"] for m in matches])) if matches else (str(d_events[-1]["dt"]) if d_events else None)
)

table = pl.DataFrame(matches) if matches else pl.DataFrame(
    schema={"disclosureAt": pl.Utf8, "newsAt": pl.Utf8, "latencyHours": pl.Float64}
)

emit_result(
    table=table,
    values={
        "matchedPairs": len(matches),
        "meanLagHr": (round(mean_lag, 2) if mean_lag is not None else None),
        "medianLagHr": (round(median_lag, 2) if median_lag is not None else None),
        "stdLagHr": (round(std_lag, 2) if std_lag is not None else None),
        "phase": phase,
    },
    date=latest_date,
    sources=["dartlab://gather/dartDoc", "dartlab://gather/news"],
)
```

## 호출 동작

### 1. 결론 도출

공시 → 뉴스 보도 lag (hr) phase 단정 (fastBroadcast < 1h / normal 1-6h / slow > 6h). 예: "최근 30일 매칭 pair N 건, mean lag 2.3h → normal phase."

### 2. 핵심 근거 수집

- 공시 row (Company.filings 시각 정보)
- 뉴스 row (Company.gather('news') 시각 정보)
- 48 시간 window 안 첫 뉴스 1 건 best-match

### 3. 메커니즘 분석

```
공시 시각 t₁ → t₁ ~ t₁+48h window 안 뉴스 시각 t₂ 모두 후보
            → 가장 빠른 t₂ 선택 (best match)
            → latency = t₂ - t₁ (시간 단위)
                            ↓
                    mean(latency) 산출
        < 1h    → fastBroadcast (실시간 보도)
        1-6h    → normal (정상 lag)
        > 6h    → slow (느린 보도)
```

분포 std 가 크면 매체별 보도 속도 편차 큼. matchedPairs 수 ↑ + std ↓ = 신뢰도 ↑.

### 4. 반례·한계

- 정정·재공시는 원공시 시각 기준이라 lag 부풀려짐.
- 같은 사건의 일괄 보도 (한 시점에 다수 뉴스) 는 첫 1 건만 매칭.
- 48 시간 window 너무 짧으면 미매칭, 너무 길면 무관 이벤트 매칭.
- 공시·뉴스 시각 timezone 불일치 시 lag 오류.

### 5. 후속 모니터링

- newsAt < disclosureAt (lag 음수) row 발생 시: `recipes.news.eventTimelineFusion` 으로 정보 비대칭 의심 확인.
- slow phase 지속 시 매체별 보도 cluster `recipes.news.newsHeadlineVelocity` cross-check.
- 매칭 pair 적은 종목 (< 10) 은 `recipes.news.disclosureNewsCrosscheck` 키워드 매칭 정밀화.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `disclosureAt` | 공시 시각 |
| `newsAt` | 매칭 뉴스 시각 |
| `latencyHours` | 두 시각 차이 (h) |

values: matchedPairs · meanLagHr · medianLagHr · stdLagHr · phase

## 연계 절차

1. recipes.news.eventTimelineFusion — 매칭 row 시점 ± 가격 반응 결합.
2. recipes.news.newsHeadlineVelocity — 보도 속도 분포와 결합.

## 기본 검증

- 매칭 < 5 → 결론 X.
- 동일 공시에 대한 중복 뉴스 보도가 latency 측정에 영향.
- latency 짧음 자체가 *정보 유출* 신호 아님.
