# dartlab 이야기 파이프라인 (03-dartlab-stories)

> **뼈대는 [blog/PIPELINE.md](../PIPELINE.md)·[BLOG.md](../BLOG.md)를 그대로 준용한다.** 이 문서는 다른 카테고리와 다른 **델타만** 적는다(중복 금지). 강행규칙은 `CLAUDE.md`.

## 1. 정체성

기업이야기가 "한 회사의 왜?", 기술이야기가 "기술의 왜?", 데이터 리포트가 "시장 전체의 왜?"라면,
dartlab 이야기는 **"이걸 네가 직접 해 봐"** 다.

- **주어 = dartlab.** 회사도 기술도 시장도 아니다. 도구와 그 도구가 딛고 선 데이터가 주어다.
- **독자 = 아무것도 모르는 사람.** 파이썬을 처음 보는 사람이 첫 코드블록에서 결과를 본다.
- **읽는 글이 아니라 도는 글.** 본문 python 코드블록은 독자의 브라우저에서 그 자리에서 실행된다.
  버튼 하나로 그 글 전체가 노트북이 된다. 실행해 보지 않은 코드는 싣지 않는다.
- **커리큘럼은 연재가 진다.** 노트북 허브에는 레슨이 없다. 배우는 곳은 여기다.

## 2. 준용

Phase 1 적대 토론 기획 92점 루프 / Phase 2.5 마스터라이터 편집 게이트 / Phase 4 독자 루프 /
수치 6원칙·검증표 / 용어 풀어쓰기 / `audit_seo.py` 95 이상 / `auditBlog.py --gate` 통과.

## 3. 델타

1. **본문 코드 = 실행되는 셀.** ` ```python ` 코드펜스가 곧 실행 셀이다. 별도 문법도 별도 산출물도
   없다. `landing/src/routes/blog/[slug]/+page.svelte` 가 `pre[data-lang="python"]` 를 찾아 실행 막대를
   붙이고, 첫 블록에 "노트북 생성하기" 를 단다. 글이 SSOT 이고 노트북은 그 투영이다.
2. **코드는 공개 호출 계약만.** `dartlab.{engine}("{axis}", ...)` 와 `capabilityRefs` 등재 `Company` 메서드,
   이미 정의된 provider facade 뿐이다. `tests/audit/notebookContract.py` 가 이 카테고리 본문의 python
   코드펜스를 AST 로 훑어 계약 밖 심볼을 차단한다. 통과하지 못하면 발행되지 않는다.
3. **브라우저 경계를 숨기지 않는다.** 브라우저에서 안 도는 것(실시간 시세·수급·뉴스 수집,
   `dartlab.gather(...)` 최상위 호출, `scan("screen")`·`scan("workforce")`·`scan("quality")`)을 그 자리에서
   밝힌다. 실측 정본은 Skill OS `runtime.pyodide`. 게이트가 본문에 경계·오독 방지 문장을 요구한다.
4. **막이 아니라 단계.** 6막 인과 서사가 아니다. 최소 3단계: 무엇을 왜 배우나, 직접 해 본다,
   무엇을 얻었고 다음은 무엇인가. `brief.json` 의 `acts` 는 이 단계를 담는다(하한 3).
5. **이미지 = 기획이 정한 만큼.** 고정 하한을 두지 않는다. Phase 1 기획 루프가 `imagePlan` 에 그 편에
   **정말 필요한 그림만** 적고, **그 자리에서 수급·생성한다**(Phase 3 로 미루지 않는다). 발행 게이트는
   개수 하한이 아니라 **기획과 실물의 정합**을 본다. `assets` 이미지 수가 `imagePlan` 길이 이상, 본문
   삽입 이미지 수가 `inline` 슬롯 수 이상. 채우기용 이미지는 실패다.
6. **길이 = 밀도 우선.** 하한 3,000자, 목표 5,000자. 코드·표·SVG 를 뺀 읽는 글자수 기준이다.
   설명이 코드보다 길 필요는 없지만, 코드만 던지고 왜를 안 적으면 그건 문서지 이야기가 아니다.
7. **주어가 회사가 아니다.** `topicSlug` 를 쓰고 `stockCode` 는 달지 않는다. 예제 회사는 예제일 뿐이다.
8. **썸네일.** `gen_blog_thumbnails.py`(SSOT). kicker 라벨 = `PREFIX["dartlab-stories"] = "dartlab 이야기"`.
   `ogImage: /thumbnails/{slug}.webp`. 본문용 이미지를 썸네일 배경으로도 쓰려면 frontmatter 에
   `thumbnailBg: ./assets/<본문용-이미지>.webp` 를 명시한다. 본문에는 `*thumbnail-bg*.webp` 를 직접
   걸지 않는다. 그 파일은 OG 합성용 소스라 실제 사이트 본문에서 깨질 수 있다.
9. **누적이 곧 커리큘럼.** 편 번호가 학습 순서다. 앞 편이 세운 개념을 뒤 편이 딛는다. 새 편을 끼워
   넣을 때는 번호와 `seriesOrder` 를 함께 옮긴다. 전체 지도는 비공개 설계문서
   `mainPlan/dartlab-story-curriculum/` 이 정본이다.

## 4. 기획 (Phase 1)

```bash
Workflow({
  scriptPath: "blog/_scripts/blog_plan_loop.workflow.js",
  args: { contentKind: "dartlab-stories", topic: "<이 편이 가르치는 개념 하나>", evidence: "<실측 근거>" }
})
```

`CONTENT_GUIDANCE['dartlab-stories']` 와 `LENSES_BY_KIND['dartlab-stories']`(교육설계자 vs dartlab
엔지니어) 가 이 카테고리 지침이다. 92점을 넘으면 `brief.json` 을 글 폴더에 쓰고, **그 자리에서
`imagePlan` 대로 이미지를 만든다**.

## 5. 발행 게이트

```bash
uv run python -X utf8 tests/audit/notebookContract.py             # 본문 코드가 공개 계약 안인가
uv run python -X utf8 blog/_scripts/auditBlog.py --gate blog/03-dartlab-stories/<폴더>
uv run python -X utf8 blog/_scripts/audit_seo.py                  # 95 이상
```

그리고 **브라우저에서 눈으로 확인한다.** `cd landing && npm run dev` 후 그 글을 열어 모든 실행
막대를 눌러 본다. 결과가 안 나오는 코드는 글에서 뺀다.
