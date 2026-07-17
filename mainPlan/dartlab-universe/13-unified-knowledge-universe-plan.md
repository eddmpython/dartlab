# 13. Unified Knowledge Universe Plan

## 1. 제품 목표

DartLab Universe는 파일 탐색기, 금융 대시보드, 블로그, 단순 그래프, 3D 점구름이 아니다.

최종 제품은 다음 네 능력을 동시에 갖는다.

1. `eddmpython/dartlab-data`의 모든 파일과 DartLab Skill OS, capability, 문서 및 공개 지식을 하나의 주소 공간에 등록한다.
2. 전체 우주에서 은하, 데이터 계층, 개체, 문서, 관측, 원본 행까지 의미가 바뀌는 시맨틱 줌으로 이동한다.
3. 선택한 지식의 정의, 속성, 관계, 원본 근거, 시점, 수정 이력을 Knowledge Lens에서 읽는다.
4. 관계가 생성되고 지식이 전개되는 순서를 결정론적 Knowledge Film으로 재생하고 같은 장면을 다시 재현한다.

공개 운영 계약은 고정이다. `/universe` 라우트는 유지하되 사용자 검수와 명시적 승인 전까지 공개 진입 버튼과 공개 내비게이션 링크는 0개다.

## 2. 전체의 정확한 의미

### Catalog complete

HF revision의 모든 sibling path와 Skill OS의 모든 항목을 중복 없이 정확히 한 domain에 귀속한다. 합계는 `hfFileCount + skillCount = addressableItemCount`이고 12개 domain 합계와 반드시 같아야 한다.

### Content reachable

파일명만 검색되는 상태는 최종 완성이 아니다. 파일 형식별 content adapter가 필요하다.

| 형식 | 지연 해소 방식 | 제품 표현 |
|---|---|---|
| Parquet | footer, schema, row group, column range | 표, 관측, 개체, 시계열 |
| JSON 및 JSONL | bounded parse, pagination | 구조 트리, 문서, 관계 |
| CSV 및 TSV | header 우선, chunk parse | 표, 관측 |
| Markdown 및 text | section index, exact span | 위키 문서, 인용 근거 |
| 이미지 및 영상 | metadata 우선, 원본 on demand | 미디어 노드, Knowledge Film |
| wheel 및 runtime artifact | manifest 및 capability refs | 엔진 및 능력 계보 |

[Hugging Face의 Parquet 설명](https://huggingface.co/docs/dataset-viewer/parquet)은 column projection과 row group skip이 전체 파일 다운로드를 피하는 핵심이라고 설명한다. [rows API](https://huggingface.co/docs/dataset-viewer/rows)도 최대 100행의 slice를 제공한다. Universe는 같은 원칙을 현재 DataCore range 런타임에 적용한다.

### Scene bounded

화면은 전체 데이터의 복사본이 아니다. 장면은 사용자 질문과 현재 zoom에 필요한 최대 80개 노드만 담는다. 장면 밖 항목은 숨긴 척하지 않고 `indexedItemCount`, `outputNodeCount`, `omittedNodeCount`, `sourceRevision` 영수증으로 표시한다.

## 3. 벤치마크와 채택 판단

| 대상 | 강점 | 채택 | 그대로 복제하지 않는 것 |
|---|---|---|---|
| Wikipedia 및 MediaWiki | 내부 링크, 외부 링크, 정확한 reference, revision history와 permanent link | Knowledge Lens에 본문, 표, 미디어, 근거, 변경 이력을 한 문서 경험으로 결합 | 페이지들이 공간 관계와 분석 엔진에서 분리되는 구조 |
| TheBrain | 현재 생각을 중심으로 부모, 형제, 자식 맥락을 즉시 전환 | 선택 중심 local context와 한 번에 이해 가능한 이웃 | 근거 상태와 데이터 계보가 없는 자유 연결 |
| Obsidian Graph | global graph, local graph, 깊이 조절, 생성 시간순 애니메이션 | 전체 조망과 선택 주변 장면의 이중 모드, 시간 전개 | 모든 링크를 같은 강도로 그리는 force graph |
| Neo4j Bloom | category와 relation을 제한한 Perspective, scene 저장 | 12개 은하와 lens가 같은 정본에 다른 perspective를 적용 | 브라우저 공개 제품에 별도 graph DB와 전량 scan 도입 |
| Mapbox | zoom level별 layer visibility와 zoom-driven style | L0부터 L5까지 representation 자체를 교체하는 시맨틱 줌 | 같은 노드를 단순 확대하는 카메라 zoom |
| NASA Eyes | 자유 탐색과 guided replay를 같은 공간에 결합 | 수동 탐색과 Knowledge Film의 공존 | 3D와 장식이 기본 정보 구조를 지배하는 방식 |
| Cosmograph | WebGL 기반 대규모 네트워크 렌더링 | Canvas 2D budget을 실제로 넘을 때만 선택 가능한 adapter 후보 | 초기 번들, 라이선스 및 접근성 검증 없이 기본 renderer로 고정 |

근거 링크:

- [MediaWiki links](https://www.mediawiki.org/wiki/Help:Links/en), [references](https://www.mediawiki.org/wiki/Page_Content_Service/References), [history](https://www.mediawiki.org/wiki/Help:History/en)
- [TheBrain visual knowledge network](https://thebrain.com/)
- [Obsidian Graph view](https://obsidian.md/help/Plugins/Graph%2Bview)
- [Neo4j Bloom Perspectives](https://neo4j.com/docs/bloom-user-guide/current/bloom-perspectives/perspective-creation/)
- [Mapbox zoom-driven styling](https://docs.mapbox.com/mapbox-gl-js/guides/styles/style-layers/)
- [NASA Experience Curiosity](https://eyes.nasa.gov/curiosity)
- [Cosmograph documentation](https://cosmograph.app/docs-general/)

## 4. 선택 스택

### 제품 shell

- Svelte 5와 TypeScript를 유지한다.
- route 조립은 `landing`, 제품 계약은 `ui/packages/contracts`, 데이터와 projection은 `ui/packages/runtime`, 화면은 `ui/packages/surfaces`에 둔다.
- 공개와 local은 동일 runtime을 사용한다.

### 데이터 작업대

- 모든 네트워크 호출은 `data/fetch.request()`와 `data/origins`를 통과한다.
- HF Hub API는 metadata와 전체 file catalog만 담당한다.
- 실제 내용은 기존 HF range, Parquet, JSON 및 text adapter가 revision 고정 주소에서 지연 해소한다.
- 초기 요청은 작은 metadata, root tree, Skill graph뿐이다. 전체 파일 index와 skill catalog는 idle 이후 한 번 로드한다.
- 별도 Neo4j, GraphQL, 서버 graph DB, 전량 client download는 도입하지 않는다.

### projection과 검색

- catalog index는 file path, title, purpose, refs, domain, lifecycle을 가진다.
- 검색은 exact, prefix, token AND, domain filter 순으로 결정론적 점수를 쓴다.
- 다음 단계에서 catalog scan과 layout은 Web Worker로 이동하고, query token으로 stale result를 폐기한다.
- 검색 결과와 각 계층은 최대 80개 노드의 bounded scene으로 컴파일한다.

### renderer

- 제품 기본은 dependency-free Canvas 2D다.
- continuous animation loop는 금지하고 resize, camera, selection, film beat가 바뀔 때만 한 프레임을 예약한다.
- DOM 44px hit target과 완전 동등한 table view를 항상 제공한다.
- WebGL adapter는 실제 500노드 이상 상호작용 요구와 성능 측정이 발생한 뒤 별도 admission을 통과해야 한다.

## 5. 정보 구조

12개 은하는 다음과 같다.

1. 데이터 원천
2. 법인과 기관
3. 증권과 시장
4. 공시와 문서
5. 재무 관측
6. 산업과 관계
7. 가격과 퀀트
8. 거시와 공공
9. 뉴스와 리서치
10. 엔진과 능력
11. Skill OS
12. 시간과 미디어

법인, 공시, 재무 관계는 4개 이상의 은하를 연결하는 대표 지식 경로다. 그러나 시작 화면은 특정 금융 장면이 아니라 모든 은하를 동등하게 보여주는 macro universe다.

## 6. GUI 기획

### 상단 Command Bar

- 현재 지식 주소 breadcrumb
- 회사, 공시, 데이터, 엔진, 스킬을 함께 찾는 omnibox
- 정확한 addressable item count, HF revision, main size 상태

### 좌측 Galaxy Rail

- 12개 은하와 정확한 항목 수
- domain filter와 현재 위치
- 모바일에서는 가로 스크롤 가능한 은하 strip

### 중앙 Spatial Stage

- L0 전체 12개 은하
- L1 domain cluster
- L2 directory, dataset, capability family
- L3 entity, filing, skill, document
- L4 observation, table, section, media
- L5 exact row, cell, span, source revision
- 휠 확대 임계값에서 선택한 expandable node를 새 장면으로 연다.
- 축소 임계값에서 parent scene으로 돌아간다.

### 우측 Knowledge Lens

- 정의와 식별자
- 타입과 domain
- 들어오고 나가는 relation
- 속성, 단위, 기간, lifecycle
- exact sourceRef와 revision
- rich content preview, 표, 이미지, 영상
- 수정 이력과 evidence status

### 하단 Knowledge Film

- 재생, 정지, 이전, 다음, 0.5배, 1배, 2배
- beat별 camera focus, reveal node, reveal edge, narration
- scene receipt와 revision 표시
- `prefers-reduced-motion`에서는 즉시 장면 전환

## 7. 구현 단계

### K0 Goal lock와 catalog spine

- 전체 HF file catalog 및 Skill OS 정확 계수
- 12개 domain classifier
- root, domain, directory, file, skill scene
- bounded receipt와 revision source URL
- 상태: 2026-07-17 첫 수직 슬라이스 구현

### K1 Content adapters

- Parquet schema 및 row group explorer
- JSON, CSV, text, markdown, media preview
- exact source locator
- 파일명 수준에서 실제 내용 수준으로 완성도를 올리는 필수 단계
- 상태: K1a 완료. HF catalog commit을 고정한 byte range, Parquet 12행 및 16열 bounded preview, text 및 JSON 원문, 이미지와 영상 및 오디오 reference를 Knowledge Lens에 연결했다.
- 상태: K1b 구조화 preview 완료. JSON을 최대 96개 node의 hierarchy tree로 투영하고 raw 원문을 함께 유지한다. CSV 및 TSV는 quote, 중복 header, cell 내부 newline, 잘린 마지막 행을 처리하는 최대 12행 및 16열 표로 투영한다.
- 상태: K1c Parquet metadata 완료. parsed footer를 행 읽기와 공유하는 단일 preview session에서 file size, 전체 row, row group count, physical 및 logical schema, request count와 transfer bytes를 함께 반환한다.
- 상태: K1d row window 완료. 전체 row 범위 안에서 이전 및 다음 12행을 revision 고정 cache key로 이동하고 현재 시작 및 끝 행을 전체 row와 함께 표시한다.
- K1 잔여: 파일별 수정시각 metadata와 K1b부터 K1d까지의 실브라우저 눈검수를 완료한다.

### K2 Semantic ontology

- entity, security, filing, document, section, observation, capability, skill, media ID
- contains, describes, observed, computed, used, supported, revised relation
- 기존 finance atlas와 global DART 및 EDGAR 기능을 12개 은하에 결속

### K3 Retrieval worker

- 68K 이상 catalog worker index
- domain 및 kind filter
- stale query cancellation
- 첫 검색과 warm 검색 성능 측정

### K4 Wiki-grade Lens

- article lead, 목차, 표, 이미지, 출처, 변경 이력
- relation에서 원문 span 및 table cell 왕복
- missing과 candidate를 fact처럼 보이지 않는 lane

### K5 Knowledge Film compiler

- 수동 scene beat
- query 및 workflow에서 결정론적 beat 자동 컴파일
- shareable flight receipt와 camera path

### K6 Product hardening

- 1440, 768, 390, 320px
- keyboard, table parity, reduced motion, high contrast
- console error 0
- 공개 진입 버튼 0 유지
- 사용자 직접 검수 후 별도 push 승인

## 8. 제품급 종료 조건

- 현재 HF revision의 모든 file path와 모든 Skill OS 항목이 정확히 한 번 주소화된다.
- 12개 domain count 합계가 addressable total과 일치한다.
- 모든 지원 형식이 파일명에서 끝나지 않고 실제 내용 preview 또는 정확 원본 주소로 이어진다.
- 대표 경로 20개가 `Universe > domain > dataset > entity or document > exact evidence`로 왕복한다.
- cold overview 1.5초, warm scene 300ms, warm search 120ms 목표를 측정한다.
- 장면은 80개 노드 이하이며 모든 생략이 receipt에 기록된다.
- graph를 못 쓰는 환경에서 table view로 동일 작업을 완료한다.
- film이 같은 revision과 query에서 같은 beat 및 camera target을 만든다.
- 공개 진입 버튼과 공개 링크는 사용자 승인 전 0개다.

## 9. 현재 완성도 판정

2026-07-17 현재는 K0와 K1a 및 K1b 구조화 preview 수직 슬라이스다. 전체 HF file path와 Skill OS를 하나의 주소 공간으로 검색 및 탐색하고, 12개 은하, 시맨틱 줌, Knowledge Lens, table parity, Knowledge Film 기본 제어가 연결됐다. 파일을 한 번 선택하면 catalog commit에 고정된 text, JSON, Parquet, 이미지, 영상 및 오디오 원본을 형식에 맞게 지연 해소한다. JSON은 구조 tree와 raw 원문을 함께 보이고 CSV 및 TSV는 bounded table로 읽는다.

아직 최종 완성이라고 부르지 않는다. K1 file metadata와 구조화 preview 실브라우저 검수, K2 전체 semantic relation, K3 worker index, K4 wiki-grade rich content, K5 workflow film, K6 성능과 접근성 hardening 및 사용자 눈검수가 남아 있다.
