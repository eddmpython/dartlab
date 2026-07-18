# pyproc Runtime SSOT - dartlab 커널을 pyproc 공유 런타임으로

상태: **P0~P3 완료 + P2 라이브 배포 (pyproc 기본 커널)** (2026-07-12). P0 파리티 + P1 seam + P3 자동반영 + **P2 flip(`USE_PYPROC_ASGI=true`) 검증 후 push, deploy-landing GREEN 로 라이브 배포됨**. 실패 시 손수 경로 자동 폴백(kill-switch). P4(격리 fork)만 봉인(스냅샷 spike SUPPORTED, COEP/Chromium전용은 별도 PRD). 검증 기반 = [00-verified-facts.md](00-verified-facts.md), 진행 = [06-progress-ledger.md](06-progress-ledger.md).

범위: dartlab 브라우저 노트북의 pyodide 커널을, 저자 동일의 공유 런타임 **pyproc**(github.com/eddmpython/pyproc, "브라우저 파이썬 프로세스 OS")으로 이관한다. 손수 만든 것(pyodide boot, ASGI dispatch, heap 체크포인트, interrupt)을 pyproc 이 흡수하고, dartlab 은 노트북 고유층(postMessage·OPFS·결과 포매팅·SW 배선)만 소유한다. 나아가 멀티코어 fork·터미널·리액티브를 점진 획득한다.

> 계보: codaro 가 browser-as-server 발명 -> dartlab 이 접목([mainPlan/_done/browser-as-server-ssot](../_done/browser-as-server-ssot/)) -> pyproc 이 2026-07-11 그 패턴을 공유 프리미티브로 흡수. 이 PRD 는 그 다음 장. dartlab 이 pyproc 을 런타임 SSOT 로 소비한다.

---

## 한 줄 결정 (초안, 01 에서 확정)

**"브라우저 파이썬 커널은 제품마다 복붙하지 않는다. pyproc 하나를 SHA 핀으로 공유한다."**
dartlab 은 pyproc `Runtime` 위에서 돌고, `AsgiServer`(browser-as-server), `ReactiveController`(체크포인트), 이후 `PyProc`(멀티코어 fork)를 능력으로 얹는다. 커널을 즉시 삭제하지 않는다. **seam 뒤에서 pyproc 을 주 경로로 올리고, 현 손수 커널은 게이트 통과 전까지 폴백으로 남긴다.**

## 왜 지금 (초안)

1. **중복 제거**: 우리가 이미 손수 만든 것(ASGI dispatch·heap 스냅샷 체크포인트·interrupt)을 pyproc 이 표준으로 흡수했다. 3제품 복붙 대신 한 곳에서 고친다.
2. **새 능력**: 스냅샷-fork 스폰 2.8s -> 184ms(15배), 멀티코어 병렬(전종목 scan 등), 터미널, 리액티브. 지금 우리 블로그가 "스레드 없음·순차만"이라 적어둔 한계를 깬다.
3. **실증됨**: Tier-1(Runtime + AsgiServer, 격리 불필요, 전 브라우저)은 이미 실제로 dartlab 을 서빙한다(00 §6).

## 단계 (초안, 04 에서 확정)

- **Tier-1** (격리 불필요, 전 브라우저, 회귀 0): pyproc `Runtime` + `AsgiServer` 를 seam 뒤에 두고 손수 dispatch 대체. CDN(jsDelivr gh SHA 핀) 소비.
- **Tier-2** (Chromium + crossOriginIsolated, 점진): SW 에 COOP/COEP 주입 + pyproc 벤더링 후 `PyProc` fork 멀티코어. 비-격리·비-Chromium 은 Tier-1 로 자동 폴백.

## 무엇을 잠그나 (재론 금지, 초안)

- **커널 즉시 삭제 금지.** 라이브 노트북이 도는 커널을 대체품 게이트 통과 전에 지우지 않는다. seam 뒤 폴백으로 강등 후, 검증되면 삭제.
- **dartlab 고유층 유지.** FORMAT_CODE(표·그림 렌더)·OPFS 영속·postMessage 15 커맨드·marimo/matplotlib shim 은 seam 위 dartlab 소유. pyproc 은 커널(실행·프로세스·dispatch·메모리)만.
- **자동 반영 = 게이트 통과 후 핀 범프.** float 금지(pyproc 정책). 새 SHA 는 pyproc 게이트(Runtime+AsgiServer+셀) 통과해야 착지.

## 문서 지도

1. [00-verified-facts.md](00-verified-facts.md) - 실측 원장 (COEP 헤더·격리 매핑·부팅 토폴로지·Tier-1 실증). **확정.**
2. [01-architecture.md](01-architecture.md) - 커널 seam, pyproc 소유 vs dartlab 소유, `new Runtime(py)` 채택, 마이그레이션·롤백, upstream 요청 4. (아키텍트 에이전트)
3. [02-auto-update.md](02-auto-update.md) - package.json SHA 핀 + 주간 게이트 범프 워크플로 + PYPROC 게이트 + COEP credentialless 롤아웃. (인프라 에이전트)
4. [03-risk-register.md](03-risk-register.md) - 리스크 R1~R9 + go/no-go + veto 5조건 + kill-switch. (적대 PM 에이전트)
5. [04-prd.md](04-prd.md) - **종합 SSOT**. 단계 P0~P4·영향 파일/함수·게이트·롤백·이중평가(5섹션). 착수 전 여기부터.
6. [06-progress-ledger.md](06-progress-ledger.md) - 결정 원장·세션 재개(NEXT).

## 한계 표기 원칙

1. 새 발명 최소화. pyproc·pyodide·SW·ASGI 전부 기성. 새로운 건 조합(dartlab 이 pyproc 을 소비)뿐.
2. Tier 표면화. 브라우저가 Tier-1(전 브라우저) 인지 Tier-2(격리 fork) 인지 숨기지 않는다.
3. 0.0.x 의존 정직. pyproc 은 신생·단일저자. 게이트·폴백·kill-switch 로 라이브 노트북을 보호한다.
