# 계정 매핑 학습 워크플로우

계정 매핑을 지속적으로 개선하기 위한 학습 사이클 가이드.
새 종목 데이터가 추가되거나 매핑률을 올리고 싶을 때 이 문서를 따른다.

**핵심 원칙: 학습은 _reference/ 내부에서만 한다**
- `_reference/`는 `.gitignore`에 등록 → git에 올라가지 않음
- 학습 데이터(standardAccounts.json, learnedSynonyms.json)는 전부 여기에 있음
- 학습 결과를 `mapperData/accountMappings.json`으로 병합하면 그것만 git에 올라감
- 즉: 원본 데이터(비공개) → 병합 결과(공개) 구조

```
_reference/                             ← git 미포함 (학습 작업 공간)
+-- eddmpython/
|   +-- standardAccounts.json           ← 원본 A
|   +-- learnedSynonyms.json            ← 원본 B (학습하면 여기가 커짐)
|   +-- v8/                             ← 학습 도구들

mapperData/                             ← git 포함 (프로덕션 데이터)
+-- accountMappings.json                ← A + B 병합 결과 (mapper.py가 사용)
```

---

## 전체 사이클 요약

```
1. 측정 — 현재 매핑률 확인 (몇 % 매핑되는가?)
2. 수집 — 미매핑 계정 리스트 추출
3. 분석 — 미매핑 계정이 어떤 표준계정에 해당하는지 판단
4. 학습 — learnedSynonyms.json에 새 동의어 추가
5. 병합 — accountMappings.json 재생성 (standardAccounts + learnedSynonyms)
6. 검증 — 매핑률 재측정 + 재무제표 합계 검증
7. 반복 — 만족할 때까지 2~6 반복
```

---

## 1단계: 매핑률 측정

### 방법 A — dartlab에서 직접 측정

```python
import dartlab
from dartlab.engines.dart.finance import buildTimeseries
from dartlab.engines.dart.finance.mapper import AccountMapper
import polars as pl

mapper = AccountMapper.get()

stockCode = "005930"
dataDir = Path(dartlab.dataDir) / "finance"
parquetPath = dataDir / f"{stockCode}.parquet"
df = pl.read_parquet(parquetPath)

total = 0
mapped = 0
unmapped = []

for row in df.select(["account_id", "account_nm"]).unique().iter_rows(named=True):
    accountId = row["account_id"] or ""
    accountNm = row["account_nm"] or ""
    result = mapper.map(accountId, accountNm)
    total += 1
    if result:
        mapped += 1
    else:
        unmapped.append(accountNm)

print(f"매핑률: {mapped}/{total} ({mapped/total*100:.1f}%)")
print(f"미매핑 상위 20개:")
for nm in unmapped[:20]:
    print(f"  - {nm}")
```

### 방법 B — v8 QualityCheck 활용

_reference/v8/qualityCheck.py의 MappingQualityChecker를 dartlab 환경에 맞게 수정해서 실행.
이쪽이 더 체계적 (재무제표별 분석, 신뢰도 분포, 표준화 품질까지 측정).

### 목표 매핑률

| 등급 | 매핑률 | 판단 |
|------|--------|------|
| 우수 | ≥95% | 프로덕션 사용 가능 |
| 양호 | ≥90% | 핵심 계정은 OK, 세부 계정 보완 필요 |
| 보통 | ≥80% | 주요 분석에는 사용 가능하나 개선 필요 |
| 미흡 | <80% | 적극적 학습 필요 |

---

## 2단계: 미매핑 계정 수집

### 방법 A — 종목 단위

위 1단계 코드의 `unmapped` 리스트.

### 방법 B — 전체 종목 빈도 기반

```python
from collections import Counter
from pathlib import Path
import polars as pl

mapper = AccountMapper.get()
dataDir = Path(dartlab.dataDir) / "finance"
unmappedCounter = Counter()

for parquetPath in dataDir.glob("*.parquet"):
    df = pl.read_parquet(parquetPath)
    for row in df.select(["account_id", "account_nm"]).unique().iter_rows(named=True):
        accountId = row["account_id"] or ""
        accountNm = row["account_nm"] or ""
        if not mapper.map(accountId, accountNm):
            unmappedCounter[accountNm] += 1

for nm, cnt in unmappedCounter.most_common(50):
    print(f"  {cnt:>5}  {nm}")
```

빈도가 높은 미매핑 계정부터 처리하면 매핑률이 빠르게 올라감.

### 방법 C — v8 SynonymLearner 활용

```python
learner = SynonymLearner(dataDir=referenceDir)
result = learner.analyzeCompany("005930")
print(f"매칭률: {result.matchRate:.1f}%")
print(f"미매칭: {result.unmatched}")
```

또는 exportUnmatched()로 JSON 내보내기:
```python
learner.exportUnmatched(outputPath=referenceDir / "unmatchedAccounts.json")
```

출력 형태:
```json
{
  "accounts": [
    {
      "stdAccountNm": "환불부채",
      "frequency": 47,
      "candidates": [
        {"snakeId": "refund_liabilities", "korName": "환불부채", "similarity": 1.0},
        {"snakeId": "other_current_liabilities", "korName": "기타유동부채", "similarity": 0.4}
      ],
      "approved": null
    }
  ]
}
```

---

## 3단계: 미매핑 분석 및 판단

미매핑 계정을 보고 어떤 snakeId에 매핑해야 하는지 판단하는 단계.

### 판단 기준

**1) 표준계정에 정확히 대응하는 경우** → 해당 snakeId 직접 매핑
- "환불부채" → refund_liabilities (standardAccounts.json에 있음)
- 이 경우 learnedSynonyms.json에 추가

**2) 동의어/변형인 경우** → 대표 계정의 snakeId로 매핑
- "종속기업에대한투자자산" → investments_in_subsidiaries
- "관계기업 및 공동기업 투자" → investments_in_associates
- DART 회사마다 다른 표현을 쓰므로 가장 흔한 케이스

**3) 상위 분류로 매핑하는 경우** → other_xxx 계열
- "○○기금" → other_noncurrent_assets (뭔지 특정 불가, 비유동자산으로 분류)
- 이런 건 FallbackMapper가 처리할 영역

**4) 매핑 불필요한 경우** → 무시
- "주석" 같은 텍스트 항목
- level이 0인 소계/합계 라벨

### 유사도 기반 자동 판단

v8 SynonymLearner의 suggestMappings()가 SequenceMatcher로 유사도를 계산해서 후보를 제안.

| 유사도 | 판단 |
|--------|------|
| ≥0.95 | 자동 승인 가능 (오타/공백 차이 수준) |
| 0.8~0.95 | 높은 확률로 맞지만 사람이 확인 |
| 0.6~0.8 | 후보로 제시, 반드시 사람이 판단 |
| <0.6 | 무관한 계정일 가능성 높음 |

### 참고 자료

**standardAccounts.json 검색** — snakeId를 모르겠으면:
```python
import json
with open("_reference/standardAccounts.json", encoding="utf-8") as f:
    data = json.load(f)

query = "환불"
for acc in data["accounts"]:
    if query in acc.get("korName", ""):
        print(f"{acc['korName']} → {acc['snakeId']} (industry={acc['industry']}, stmt={acc['statementKind']})")
```

**learnedSynonyms.json 역검색** — 이미 매핑된 비슷한 계정 확인:
```python
with open("_reference/learnedSynonyms.json", encoding="utf-8") as f:
    synonyms = json.load(f)["synonyms"]

query = "종속기업"
for key, snakeId in synonyms.items():
    if query in key:
        print(f"'{key}' → {snakeId}")
```

---

## 4단계: learnedSynonyms.json에 추가

### 수동 추가

learnedSynonyms.json을 직접 편집:
```json
{
  "synonyms": {
    "기존키": "기존snakeId",
    "환불부채": "refund_liabilities",
    "새로추가한계정명": "target_snake_id"
  }
}
```

규칙:
- 키는 **공백 제거한 한글명** (또는 영문 normalizedId)
- 값은 **snakeId** (snake_case)
- 이미 있는 키를 덮어쓰면 안 됨 (중복 체크)

### v8 SynonymLearner로 추가

```python
learner = SynonymLearner(dataDir=referenceDir)
learner.learnSynonym("환불부채", "refund_liabilities")
```

일괄:
```python
learner.learnBatch({
    "환불부채": "refund_liabilities",
    "반환제품회수권": "right_of_return_assets",
})
```

수동 검토 파일에서 가져오기:
```python
learner.importApproved(referenceDir / "unmatchedAccounts.json")
```

### 자동 학습

유사도 95% 이상을 자동 승인:
```python
report = learner.autoLearn(
    stockCodes=["005930", "000660", "035420"],
    autoApproveThreshold=0.95,
    verbose=True
)
print(f"학습된 동의어: {report.synonymsLearned}개")
```

---

## 5단계: accountMappings.json 재병합

learnedSynonyms.json을 수정한 후, accountMappings.json을 재생성해야 함.
이 파일이 dartlab mapper.py가 런타임에 사용하는 프로덕션 데이터.

### 병합 스크립트

```python
import json
from pathlib import Path

referenceDir = Path("src/dartlab/engines/dart/finance/_reference")
mapperDataDir = Path("src/dartlab/engines/dart/finance/mapperData")

with open(referenceDir / "standardAccounts.json", encoding="utf-8") as f:
    standard = json.load(f)

with open(referenceDir / "learnedSynonyms.json", encoding="utf-8") as f:
    learned = json.load(f)

mappings = {}

standardCount = 0
for acc in standard.get("accounts", []):
    korName = acc.get("korName", "").replace(" ", "")
    snakeId = acc.get("snakeId", "")
    if korName and snakeId and korName not in mappings:
        mappings[korName] = snakeId
        standardCount += 1

synonyms = learned.get("synonyms", {})
for key, snakeId in synonyms.items():
    if key not in mappings:
        mappings[key] = snakeId

result = {
    "_metadata": {
        "description": "DART 표준계정 매핑 테이블 (korName/synonym -> snakeId)",
        "standardAccounts": standardCount,
        "learnedSynonyms": len(synonyms),
        "merged": len(mappings),
        "lastUpdate": "YYYY-MM-DD"
    },
    "mappings": mappings
}

with open(mapperDataDir / "accountMappings.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"병합 완료: {len(mappings):,}개 (standard={standardCount}, synonym={len(synonyms)})")
```

이 스크립트를 학습 후 매번 실행하면 mapper.py가 새 매핑을 바로 사용.

---

## 6단계: 검증

### 매핑률 재측정

1단계와 동일. 학습 전후를 비교:
```
학습 전: 89.3% (2,450/2,743)
학습 후: 94.1% (2,581/2,743) → +4.8%p
```

### 재무제표 합계 검증 (v8 SumValidator)

매핑이 정확한지 회계 공식으로 교차검증:
```python
validator = SumValidator(tolerance=0.01)

bsResults = validator.validateBalanceSheet(bsData)
isResults = validator.validateIncomeStatement(isData)
cfResults = validator.validateCashFlow(cfData)

for r in bsResults + isResults + cfResults:
    status = "OK" if r.isValid else f"오차 {r.diffPct:.2f}%"
    print(f"  {r.formula} → {status}")
```

### 표준화 품질 (같은 개념 → 같은 snakeId)

같은 개념의 변형이 같은 snakeId로 수렴하는지 확인:
```
[매출액]
  "매출" → revenue
  "수익(매출액)" → revenue
  "영업수익" → revenue
  "매출액(수익)" → revenue
  통일률: 4/4 (100%)

[영업이익]
  "영업이익(손실)" → operating_income
  "영업손익" → operating_income
  통일률: 2/2 (100%)
```

---

## 학습 이력 기록 (이 파일에 추가)

학습할 때마다 아래 형식으로 기록해두면 진행 추적에 도움.

### 학습 이력

| 날짜 | 작업 | 학습 전 | 학습 후 | 비고 |
|------|------|---------|---------|------|
| (아직 없음) | | | | |

---

## 자주 하는 실수

**1) learnedSynonyms.json만 수정하고 accountMappings.json 재병합 안 함**
→ mapper.py는 accountMappings.json만 보므로 학습 결과가 반영 안 됨

**2) 이미 CORE_MAP에 있는 계정을 learnedSynonyms에 중복 추가**
→ 동작은 하지만 불필요. CORE_MAP이 우선순위가 높으므로 learnedSynonyms는 사용 안 됨

**3) snakeId 오타**
→ "opreating_income" 같은 오타. standardAccounts.json에서 정확한 snakeId 확인 후 추가

**4) 공백 제거 안 하고 추가**
→ learnedSynonyms의 키는 공백 제거된 형태. "영업 이익"이 아니라 "영업이익"

**5) 같은 한글명을 다른 snakeId에 매핑**
→ 산업별로 다를 수 있으나, 현재 dartlab의 단순 dict lookup은 산업 구분 불가.
→ 이 문제를 해결하려면 v8의 컨텍스트 매핑(ParquetMapper)이 필요
