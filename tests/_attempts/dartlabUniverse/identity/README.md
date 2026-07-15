# Identity attempts

> 상태: U0-I01 canonical ID 계약 완료, live historical registry 차단
> 책임: legal entity, security, filing identity를 분리하고 alias ambiguity와 validity를 fail closed로 판정한다.

## 가설

DART corpCode, KRX ISIN, SEC CIK와 provider filing ID를 canonical key로 사용하면 stockCode와 ticker를 presentation key로 제한할 수 있다.

## 실행

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/identity/entityIdentityProbe.py
uv run python -X utf8 tests/audit/docstring4Section.py tests/_attempts/dartlabUniverse/identity --strict
uv run python -X utf8 tests/audit/docstring9Section.py tests/_attempts/dartlabUniverse/identity --strict
```

Unit test는 repository test lock을 획득한 뒤 `testEntityIdentityProbe.py` 단일 파일만 실행한다.

## 계약

- KR legal entity: `kr:dart:corp:{corpCode8}`
- KR security: `kr:krx:security:{isin}`, ISIN이 없을 때만 `kr:krx:stock:{stockCode}` fallback
- US legal entity: `us:sec:cik:{cik10}`
- US security: `us:{exchange}:ticker:{ticker}`, legal entity와 별도이며 historical 사용에는 validity 필요
- DART filing: `kr:dart:filing:{rceptNo14}`
- SEC filing: `us:sec:filing:{accessionNo}`
- Alias는 Unicode와 whitespace exact normalization만 허용하고 fuzzy name은 identity admission에 사용하지 않는다.
- 같은 alias가 다중 identity로 이어지면 `ambiguous`와 모든 candidate를 반환하고 selectedId를 비운다.
- Historical query에서 validity가 하나라도 빠지면 `unresolvedValidity`다.

## U0-I01 결과

| 항목 | 실측 |
|---|---:|
| DART legal master | 115,963 |
| DART listed stock row | 3,959 |
| KR legal entity sample | 50/50 canonical |
| Full DART master ambiguous exact name | 5,392 |
| StockCode to multiple corpCode | 0 |
| KR alias validity field | 0 |
| KRX security | 2,872 |
| ISIN security canonical | 2,872/2,872 |
| KRX security to DART issuer exact link | 2,742 |
| KRX issuer link gap | 130 |
| SEC ticker row | 10,436 |
| Unique CIK | 8,023 |
| Unique ticker | 10,436 |
| US legal entity sample | 30/30 canonical |
| CIK with multiple current security | 1,473 |
| Ticker to multiple CIK | 0 |
| US ticker validity field | 0 |
| KR filing sample | 50/50 canonical, source company file 30 |
| US filing sample | 30/30 canonical, local issuer 2 |
| Exact identifier total | 160/160, 100% |
| Synthetic regression | 9/9 PASS |
| live historical registry ready | false |

표본은 대표성을 주장하지 않는 deterministic schema sample이다. Full DART master의 ambiguous name 5,392는 현재 KIND listed name ambiguity와 같은 뜻이 아니다. 이름이 historical, private, related legal entity를 접을 수 있다는 위험 계수다.

KRX issuer link gap 130개는 우선주 등 security class를 DART stock_code exact join만으로 법인에 붙일 수 없음을 보여준다. 이름이나 종목코드 suffix로 issuer를 추정하지 않는다. US CIK 1,473개도 복수 ticker를 가지므로 CIK와 ticker node를 합치지 않는다.

판정은 `revise`다. Canonical builder와 ambiguity contract는 완료했다. 그러나 KR security issuer link 130개, KR 및 US validity field 0, US local filing issuer 2개, reviewed merger, rename, preferred, SPAC, ticker change gold 부재 때문에 live historical identity registry는 차단한다. Reference owner가 issuer link와 validity를 소유해야 하며 UI alias dict는 금지한다.

## 다음

U0-E01에서 candidate edge가 exact filing, section, locator로 돌아가는지 검증한다. Identity는 source resolution의 입력일 뿐 evidence 자체가 아니다.

Production 코드는 이 경로를 import하지 않는다.
