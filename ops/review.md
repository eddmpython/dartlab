# Review

analysis 결과와 credit 블록을 블록-템플릿으로 조립한 6막 서사 보고서.
analysis/credit 품질이 올라가면 review 품질도 올라간다.

| 항목 | 내용 |
|------|------|
| 레이어 | L2 |
| 진입점 | `c.review()`, `c.reviewer()` |
| 소비 | analysis + credit (블록식 조합) |
| 생산 | ai(reviewer), 사용자(터미널/HTML/마크다운/JSON) |
| 출력 | rich, html, markdown, json |

## 단일 진입점

- **`c.review()` / `c.reviewer()`** 로 접근한다 (Company-bound)
- review는 analysis 결과와 credit 블록을 소비하여 보고서로 조립한다

## API

```python
c.review()              # 전체 보고서
c.review("수익구조")     # 단일 섹션
c.reviewer()            # review + AI 종합의견
c.reviewer(guide="반도체 사이클 관점에서 평가해줘")
```

4개 출력 형식: `rich`(터미널), `html`, `markdown`, `json`

## 아키텍처

```
catalog.py          단일 진실의 원천 (블록 메타 + 섹션 메타 + 순서)
  ├── templates.py  섹션별 설정 (visibleKeys, helper, aiGuide)
  ├── builders.py   analysis calc* → Block 리스트 변환
  ├── registry.py   buildBlocks() / buildReview() 조립
  │     └── blockMap.py  BlockMap — 사용자 친화 블록 사전
  ├── renderer.py   Rich 콘솔 렌더링
  ├── formats.py    HTML / Markdown / JSON 렌더링
  ├── blocks.py     Block 타입 (Heading, Table, Text, Flag, Metric)
  └── section.py    Section dataclass
```

## catalog.py — 단일 진실의 원천

- `_BLOCKS` 리스트 = 블록 정의 + 렌더링 순서
- `SECTIONS` 리스트 = 섹션 정의 + 렌더링 순서
- **key는 불변** — 한번 등록된 key는 영구 유지
- **label은 자유** — 사용자 표시명은 언제든 변경 가능
- **리스트 정의 순서 = 렌더링 순서** (list로 순서 보장)
- catalog label 하나 바꾸면 전체 렌더링이 따라간다
- builders.py에 하드코딩된 HeadingBlock title은 **0개**

## BlockMap — 사용자 친화 블록 사전

```python
b = c.blocks()
b["매출 성장률"]      # 한글 label
b["growth"]          # 영문 key
b.growth             # attribute (tab-complete)
b                    # 섹션별 카탈로그 테이블
```

오타 시 `KeyError: 'grwth' — 혹시: growth?`

## 블록 추가 절차

1. `catalog.py`: `_BLOCKS`에 BlockMeta 추가
2. `builders.py`: builder 함수 작성, `_meta(key).label`로 title
3. `registry.py`: `buildBlocks()` 안에 추가
4. `templates.py`: 섹션의 `visibleKeys`에 key 추가

**라벨 변경**: catalog.py label만 변경. 끝. 전부 자동 반영.
**순서 변경**: catalog.py _BLOCKS 위치만 이동. 끝.

## 품질 검증

- 빈 섹션, 중복 표시, 극단값 비율(수만%), 맥락 없는 경고 체크
- 공개 샘플: `docs/samples/{종목코드}.md` (10개)
- `grep -n 'HeadingBlock("' src/dartlab/review/builders.py` → 0건이어야 함

## 관련 코드

- `src/dartlab/review/` — 전체 패키지
