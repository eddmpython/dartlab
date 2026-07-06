---
id: operation.notifyPipeline
title: 왓처-노티파이 파이프라인 (IPO 베이크 → 왓치 → Web Push + 헬스체크) 운영 SSOT
kind: curated
scope: builtin
status: observed
category: operation
purpose: 공개 왓처-노티파이 파이프라인의 운영 SSOT. cron 이 IPO 공모분석을 첫 관문으로 베이크(라이브 롤링 + 누적 아카이브)한 뒤 왓치 토픽(newIpo·newOrders)을 평가해 pushHub 로 Web Push 브로드캐스트하고, Data Audit(monitorPipeline)이 매일 건강을 감시한다. 트리거 '왓처 파이프라인', '알림 파이프라인', 'notify-watch', 'IPO 베이크 운영', 'push 헬스체크'.
whenToUse:
  - 왓처 파이프라인 운영
  - 알림 파이프라인
  - notify-watch
  - IPO 베이크 운영
  - push 파이프라인 헬스체크
  - 파이프라인 배포 런북
  - Web Push 운영
inputs:
  - DART 증권신고서(corp_cls=E) + scan 축(ipo·orders)
  - 배포 secret (HF_TOKEN · PUSHHUB_SEND_TOKEN · VAPID · D1)
outputs:
  - HF dart/ipo/reports.parquet (라이브 롤링) + history.parquet (누적 아카이브)
  - Web Push 알림 (newIpo·newOrders) 로 /terminal 딥링크
  - pipeline-failure Issue (헬스체크)
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: limited
  webAi:
    status: limited
  pyodide:
    status: unsupported
knowledgeRefs:
  - operation.observability
  - operation.architecture
  - engines.scan
  - operation.terminal
sourceRefs:
  - dartlab://skills/operation.notifyPipeline
failureModes:
  - bake 실패를 continue-on-error 로 삼켜 조용한 실패 (F1 수리: assert 스텝이 job RED)
  - Notify Watch cron drop 미감지 (F5 수리: STALE_AFTER_HOURS 80h)
  - newIpo slug=rcept 라 기재정정마다 재발화 (F2 수리: slug=corpCode)
  - 허브 전건 발송실패 시 nonce 소각 후 재시도 불가 (F3 수리: nonce 롤백)
  - newOrders 재크로싱 미발화 (F7 수리: /active set-diff 커서)
forbidden:
  - reports.parquet(라이브 whole-file)에 전이력 누적 (1.5MB 게이트 초과, history.parquet 별도)
  - graph 회귀 (BRIEF/WORK 고정노드) 또는 파이썬 파서 JS 재구현
  - 시뮬레이터에 rcept 키 아카이브 직결 (corpCode 에서 stock_code 브리지 없이 orphan)
lastUpdated: '2026-07-06'
---

## 역할

공개 왓처-노티파이 파이프라인은 **감지할 만한 공시 이벤트를 cron 이 발굴해 Web Push 로 사용자에게 밀고, 클릭 시 터미널의 인사이트로 잇는다**. 감지 지능은 dartlab(gather·scan SSOT)에 살고, 허브(pushHub Worker)는 구독 보관 + VAPID 서명 + 발송만 한다(런타임-SSOT, `operation.architecture`). 이 문서는 그 파이프라인의 운영 계약이다. 상세 진행 원장·배포 런북은 `mainPlan/_done/watcher-notify-platform/05-progress-ledger.md`.

핵심 원칙: **왓치가 첫 관문**이다. cron 은 알림을 쏘기 전에 IPO 공모분석을 먼저 베이크해 HF 에 올려, 딥링크가 여는 리포트가 이미 존재하게 한다.

## 파이프라인 단계 (notify-watch.yml cron, 평일 17시 KST)

```
[1] Bake  buildIpoReports.py  발굴→파싱→ reports.parquet(라이브) + history.parquet(누적) → HF push
[2] Watch watch.py            _baked_ipo_df 직독(없으면 scan 폴백) → 토픽 평가 → 허브 /send·/active
[3] Assert                    bake genuine-failure(push·파싱·사이즈가드)면 job RED (조용한 실패 가드)
```

- **첫 관문 순서**: bake 가 watch 앞. 딥링크(`/terminal?ipo=1`) 목적지 리포트가 알림 전에 HF 에 등재된다.
- **단일 파싱**: watch 는 스스로 scan("ipo") 를 다시 돌리지 않고 방금 구운 parquet 을 같은 runner 에서 직독한다(컬럼 호환). 베이크 부재/실패면 scan 폴백.
- **회복성 + 가시성**: bake 는 `continue-on-error`(알림은 계속) + 별도 assert 스텝(진짜 실패면 job RED). 미설정(HF_TOKEN 부재)은 graceful no-op(exit 0), genuine-failure 만 RED.
- **발굴 SSOT**: corp_cls=E 발굴·그룹핑은 `scan.ipo._discoverIpoIssuers` 단일 소스(베이크·scan 공유). 파싱은 `story.buildIpoReport`. 워커 TS `groupIpoFilings` 는 크로스런타임 미러.

## 데이터 산출물 (2파일 모델, buildAllFilingsRecent recent/market_recent 미러)

| 파일 | 모델 | 소비 | 게이트 |
|---|---|---|---|
| `dart/ipo/reports.parquet` | 라이브 롤링(최근 85일, 매 cron 덮어씀) | 터미널 whole-file 직독 + 왓치 알림 | 1.5MB whole-file |
| `dart/ipo/history.parquet` | 누적 아카이브(rcept 키, HF baseline merge + dedup + 무trim) | 역사·백테스트(정적) | corpCode range-fetch (whole-file 게이트 면제) |

- corp_cls=E 증권신고서는 allFilings·panel(Y/K 전용)에 없어 이 파이프라인이 그 SSOT 를 처음 생산한다.
- 라이브는 aging out(상장·85일 경과)으로 소실되므로, history 가 rcept 키로 영구 보존(list.json 3개월 제한이라 재발굴 불가). reportJson 전블롭 보존. 이력이 커지면 실측 후 연 샤딩(`history_{yyyy}.parquet`) 승격, 선제 샤딩 금지.

## 왓치 토픽 (평가 = plain 함수 1개, 레지스트리 0)

| 토픽 | 데이터원 | 발화 | dedup |
|---|---|---|---|
| `newIpo` | reports.parquet(베이크)·scan("ipo") 폴백 | 발행사 등장(slug=corpCode) + 확정공모가(corpCode:conf) 2신호 | 허브 sentNonce(영구 멱등), slug=corpCode 라 기재정정 재발화 0 |
| `newOrders` | scan("orders") | book-to-bill>=1 신규 진입 | 허브 `/active` topicActive set-diff 커서(직전 활성셋 대비 entered 만, 이탈 종목 재진입 시 재발화) |
| `screenAlert` | scan.screen 저장 스크린(`notify: true` opt-in) | 스크린 멤버십 진입(조건 충족) | 허브 `/active` set-diff 커서(직전 멤버셋 대비 entered, 이탈 후 재진입 재발화). newOrders 동형 |

- new_listing 형(newIpo)은 per-match `/send`(영구 nonce), threshold_cross 형(newOrders·screenAlert)은 `/active` set-diff(재크로싱 발화). watch.py `_STATEFUL_TOPICS` 로 분기.
- **screenAlert 롤아웃 게이트**: 저장 스크린(`screens/*.json` + `notify:true`) 멤버십을 `evaluateScreenMembers` 로 평가해 진입 알림. 첫 활성화 시 현 멤버 전원이 진입으로 보여 flood 가능하므로 `main` default 토픽에서 제외(운영자가 cron `--topics` 에 추가해 롤아웃). flagship=`financialStabilityDrawdown`(하락장 재무안전).
- 허브는 전건 발송실패(sent=0 && failed>0)·구독자0 시 nonce 롤백(다음 cron 재시도). 러너는 body.failed 를 전건=RED·부분=warning 으로 표면화(조용한 미발화 종료).
- 딥링크: newIpo `/terminal?ipo=1`, newOrders `/terminal?sym={code}`.

## 헬스체크 (Data Audit, 매일 05시 KST)

`monitorPipeline.py`(`operation.observability`)가 scheduled 파이프라인 전체의 실패·cron drop 을 매일 감시해 pipeline-failure Issue 로 알린다. "Notify Watch" 등록 상태:

- **실패 감지**: MONITORED_WORKFLOWS 등록. bake genuine-failure 는 위 assert 스텝이 job RED 로 만들어 여기서 잡힌다.
- **cron drop 감지**: STALE_AFTER_HOURS 80h(금~월 72h 주말 갭 초과) 등록. 3일+ 연속 스케줄 누락(퍼블릭 IPO SSOT 동결) 시 stale 감지·자동 트리거(nonce 멱등이라 오탐 무해).

★ 운영자 상시 규칙: 이 파이프라인은 하루 1회 헬스 체크(자동=Data Audit). 세션 체크 3점: Notify Watch run 초록+assert 통과 / HF reports.parquet 최신 / 열린 pipeline-failure Issue.

## 배포 런북 (운영자 게이트. 코드는 green, 이것만 하면 활성)

전 러너는 미설정 시 graceful no-op(RED 0). 활성 순서:

1. **pushHub Cloudflare**: `infra/workers/pushHub` D1 생성 + schema.sql/migrations(0002 topicActive 포함) 적용 + VAPID·PUSHHUB_SEND_TOKEN secret + `wrangler deploy`.
2. **GitHub**: `VITE_PUSHHUB_URL`·`VITE_VAPID_PUBLIC_KEY` vars + `PUSHHUB_SEND_TOKEN`·`HF_TOKEN` secret.
3. **hfProxy 재배포**: `/ipo-filings` 라우트 활성(newIpo 딥링크 발굴 데이터원).
4. **landing 눈검수 후 push** + 실기기 1대 aes128gcm 수신 확인.

상세 명령·postmortem 은 원장 05 배포 런북 참조.

## 불변식 (회귀 가드)

- 첫 관문 순서(bake 먼저, watch 나중) + 단일 파싱 유지. graph 강박(고정 노드) 금지(`ai/agent.py` 본체).
- 라이브/아카이브 2파일 분리 불변: reports 는 whole-file 게이트, history 는 누적. 라이브에 전이력 넣지 말 것.
- 발굴 SSOT `_discoverIpoIssuers` 단일화 유지(재구현 0). 파서 JS 재구현 금지.
- 밸류 이종기준 가드: 적용모형 EV/EBITDA 면 implied PER 와 좌표 비교 금지(알림 라벨은 중립 "적용배수").

## 검증

- 러너: `.github/scripts/notify/test_watch.py`(16, screenAlert 멤버십 포함) · 허브 vitest `infra/workers/pushHub`(24, /active 재크로싱 포함) · 베이크 `tests/sync/test_buildIpoReports.py`(4, 누적·dedup) · scan `tests/scan/test_ipo.py`(5) · 모니터 `tests/pipeline/test_monitor_classify.py`(20, Notify Watch staleness).
- 실측: 실 DART 발행사 build 로 reports + history 2파일 산출 확인. 첫 빌드는 baseline 없어 history==live.
- 감사: 5차원 적대검증(wf_47c0b9eb 확증 10) + 파이프라인 적합성(wf_2af24a25). 상세 원장 05 §감사.
