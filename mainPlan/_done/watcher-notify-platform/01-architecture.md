# 01 — 아키텍처 · 왓처의 물리적 자리 · 졸업 트랙

## 1. 3계층

| 계층 | 자리 | 책임 | 선례 |
|---|---|---|---|
| 왓처(지능) | dartlab 라이브러리 | 감시 대상·판정을 gather·scan SSOT **직독**으로 평가 | gather 축·scan 레지스트리 |
| 러너(스케줄) | GitHub Actions cron | dartlab 으로 평가 → 매치를 허브 `/send` 로 | `brokerageSync.yml`(HF_TOKEN 주입·헬스게이트) |
| 허브(배달) | Cloudflare Worker | 구독 저장 + 발송 + VAPID. 크롤·판정 0 | `siteSignals`(D1)·`questionCollector`(thin POST) |

**불변 원칙**: 감지 지능은 dartlab 이 사는 곳에. Cloudflare 는 저장 + 발송만(런타임-SSOT 정합,
`architecture.md` §122 "공동작업대(gather·scan SSOT)만, 별도빌드 금지").

## 2. 왓처의 물리적 자리 — 단계별로 다르다 (핵심 결정)

새 L2 엔진은 **회귀**다. 왓처는 단일 도메인 분석이 아니라 *여러 엔진 결과 위에 선언적 조건을 거는
cross-cutting 평가*다. 새 L2 엔진은 5엔진 도메인 격리(`architecture.md` §108 "다른 L2 직접 import 금지")를
깨고 engine-add 게이트(9섹션 docstring·lint-imports·Skill OS sub-spec) 비용을 부른다. recipe 도 아니다
(recipe = 분석 5단 답변 산출이지 조건 평가·발송 트리거가 아님).

### P1-P2: 러너 plain 함수 (src 밖)
왓처 = `.github/scripts/notify/` 의 평가 함수, **토픽 1개 = 함수 1개**. gather/scan SSOT 를 *입력으로만*
직독(베이크 0, 새 능력 0). src/dartlab 신규 능력이 아니라 러너 로직이므로 **`_attempts` 졸업 게이트 비대상**.
레지스트리·synth 모듈은 **짓지 않는다**(YAGNI — N=5, 형태 제각각: 브로드캐스트 vs per-user, 이벤트 vs 시계열).

예: `evalNewOrders()` → `scan('orders')` 결과 위 `book-to-bill ≥ 1` threshold_cross diff → 매치 list → `/send`.

### P3: synth/watch 모듈 + 레지스트리 (발견적 추출)
두 번째 소비자(로컬 Mode A 데몬)가 **같은 평가 함수를 재사용**함이 실증될 때 — `architecture.md` §118
"L1.5 진입 = ≥2 소비자" 충족 — `tests/_attempts/watcherEval/` 졸업 후 `src/dartlab/synth/watch/` 에 배치.

- `synth/watch/` — `WATCHER_REGISTRY` (frozen dataclass) + 순수 `evaluate(watcherType, snapshotData, params) -> list[Match]`
- `pipeline/stages/watch` — gather/scan fetch + `synth.evaluate` + `/send` 오케스트레이션 (L4 sink)

## 3. import 방향 — 호출자 inversion (high-severity 리스크 해소)

`synth`(L1.5)는 `gather`(L1)·`scan`(L1.5 형제)를 **직접 import 못 한다**(`architecture.md` §117 L1.5 4형제
cross import 금지). 정공법 = 호출자 inversion(§177 패턴1):

- `synth.evaluate(watcherType, snapshotData, params)` 가 *이미 fetch 된 데이터를 인자로 받는다*(순수 함수).
- gather/scan 호출은 **L4 pipeline stage**(sink, 모든 하위 import 합법)가 수행 → synth 에 주입.
- `WatcherType.ssotRef` 는 **문자열 메타**(`'scan.orders'`/`'gather.price'`)로 pipeline 이 dispatch — synth 내 import 아님.

→ synth 는 import 방향 0 위반, 평가 순수성 유지.

## 4. 레지스트리 설계 (P3 도입 시)

scan `_AxisEntry`·gather `GatherAxisEntry` 와 **필드·구조 동형**(세 번째 패턴 발산 방지). frozen `@dataclass`:

```
WatcherType:
  id · label · description
  ssotRef          # 'scan.orders' | 'gather.price' | 'Company.disclosure'
  predicateKind    # threshold_cross | keyword_match | new_listing  (≤3 고정, 타입별 if-분기 0)
  defaultParams    # 공개 토픽용 고정 파라미터
  userParamSchema  # 개인용 사용자 파라미터 스키마
  scope            # Literal['public','personal','both']
WATCHER_REGISTRY: dict[str, WatcherType]   # 단일 dict
```

`scope` 한 필드가 **"두 바인딩 모드"를 코드로 실현** — 타입 1개 등록 = 공개·개인 양쪽 자동 노출.
"한 곳 추가" = dict 에 엔트리 1개 + (필요시) predicate 함수 1개. 새 엔진·파서·데이터 0.

## 5. 상태(커서) — 런타임-SSOT 위반 아님

gather/scan 은 *현재 스냅샷*만 반환하므로 `threshold_cross`(돌파)·`new`(신규)·키워드 신규출현은 *직전 평가
상태(last-seen)*가 필요하다. 이 커서는 **원천 데이터 베이크가 아니라 알림 dedup 메타**(직전 매치 id set)다.
거처 = 허브 D1(잠정 — repo 청결 우선). 데이터 SSOT 는 그대로 gather/scan 직독.

## 6. 졸업 트랙 (두 갈래)

- **배선 트랙 (`_attempts` 비대상)**: pushHub Worker·SW 리스너·NotifyOptIn·PNA/CORS 미들웨어·`bridge/ping`·
  `watch.json` IO·러너 스크립트. "능력이 아니라 배선"이라 직접 src/infra (선례: `channel.py` 도 `_attempts` 미경유).
- **능력 트랙 (`_attempts` 필수)**: 왓처 *평가 로직*만 — `tests/_attempts/watcherEval/` 에서 8단계 졸업.
  졸업 4 실측 게이트: (a) ≥3 타입이 서로 다른 `ssotRef`(scan·gather·Company.disclosure)에서 동작 —
  데이터원 중립 증명, (b) 같은 타입이 `scope=public`(고정)·`personal`(사용자) 양 모드 평가 — 두 모드 증명,
  (c) predicate if-분기 0 — 덕지덕지 게이트, (d) last-seen 커서 diff 로 중복 알림 0건 재현.

aes128gcm 발송 암호화는 `tests/_attempts/pushHub/` 에서 실브라우저 1대 ece 인코딩 별도 졸업.
