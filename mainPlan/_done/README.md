# _done — 완료·격리 PRD 보관

> 끝난 PRD/플랜은 여기로 **격리**한다. 진행 중인 PRD(`mainPlan/<name>/`)와 섞이지 않게.
> 삭제하지 않는 이유: 설계 근거·완료 기록·*살아있는 유지보수 런북*은 계속 참조된다.

## 규칙

- 완료된 작업은 자기 서브폴더째 `mainPlan/_done/<name>/` 로 옮긴다(파일명 프리픽스 금지 — 경로 참조·문서 내부 상호참조가 깨진다).
- 각 폴더 `README.md` 상단에 `✅ 완료 (YYYY-MM-DD)` 배너 + 한 줄 요약.
- 완료 폴더 안에 **현역 운영 문서(런북·드리프트 레지스트리)** 가 섞여 있으면 그 README 가 명시한다(프로젝트는 끝났어도 배포된 시스템의 정비 문서는 계속 본다).
- 옮긴 뒤 memory 포인터·외부 참조 경로를 새 위치로 갱신한다.

## 보관 목록

| 폴더 | 완료·상태 | 한 줄 |
|---|---|---|
| `realestate-data/` | 🚫 폐기 2026-06-23 | 공공데이터 부동산 실거래(국토부 RTMS) 수집·분석조합 PRD. **미착수 영구 기각**(빌드 0줄). PRD는 96점 완성이나 코드 실측 결론 = net-new 거래량 1축뿐·P1 조건부·즉시가능 비자명연결 0, 게다가 RTMS 키-계정 미스매치(403)로 P1 검증조차 미수행 → ROI 낮아 폐기. 보관 사유 = 경계지도·KILL 5·feasibility 방법론 자산. README 상단 폐기 배너 참조. |
| `ui-platform-refactor/` | 2026-06-13 | public(GitHub Pages)·local(pip) 단일 UI 자산 공유 리팩토링(단계 1~10). ⚠ `08-shared-wiring-parity-maintenance.md` 는 현역 런북. |
| `scan-grade-explainer/` | 2026-06-15 | 스캔등급 설명 다이얼로그. as-built 는 PRD 확장 — 10~12 종합축 SSOT(`COMPOSITE_AXES`) 통일 + 등급 근거 = 축 자체 동종업종 백분위(midrank)+분포 막대 + 현금흐름 부호 표기. 구현 SSOT=`ui/packages/surfaces/src/terminal/`. |
| `data-build-workbench-ssot/` | 2026-06-21 | 공동작업대(in-library `dartlab.pipeline`) 데이터빌드 SSOT. MUST(macro 첫 증명) 흡수 완료 — sync 3 + prebuild 1 스크립트를 `stages/{macro,prebuild}.py` 로 흡수, 4스크립트 thin shim(중복 0). 구현 SSOT=`src/dartlab/pipeline/stages/`. ⏭ SHOULD(dart/news/gov)는 별개 후속 웨이브(미착수). |
| `industry-analysis-lab/` | 2026-06-23 | industry 엔진+양 터미널 세계수준화. 3 killer(profit-pool 격자·공시인용 공급망 evidence·산업 분포 밴드) + 묻어둔 함수 배선(집중도·edges amount/ratio·polarization verb) + 한계 라벨 + 레버A 재빌드(amount 132→1,097) 구현·검증·push 완료. 구현 SSOT=`src/dartlab/industry/`. ⏭ 보너스 2건(집중도 verb 화면배선·RightStack hop walk)은 PRD 본체 외 미착수. |
| `data-download-center/` | 2026-07-01 | HF parquet→Excel/구글시트 라이브 다운로드 센터. Tier1 브라우저 직독(xlsx/csv)+Tier2 무료 CF 워커(`dartlab-data-csv`), `/data` 프로덕션 라이브(미리보기·다운로드·HF 파일브라우저·라이브 API). **as-built 확장=런타임 변환 3종 라이브 API**(재무제표 bundleFromRows·주가 priceWithIndicators KR일봉+US·경제지표/지수 valueWithIndicators, 워커·브라우저 동일 변환 esbuild 공유·베이크 0). ⚠ 워커·`allowlist.js`·drift 가드(`test_worker_allowlist_in_sync`)는 **현역 배포 시스템**(유지보수 참조). ⏭ Phase5(날짜샤드·index.json)·macro CF observations 분할·landing UI push 미착수. 상세=memory [[project_data_download_center]]. |
| `ipo-prospectus-summary/` | 2026-07-03 (dev) | IPO 공모 신고서 분석(증권신고서 6카테고리). 엔진(providers 파서·`scan("ipo")`·story 리포트) + 로컬 서빙 + 터미널 IPO 뷰 + HF 베이크 직독 구현·실렌더 검증. **운영계약 = Skill OS `engines.scan` `scan("ipo")` 등록됨.** ⏳ 운영자 롤아웃 잔여 = hfProxy 재배포(/ipo-filings)·landing push. 베이크→왓치→알림 파이프라인 헬스체크는 `watcher-notify-platform/05 §감사`(현역 런북). |
| `watcher-notify-platform/` | 2026-06-30 (dev, 미배포) | 왓처·알림 플랫폼(PWA 웹푸시, 감지=dartlab·배달=CF thin 허브). P1+P2 코드 green(허브 16·러너 18·landing 17·크립토 16). ⏳ **미배포·운영자 롤아웃 대기**(런북 = `05-progress-ledger.md §배포`). ⚠ **운영계약 Skill OS operation 스펙 미등록**(선례 `operation.dataDownloadCenter` 대비 갭 → 배포 확정 후 `operation.notifyPipeline` 신설 필요). `05 §감사` = 현역 파이프라인 헬스체크 런북(자동 = Data Audit 매일 05시 KST). |
| `weekly-uplift-shortlist/` | 🔀 흡수 2026-07-05 | 주간 상승후보 100→10. 설계·빌드가 `scenario-simulator/06-engine-readings-and-sweep.md`(simulate L2.5 "현재" 축)로 흡수됨. 남은 것 = 갭 원장(03)·진행 원장(05) append-only 참조. 별도 운영계약 없음. |
| `panel-note-extraction-ssot/` | 🔀 흡수 2026-07-06 | Panel 주석 추출 SSOT(노트 한정). `panel-extraction-workbench-ssot`(활성)가 흡수·확장. 원본 PRD 는 설계 근거·IFRS 32종 카탈로그 자산으로 보존. 추출 능력은 `providers/dart/notes.py`+`core/_entries/notes.py` 소유. |
