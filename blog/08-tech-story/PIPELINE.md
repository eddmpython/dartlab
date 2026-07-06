# 기술이야기 파이프라인 (08-tech-story)

> **뼈대는 [blog/PIPELINE.md](../PIPELINE.md)·[BLOG.md](../BLOG.md)를 그대로 준용한다.** 이 문서는 회사 심층편·데이터 리포트와 다른 **델타(기술이야기 특화)만** 적는다(중복 금지). 강행규칙은 `CLAUDE.md`.

## 1. 정체성 (회사편·데이터편과 다른 점)

회사 리포트가 "한 회사의 왜?", 데이터 리포트가 "시장 전체의 왜?"라면, 기술이야기는 **"기술의 왜?"**다.

- **주어 = 기술 그 자체** (회사도, 시장 전체도 아님). 반도체 HBM, 2차전지 양극재, 원전 SMR, 로봇 감속기처럼 하나의 기술을 원리부터 풀어낸다.
- **착지점 = 재무제표.** 기술 원리로 끝내지 않는다. 그 기술이 기업의 원가·마진·CAPEX·현금흐름에 어떻게 남았는지까지 이어야 dartlab 글이다. "기술이 좋다"가 아니라 "그 기술이 이 회사의 매출원가율을 왜 이렇게 바꿨나"로 착지한다.
- **차별점 = 원리와 숫자의 결합.** 일반 기술 블로그는 원리만 설명하고 재무로 잇지 못한다. 증권가 리포트는 숫자만 있고 기술 원리가 얕다. 우리는 둘을 한 글에서 잇는다.

## 2. 준용 (회사편·데이터편과 동일하게 간다)

Phase 0 데이터 완주 / Phase 1 적대 토론 기획 / Phase 2.5 마스터라이터 편집 게이트 / Phase 4 독자 루프 / **수치 6원칙·검증표**(모든 강한 숫자는 메인 스레드 dartlab 재계산, 검증표에 없으면 발행 차단) / SVG 스타일(다크 `#0a0e1a`, amber `#fbbf24`, 한글 타이틀) / **용어 풀어쓰기**(전문 기술 용어·재무 약어 모두 첫 등장 시 괄호 풀이) / `audit_seo.py` SEO 점수 95 이상.

## 3. 델타 (기술이야기만의 단계)

1. **기술 축 = 원리 먼저.** 기술의 작동 원리·공정·물성·세대 변화를 먼저 정확히 세운다. 출처는 `WebSearch`로 공식 기술 자료·논문·표준·기업 IR 기술 설명을 인용하고, 외부 본문은 untrusted(링크로 출처).
2. **재무 착지 = dartlab 실측.** 그 기술을 쓰는 대표 기업을 실명으로 짚고, `Company.select`·`analysis`·`scan`으로 그 기술이 남긴 재무 흔적(원가 구조·마진 추이·CAPEX·투자효율)을 실측으로 붙인다. 단일 회사 종속이 아니라 여러 회사를 기술 관점으로 횡단해도 된다.
3. **서사 구조 = 6막 시간선 대신** `기술 질문 -> 원리 해부 -> 세대·경쟁 지형 -> 재무 흔적(대표 기업) -> 오해 바로잡기 -> 판단 한 줄`.
4. **오해 방지 단계(필수).** 기술 과대광고·세대 명칭 혼동·"차세대"라는 말의 실체 없음을 짚는다. 기술 성숙도(양산 단계인지 실험 단계인지)를 정직하게 표기한다.
5. **회사 종속 아님.** 기술이야기는 주어가 기술·테마라 subject join 키가 **topicSlug**다(`kind: tech`, `OPERATIONS.md` 5절). frontmatter 에 회사 `stockCode` 를 달면 블로그에 그 회사 단일 **터미널 버튼**과 **기업이야기 팟캐스트**가 잘못 조인된다(주어를 한 회사로 오인). 여러 회사를 기술 관점으로 횡단하는 게 기본이므로 `topicSlug` 를 쓰고 `stockCode` 는 **달지 않는다**. 예외적으로 한 회사만 다루는 글일 때만 `stockCode`. `audit_seo.py` 가 주제글의 stockCode 를 오배선으로 경고한다. 회사 심층 하드게이트(`auditBlog.py --gate`의 14,000자·실사 사진·`brief.json`)는 `tech-story`에 적용되지 않는다(`DEEP_GENRE_CATEGORIES` 밖). 대신 기술이야기 자체 체크: (a) 원리 해부 섹션 ≥ 1 (b) 재무 착지(dartlab 실측 표) ≥ 1 (c) "이렇게 오해하면 안 된다" 섹션 (d) SVG ≥ 4 (e) 기술 성숙도·출처 명시 (f) `audit_seo.py` 95 이상.
6. **길이 = 밀도 우선.** 회사편 20,000자가 아니다. 원리도해·재무 실측표·재현 코드로 근거를 채운 **6,000~12,000자**. 패딩 금지.
7. **썸네일 = 통합 생성기.** `gen_blog_thumbnails.py`(SSOT, frontmatter 구동)를 쓴다. kicker 라벨은 `PREFIX["tech-story"] = "기술이야기"`. 별도 생성기를 만들지 않는다. `ogImage: /thumbnails/{slug}.webp`.

## 4. 이미지 수급 (기술이야기 오버라이드)

**Openverse 실사 우선.** 기술 장면(웨이퍼·팹 클린룸·배터리 셀·SMR 모듈·로봇 팔 등)을 Openverse에서 라이선스 깨끗한 실사로 먼저 수급한다.

**적합한 실사가 없으면 자동 생성으로 넘어가지 않는다.** 운영자에게 "이 글에 필요한 이미지 A·B·C, Openverse에서 적합본 없음"을 알리고 **수급 요청**한다. 수급 주체별 도구는 정해져 있다.

- **Claude 세션**: Openverse(실사)만 쓴다. 적합본 없으면 pending 처리 후 운영자에게 알린다. 생성 도구(FLUX 등)를 **먼저 언급·제안하지 않는다**.
- **GPT/Codex 세션**: gpt image_gen 을 쓴다.
- **FLUX**: 폐기가 기본. **운영자의 명시 지시가 있을 때만** 예외적으로 사용한다(`REPLICATE_API_TOKEN` + `gen_news_flux.py` 배선 재사용). 생성 이미지는 `CREDITS.md`에 "생성 이미지(운영자 명시 지시)"로 주체 중립 기록.

정본 = memory `feedback_image_sourcing_policy`.

- 배경: `assets/{NN}-thumbnail-bg.webp`(`gen_blog_cc0.py` PD/CC0) + `CREDITS.md`. 정본 = `blog/OPERATIONS.md` 2절 + memory `feedback_image_sourcing_policy`.

## 5. 자산

- **SVG ≥ 4** (`assets/{NN}-*.svg`): 원리 도해(공정·구조) · 세대/경쟁 지형 · 재무 흔적 추이 · 대표 기업 비교. 다크 배경, 한글 타이틀, amber 강조.

## 6. 발행

`audit_seo.py` 95 이상 -> `gen_blog_thumbnails.py --slugs {slug} --apply` -> 커밋. `TOPIC_ROADMAP.md` 갱신. subject `kind: tech`(topicSlug 기반, `OPERATIONS.md` 5절). 데이터·산출물은 런타임 SSOT 직독(굽지 않음).

---
정본: 뼈대 [BLOG.md](../BLOG.md)·[PIPELINE.md](../PIPELINE.md), 마스터라이터 [_reference/BLOG_MASTER_WRITER.md](../_reference/BLOG_MASTER_WRITER.md), 운영 라우팅 [OPERATIONS.md](../OPERATIONS.md), 이미지 수급 memory `feedback_image_sourcing_policy`.
