---
id: recipes.news.disclosureNewsCrosscheck
title: Disclosure News Crosscheck
category: recipes
kind: recipe
scope: builtin
status: curated
graphTier: L1.5
cluster: news
purpose: DART 공시 (1 차 출처) 와 Naver 뉴스 헤드라인 (외부 untrusted) 를 같은 ±1 day window 안에서 회사명·키워드·이벤트 단어로 매칭해 정합성을 보는 절차다. 트리거 — 'Disclosure News Crosscheck', 'disclosure news crosscheck', 'disclosureNewsCrosscheck'.
whenToUse:
  - 공시 뉴스 정합성
  - 뉴스 선행 vs 공시 선행 확인
  - 1 차 출처 검증 루프
inputs:
  - filing rows
  - news rows
outputs:
  - disclosureNewsCrosscheck table
capabilityRefs:
  - Company.filings
  - Company.filings
  - Company.gather
toolRefs:
  - EngineCall
  - RunPython
knowledgeRefs:
  - runtime.untrustedContent
  - engines.company
  - engines.gather
sourceRefs:
  - dartlab://skills/recipes.news.disclosureNewsCrosscheck
requiredEvidence:
  - skillRef
  - tableRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - matched / dartOnly / newsOnly row 분류
  - 시간차 (뉴스 선행 vs 공시 선행) 일 수
  - 키워드 매칭 점수
visualRefs:
  - engines.viz.evidenceCoverage
visualGuidance:
  - "disclosureNewsCrosscheck 는 표 우선이며 matched/dartOnly/newsOnly 분포만 engines.viz.evidenceCoverage 로 보조한다."
linkedSkills:
  - recipes.news.untrustedToneAudit
  - recipes.news.eventTimelineFusion
  - recipes.fundamental.disclosure.eventRadar.eventInbox
gap:
  primary:
    - synth
    - gather
falsifier:
  description: "뉴스만 있고 공시가 없는 row 를 결론 근거로 쓰면 실패로 본다."
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
forbidden:
  - newsOnly row 를 결론 근거로 사용
  - 매칭 점수만으로 이벤트 중요도 확정
  - 외부 본문 마커 안 숫자를 공시 검증 없이 답변에 인용
failureModes:
  - 같은 사건의 정정·재공시 뉴스를 별도 매칭으로 처리
  - 회사명 동음이의로 다른 회사 뉴스 매칭
  - 매칭 window 가 너무 넓어 무관 이벤트 결합
examples:
  - 최근 7 일 공시-뉴스 정합성
  - 뉴스가 공시보다 먼저 나온 사건 식별
audiences:
  llm: filing 과 news row 를 EngineCall 로 받은 뒤 회사명·이벤트 키워드 매칭만 수행하고 의미 추론은 하지 않는다.
  agent: matched row 만 결론 근거로, newsOnly 는 한계로 명시.
  human: 뉴스가 공시 전에 의미 있는 정보를 알고 있었는지 row 단위로 본다.
humanIntro: "disclosureNewsCrosscheck 는 외부 untrusted 본문 (뉴스) 을 1 차 출처 (DART 공시) 로 *2 차 검증* 하는 가장 단순한 형태다. 추론 없이 시간·회사명·키워드만 비교한다."
lastUpdated: "2026-05-21"
testUniverse:
  market: KR
  stockCodes:
    - "005930"
validatedAt: '2026-05-27'
---

## 공개 호출 방식

AI 도구 실행 순서는 `EngineCall` 우선이다. 아래 Python 블록은 공시·뉴스 row 를 받아 ±1 day window 안에서 키워드 매칭하는 **RunPython fallback** 절차다.

```python
import dartlab
import polars as pl
from datetime import datetime, timedelta

target = "005930"
c = dartlab.Company(target)

def rows(value, limit=80):
    if hasattr(value, "head") and hasattr(value, "to_dicts"):
        return value.head(limit).to_dicts()
    if isinstance(value, list):
        return value[:limit]
    return []

def parseDate(v):
    if isinstance(v, datetime):
        return v.date()
    if v is None:
        return None
    s = str(v)[:10].replace(".", "-").replace("/", "-")
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

try:
    filings = rows(c.filings(), limit=60)
except Exception:
    try:
        filings = rows(c.filings(), limit=60)
    except Exception:
        filings = []

news_rows = rows(c.gather("news"), limit=80)

EVENT_KEYWORDS = (
    "유상증자", "무상증자", "전환사채", "신주인수권부사채", "감자",
    "합병", "분할", "지분", "취득", "처분", "배당",
    "실적", "공시", "정정", "주식분할", "자사주",
)

def tokens(text: str) -> set[str]:
    return {w for w in EVENT_KEYWORDS if w in (text or "")}

audit_rows = []
matched_news_ids = set()
WINDOW = timedelta(days=1)

for f in filings:
    f_date = parseDate(f.get("date") or f.get("rcept_dt") or f.get("filedAt"))
    f_title = str(f.get("title") or f.get("report_nm") or "")
    f_tokens = tokens(f_title)
    best = None
    for i, n in enumerate(news_rows):
        n_date = parseDate(n.get("date") or n.get("publishedAt") or n.get("pubDate"))
        if not f_date or not n_date:
            continue
        if abs((f_date - n_date).days) > WINDOW.days:
            continue
        n_title = str(n.get("title") or "")
        n_tokens = tokens(n_title)
        score = len(f_tokens & n_tokens)
        if score > 0 and (best is None or score > best[0]):
            best = (score, i, n_date, n_title)
    if best:
        matched_news_ids.add(best[1])
        audit_rows.append({
            "filingDate": str(f_date),
            "newsDate": str(best[2]),
            "leadDays": (best[2] - f_date).days,
            "filingTitle": f_title[:80],
            "newsTitle": best[3][:80],
            "score": best[0],
            "status": "matched",
        })
    else:
        audit_rows.append({
            "filingDate": str(f_date) if f_date else None,
            "newsDate": None,
            "leadDays": None,
            "filingTitle": f_title[:80],
            "newsTitle": None,
            "score": 0,
            "status": "dartOnly",
        })

for i, n in enumerate(news_rows):
    if i in matched_news_ids:
        continue
    n_date = parseDate(n.get("date") or n.get("publishedAt") or n.get("pubDate"))
    if not tokens(str(n.get("title") or "")):
        continue
    audit_rows.append({
        "filingDate": None,
        "newsDate": str(n_date) if n_date else None,
        "leadDays": None,
        "filingTitle": None,
        "newsTitle": str(n.get("title") or "")[:80],
        "score": 0,
        "status": "newsOnly",
    })

table = pl.DataFrame(audit_rows) if audit_rows else pl.DataFrame(
    schema={
        "filingDate": pl.Utf8, "newsDate": pl.Utf8, "leadDays": pl.Int64,
        "filingTitle": pl.Utf8, "newsTitle": pl.Utf8, "score": pl.Int64, "status": pl.Utf8,
    }
)

headline = {
    "matched": int((table["status"] == "matched").sum()) if table.height else 0,
    "dartOnly": int((table["status"] == "dartOnly").sum()) if table.height else 0,
    "newsOnly": int((table["status"] == "newsOnly").sum()) if table.height else 0,
    "newsLead": int(((table["leadDays"].fill_null(0)) < 0).sum()) if table.height else 0,
}

emit_result(
    table=table,
    values=headline,
    date=str(table["filingDate"].max()) if table.height else None,
    sources=[
        "dartlab://providers/dart/disclosure",
        "dartlab://gather/news",
        "dartlab://runtime/untrustedContent",
    ],
)
```

## 호출 동작

### 1. 결론 도출

DART 공시 ↔ 뉴스 정합성을 *matched / dartOnly / newsOnly 3 분류* + *뉴스 선행 row 수* 로 단정. 예: "최근 14 일 공시-뉴스 매칭률 N%, 뉴스 선행 row M 건 — 정보 비대칭 의심 여부 X."

### 2. 핵심 근거 수집

- DART 공시 row 60 건 (Company.filings(14d) 또는 Company.filings fallback)
- 뉴스 row 80 건 (Company.gather('news'))
- 이벤트 키워드 17 종 (유상증자·무상증자·전환사채·신주인수권부사채·감자·합병·분할·지분·취득·처분·배당·실적·공시·정정·주식분할·자사주)

### 3. 메커니즘 분석

```
공시 row × 뉴스 row → ±1 day window 필터 → 키워드 교집합 점수
→ score > 0 + 같은 회사 → matched (best score)
→ score = 0 + 공시만 → dartOnly
→ score > 0 + 뉴스만 → newsOnly (newsLead 검증 후보)
→ leadDays = newsDate - filingDate (음수면 뉴스 선행)
```

키워드 교집합 점수가 클수록 같은 이벤트 매칭 신뢰도 ↑. 뉴스 선행 (leadDays < 0) 은 정보 비대칭 의심 신호.

### 4. 반례·한계

- `newsOnly` row 만 결론 근거로 쓰면 외부 untrusted 본문 단독 인용 — 1 차 출처 (DART) 검증 없이 답안 작성 시 falsifier 발동.
- 같은 사건의 정정·재공시 뉴스를 별도 매칭으로 처리하면 매칭 수 인플레.
- 회사명 동음이의 (예: "한화"·"신세계") 다른 회사 뉴스 매칭 위험.
- 매칭 window 14d 너무 넓으면 무관 이벤트 결합.

### 5. 후속 모니터링

- `newsLead > 0` row 1 건 이상 발생 시: `recipes.news.eventTimelineFusion` 으로 가격 시계열 결합 → 정보 비대칭 정량.
- matched row 중 score ≥ 2 만 `recipes.fundamental.disclosure.eventRadar.eventInbox` 로 승격.
- newsOnly 키워드 빈도가 7 일 평균 대비 2x ↑: `recipes.news.newsHeadlineVelocity` 호출.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `filingDate` | DART 공시 날짜 (1 차 출처) |
| `newsDate` | 뉴스 발행 날짜 (외부) |
| `leadDays` | 뉴스가 공시보다 며칠 먼저 (-) 또는 나중 (+) |
| `filingTitle` | 공시 제목 |
| `newsTitle` | 뉴스 제목 |
| `score` | 키워드 교집합 수 |
| `status` | matched / dartOnly / newsOnly |

## 연계 절차

1. recipes.news.untrustedToneAudit - 뉴스 본문 마커 검증 (선행).
2. recipes.news.eventTimelineFusion - 매칭 결과를 가격 시계열과 합쳐 정보 비대칭 의심 row 추출.
3. recipes.fundamental.disclosure.eventRadar.eventInbox - matched row 만 이벤트 inbox 로 승격.

## 기본 검증

- `newsOnly` row 는 결론 근거가 아닌 *추적 후보* 로만 표시.
- `newsLead > 0` 이면 답변 본문에 *정보 비대칭 의심 row 수* 를 명시.
- 매칭 score 가 0 이면 같은 날짜라도 별개 이벤트로 본다 — 시간 근접만으로 결합 금지.
