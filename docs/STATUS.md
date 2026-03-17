# docs/ 현황

## 현재 기준

공개 문서의 중심 메시지는 이제 `sections -> show -> trace`다.

문서는 더 이상 parser 목록이나 property 카탈로그를 먼저 설명하지 않는다. 먼저 `Company`와 `sections`를 소개하고, 그 다음에 source namespace와 OpenAPI로 내려가는 흐름으로 정리한다.

## 핵심 공개 문서

```text
docs/
├── index.md                         # sections 중심 제품 개요
├── getting-started/
│   ├── installation.md              # 설치
│   └── quickstart.md                # Company -> sections -> show -> trace
├── api/
│   ├── overview.md                  # 공개 surface 개요
│   ├── finance-summary.md           # finance 상세
│   ├── finance-statements.md        # statements 상세
│   └── finance-others.md            # 레거시/세부 API 참고
├── tutorials/
│   ├── 01_quickstart.md             # sections-first 첫 분석
│   └── 09_edgar.md                  # EDGAR Company / OpenEdgar 흐름
├── stability.md                     # 현행 안정성 tier
└── changelog.md                     # 공개 변경 이력
```

## 공개 서사

- `Company`가 메인 진입점
- `sections`가 canonical company board
- `show(topic)`이 topic payload를 연다
- `trace(topic)`이 source와 provenance를 설명한다
- `OpenDart`, `OpenEdgar`는 source-native public API wrapper다
- AI GUI는 같은 company map을 소비하는 다음 인터페이스다

## 정리 원칙

- `Compare`는 메인 공개 서사에서 빼둔다
- `index`는 공개 기본 경로에서 제거한다
- `ShowResult` 같은 과거 반환형 설명은 공개 문서에서 제거한다
- `40 modules` 같은 옛 메시지는 홈/빠른시작/랜딩에서 쓰지 않는다

## 렌더링 / 배포

- SvelteKit + mdsvex
- `/docs`는 정적 빌드 결과로 GitHub Pages에 배포
- 랜딩과 docs는 같은 브랜드/메타를 공유

## 현재 상태

- [x] README / README_KR sections 중심 재작성
- [x] docs/index, quickstart, api/overview 재정렬
- [x] tutorials/01_quickstart, tutorials/09_edgar 현행화
- [x] stability 문서에서 `index`, `Compare` 공개 노출 정리
- [x] 랜딩 hero / architecture / workflow / CTA 메시지 재작성
- [ ] finance 상세 문서(`api/finance-*`)의 sections-first 서사 추가 정리
- [ ] 나머지 튜토리얼 구간의 오래된 property 중심 문구 추가 정리
