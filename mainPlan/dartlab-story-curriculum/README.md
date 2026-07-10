# dartlab 이야기 커리큘럼 (비공개 설계문서)

> **공개하지 않는다.** 이 문서는 운영자가 나중에 보고 판단하기 위한 편성 지도와 원장이다.
> 독자가 보는 것은 발행된 글뿐이다. 편 하나가 발행될 때마다 여기 체크박스가 닫힌다.
>
> 관련: 카테고리 운영 규약 = `blog/03-dartlab-stories/PIPELINE.md` (공개).
> 발행 게이트 = `tests/audit/notebookContract.py` + `blog/_scripts/auditBlog.py` + `blog/_scripts/audit_seo.py`.

## 0. 지금 상태

| | |
|---|---|
| 발행 완료 | 2 편 (1편 what-is-dartlab, 2편 call-financial-statements) |
| 설계 완료 | 35 편 (전문 에이전트 4 안 경합 + 심사 + 수렴 + 적대 감사, 2026-07-10) |
| 채점 | pedagogy 78 · coverage 75 · skeptic 71 · seo 66 (인플레 없이) |
| 승자 | pedagogy 안. 나머지 셋에서 살릴 아이디어를 접목 |

브라우저 노트북 허브의 레슨 15 편은 **폐기했다**. 배우는 곳은 블로그이고, 노트북은 실습장이다.
레슨 YAML · 레지스트리 · `lessonSchema.py` 게이트는 전부 삭제했다.

## 1. 사상

브라우저에서 **실제로 도는 것만** 가르친다. 안 되는 것은 감추지 않고 그 자리에서 밝히고,
`pip install dartlab` 이후 열리는 로컬 코스로 정직하게 분리한다.

편수를 채우려고 능력 하나를 한 편으로 기계 분할하지 않는다. 편은 **사람의 질문**으로 선다.
"잘 벌고 있나", "돈 떼일 위험은 얼마인가", "이 숫자는 어디서 왔나". 능력 이름이 제목이 되는 순간
그것은 도감이지 이야기가 아니다.

독자용 문구에 "축"(axis)이라는 말을 쓰지 않는다. 내부 용어다.

## 2. 트랙 여섯

| id | 제목 | 목표 |
|---|---|---|
| `start` | 시작하기 | 설치 없이 첫 재무제표를 띄우고 노트북 조작 감을 잡는다. 첫 성공을 앞에 준다 |
| `read` | 재무제표 읽기 | 넓은 표에서 원하는 숫자를 꺼내고 직접 계산한다. 파이썬 가공을 처음 만난다 |
| `interpret` | 해석과 판단 | 수익성·신용·거시로 읽고, 자동 해석을 출처로 되짚어 검증하는 습관 |
| `market` | 전종목으로 보기 | 한 회사를 넘어 전 상장사를 한 표로. 관점을 시장으로 넓힌다 |
| `compose` | 엮어서 한 편의 분석 | 조각을 이어 한 회사를 입체로 조립하고, 에러를 넘어 내 노트북을 완성한다 |
| `local` | 로컬로 확장 | 브라우저가 못 하는 시세·뉴스·스크리닝·원문 공시를 pip 설치 후 여는 졸업 코스 |

## 3. 편성표

`B` = 브라우저에서 본문 코드가 전부 돈다. `L` = 로컬 전용(본문에 그렇게 밝힌다).

### start

- [x] **1. dartlab이란 무엇인가** `what-is-dartlab` `B`
  정체 + 데이터 구조(항목 x 기간 격자) + 수집·가공·배포 3층 운영.
  코드: `Company("005930")`, `panel("IS").head(3)`, `market`, `panel("BS").shape`, `scan("growth").shape`, `select("IS", ["매출액"], freq="Y")`
- [x] **2. 재무제표를 코드 두 줄로 꺼내는 법** `call-financial-statements` `B`
  panel IS/BS/CF, select, 연간과 분기, 계정 이름이 회사마다 다른 문제, 빈칸의 의미.
- [ ] **3. 코드를 실행한다는 것** `how-notebook-runs` `B`
  셀·실행·결과·재실행, 그리고 "노트북 생성하기" 로 글을 내 것으로 가져오는 루프.
  ⚠ 적대 감사 지적: 새 능력 0. 1·2편이 이미 다룬다. **단독 편으로 설 수 있는지 재검토, 안 되면 폐기.**
- [ ] **4. 회사를 여섯 자리 코드로 지목한다** `pick-company-by-code` `B`
  종목코드 개념. 브라우저에는 이름을 코드로 되돌리는 길이 없으므로 랜딩 검색으로 코드를 찾아 온다.

### read

- [ ] **5. 항목과 기간이 만나는 넓은 표** `the-grid` `B`
  panel 이 격자라는 사상. `freq="Y"` 와 `"Q"` 로 기간을 바꾼다.
  ⚠ 설계안의 `freq="year"` 는 **미지원 값**이다. `Y` / `Q` / `YTD` 만 있다. `panel()` 빈 괄호 호출도 미측정.
- [ ] **6. 필요한 줄만 이름으로 뽑아낸다** `select-rows` `B` (2편이 일부 흡수. 잔여는 항목명 검색)
- [ ] **7. 뽑은 숫자로 직접 계산한다** `compute-from-values` `B`
  select 결과를 파이썬으로 다뤄 영업이익률을 직접 구한다. 첫 데이터 가공.
- [ ] **8. 이 숫자는 어디서 왔나** `trace-the-number` `B`. `Company.trace("영업이익")`

### interpret

- [ ] **9. 무엇을 물어볼 수 있나** `analysis-catalog` `B`. 인자 없이 부르면 목록이 열린다는 되묻기 패턴
  ⚠ 되묻기는 `scan()`, `credit()`, `macro()` 에서도 된다. analysis 하나로만 시연하면 독자가 일반화를 못 배운다.
- [ ] **10. 이 회사, 잘 벌고 있나** `is-this-company-good` `B?`. `analysis("financial", "수익성")`
  ⚠ finance-lite 로 재무 그룹 값이 실제로 채워지는지 **미검증**(`scan("quality")` total_assets 부재 선례). 발행 전 실행 필수.
- [ ] **11. 돈 떼일 위험은 얼마인가** `credit-risk` `B`. `credit("채무상환능력")`
- [ ] **12. 사람이 읽는 문장으로 받는다** `story-report` `B`. `story("full")`
- [ ] **13. 회사 밖 경제를 함께 본다** `macro-backdrop` `B`. `dartlab.macro("rates")`
- [ ] **14. 자동 해석을 그대로 믿지 않기** `dont-trust-blindly` `B`. 자동 분석의 한계 + 출처 되짚기

### market

- [ ] **15. 한 회사에서 전 상장사로** `from-one-to-all` `B`. `scan("growth")`
- [ ] **16. 진짜 남는 장사를 하는 회사** `who-makes-money` `B`. `scan("profitability")`, `scan("ratio")`
- [ ] **17. 쉽게 안 망할 회사 고르기** `who-wont-go-bust` `B`. `scan("liquidity")`, `scan("debt")`
- [ ] **18. 현금이 실제로 도는가** `cash-and-accounts` `B`. `scan("cashflow")`, `scan("account")`
- [ ] **19. 전종목 표를 내 질문으로 거른다** `filter-to-my-question` `B`
  ⚠ 16·19·21편이 `scan("profitability")` 를 반복한다. 서로 다른 질문으로 서지 못하면 축 나열이다.

### compose

- [ ] **20. 두 회사를 나란히 놓는다** `two-companies` `B`. select 두 번 + 파이썬 정렬 (compare 는 로컬 한 줄로만 언급)
- [ ] **21. 전종목 속 이 회사의 자리** `where-it-sits` `B`. scan 은 후보일 뿐, 다시 회사로 돌아와 검증
- [ ] **22. 한 회사를 여러 각도로 조립한다** `one-company-full` `B`
- [ ] **23. 안 될 때: 에러를 읽는 법** `when-it-breaks` `B`. 오타 코드, 빈 결과, try/except
- [ ] **24. 나만의 분석 노트북을 완성한다** `build-your-notebook` `B`. 브라우저 코스 졸업작

### local

- [ ] **25. 브라우저의 끝, 로컬의 시작** `end-of-browser` `B`. 인자 없는 수집 목록을 브라우저에서 미리 보고, 왜 설치가 필요한지
- [ ] **26. 실시간 시세를 끌어온다** `live-prices` `L`. `Company.gather("price")`
- [ ] **27. 뉴스·수급·지분을 모은다** `news-flows-owners` `L`
  ⚠ 이 데이터는 저작권상 **발행 금지**다. 본문에 결과 표를 싣지 말고 호출법만 가르친다.
- [ ] **28. 지금 비싼가 싼가** `valuation-local` `L`. 시세가 붙어야 값이 찬다
- [ ] **29. 조건으로 전종목을 거르는 진짜 스크리너** `real-screener` `L`. `scan("screen")`
- [ ] **30. 사람 수로 회사를 본다** `workforce-local` `L`. `scan("workforce")`
- [ ] **31. 이름으로 회사를 찾는다** `find-by-name` `L`. `search`, `codeToName`
- [ ] **32. 공시 원문을 직접 읽는다** `raw-filings` `L`. `liveFilings`, `readFiling`
- [ ] **33. 미국 기업도 같은 방식으로** `us-companies-edgar` `L`. `OpenEdgar`
- [ ] **34. 여기서 어디로 더 가나** `next-steps` `B`. 터미널, MCP, Skill OS, quant 로 이어지는 지도

## 4. 적대 감사가 잡은 것 (2026-07-10)

이미 반영한 것.

- **1편의 `Company.corpName` 은 계약 미등재**다. 어느 엔진 skill 의 `capabilityRefs` 에도 없다.
  게다가 브라우저에서는 회사명이 아니라 `'005930'` 을 돌려준다(`providers/dart/company.py` pyodide 폴백).
  본문에서 제거했고, "브라우저는 코드로만 부른다" 는 경계 수업으로 바꿨다.
- **`c.select(...)` 이 브라우저에서 아무것도 출력하지 않던 문제**는 dartlab 이 아니라 노트북 워커 버그였다.
  `wrapLastExpression` 의 정규식 `^[a-zA-Z_]\w*[\[.].*=` 가 괄호 안 키워드 인자(`freq="Y"`)를 대입문으로
  오인해 마지막 식을 통째로 버렸다. 오류도 안 나고 빈 출력이라 아무도 몰랐다.
  괄호 깊이를 세는 스캐너로 교체했다(`pyodideWorker.ts`).

아직 안 닫은 것은 5절 체크리스트와 6절 TODO 로 넘겼다.

## 5. 편당 발행 체크리스트

새 편을 쓸 때마다 이 순서로 닫는다.

- [ ] 기획 루프를 돌린다. `Workflow({ scriptPath: "blog/_scripts/blog_plan_loop.workflow.js", args: { contentKind: "dartlab-stories", topic, evidence } })`
      92점을 넘어야 `brief.json` 이다. `evidence` 에는 **브라우저에서 직접 돌려 얻은 값만** 넣는다.
      (Git Bash 에서 워킹트리 파일은 CRLF 라 승인 다이얼로그가 막는다. LF 사본을 스크래치패드에 두고 그 경로로 돌린다.)
- [ ] 기획이 정한 `imagePlan` 대로 **그 자리에서** 이미지를 수급한다. `gen_blog_cc0.py --only <폴더>`
      개수 하한은 없다. 채우기용 이미지는 발행 게이트가 아니라 이 문장이 막는다.
- [ ] 본문을 쓴다. python 코드펜스가 곧 실행 셀이다. 별도 문법 없음.
- [ ] **본문의 모든 코드를 브라우저에서 실제로 실행한다.** 결과가 안 나오는 코드는 글에서 뺀다.
      정적 소스에서 뽑은 인자 문자열은 근거가 아니다.
- [ ] `gen_blog_thumbnails.py --slugs <slug> --apply`
- [ ] `uv run python -X utf8 tests/audit/notebookContract.py` (본문 코드가 공개 계약 안인가)
- [ ] `uv run python -X utf8 blog/_scripts/auditBlog.py --gate blog/03-dartlab-stories/<폴더>`
- [ ] `uv run python -X utf8 blog/_scripts/audit_seo.py` (95 이상)
- [ ] 브라우저 눈검수. 다크·라이트 둘 다.
- [ ] 이 문서의 체크박스를 닫고, 편 번호와 `seriesOrder` 가 어긋나지 않았는지 본다.

## 6. 운영자 판단 대기 (TODO)

- [ ] **3편 `how-notebook-runs` 를 살릴 것인가.** 새 능력이 0 이고 1·2편과 겹친다. 폐기하거나,
      "셀은 위에서 아래로 커널을 공유한다" 는 진짜 개념 하나로 다시 세워야 한다.
- [ ] **`Company.industry` 를 커버할 것인가.** `engines.industry` 의 capabilityRefs 에 등재된 계약인데
      35편 어디에도 없다. 업종·동종 시각은 회사 분석의 핵심 각도다. 브라우저 가부 미측정.
- [ ] **`Company.view`(dashboard), `Company.reportModel` 을 커버할 것인가.** 등재 계약이지만 부재.
      `view` 는 로컬 서버를 띄우는 것이라 브라우저와 개념이 안 맞는다.
- [ ] **로컬 전용 편(26~33)의 실행 셀을 어떻게 보일 것인가.** 눌러도 안 도는 셀은 독자에게 고장으로 읽힌다.
      실행 막대를 감출지, 눌렀을 때 "로컬에서만 됩니다" 를 띄울지. 지금은 아무 처리도 없다.
- [ ] **`analysis("financial", "수익성")` 이 브라우저에서 값을 채우는가.** 미검증.
      비면 10·22·24편의 뼈대가 무너진다. 발행 전에 반드시 실행해 확인하고, 비면 credit/scan 기반으로 대체한다.
- [ ] **`notebookContract.py` 의 부채 원장 19 건.** `notebooks/` 의 colab·marimo 예제가 계약 밖 메서드
      (`c.show`, `c.diff`, `c.topics`, `c.BS/CF/IS` 등)를 부른다. 계약에 등재할지, 예제를 고칠지.
- [ ] **Skill OS 문서 안의 계약 위반.** `c.show` 40 회, `dartlab.flow` 11 회, `dartlab.fixedIncome` 7 회,
      `c.topics` 6 회. `c.show` 는 `Company` 에 아예 없는 메서드다. 공개 문서가 이미 깨져 있다.

## 7. 회귀 가드

| 무엇이 무너지면 | 무엇이 잡나 |
|---|---|
| 본문 코드가 공개 계약 밖 심볼을 부른다 | `tests/audit/notebookContract.py` (CI fast `notebooks` 게이트) |
| 채우기용 이미지가 붙는다 | `auditBlog.py` 가 `imagePlan` 길이와 실물 개수의 정합을 본다 |
| 6막 인과 템플릿이 교육 연재에 되살아난다 | `GENRE_PLAN_SHAPE["dartlab-stories"] = {acts: 3, visuals: 1, images: 1}` |
| 브라우저 경계를 안 밝힌 글이 나간다 | `_validate_genre_body` 가 경계·오독 방지 문장을 요구한다 |
| 주어가 회사로 미끄러진다 | `stockCode` 를 달면 게이트가 막는다 (`topicSlug` 필수) |
| 노트북 셀 출력이 조용히 사라진다 | 아직 자동 가드 없음. 6절 TODO |
