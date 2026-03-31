# 105: Filing Semantic Map — 실험 완료

## 최종 결과

| 방법 | precision@5 | cold start | 평균속도 | 의존성 |
|------|:---:|:---:|:---:|------|
| **BM25(substring)** | **71%** | **0ms** | **14ms** | 없음 (Polars) |
| SemanticMap | 68% | 0ms | 25ms | 없음 |
| Model2Vec(DART증류) | 67% | 265ms | 39ms | model2vec 24.7MB |
| Hybrid(SM+M2V) | 60% | 265ms | 39ms | model2vec |
| 임베딩(ko-sroberta) | **83%** | 12,700ms | 58ms | PyTorch 2GB |

## 핵심 발견

1. **cold start 0ms 달성** — 모델 없이 검색 가능 확인
2. **BM25가 가장 실용적** — DART 공시는 정형화된 키워드를 이미 포함, 71% precision
3. **SemanticMap 동의어 확장은 노이즈 유발** — 키워드 확장이 때로는 정밀도 하락
4. **Model2Vec 증류 성공** — ko-sroberta → 24.7MB DART 특화 모델, 15.7초 증류, 265ms cold start
5. **하이브리드는 오히려 하락** — SemanticMap + Model2Vec 합산 시 60%로 최저
6. **임베딩은 여전히 최고 품질** — 83%로 15%p 차이, 특히 의미 검색에서 강함

## 실험별 상세

| # | 실험 | 결과 |
|---|------|------|
| 001 | Taxonomy 자동 분류 | 75% 자동 분류 (144/193) |
| 002 | 동반 공시 그래프 | PMI 기반 연관 쌍 140개, 절차/인과 구분 |
| 003 | 섹션 의미 맵 | 72% 자동 분류 (200/278), 14개 클러스터 |
| 004 | 통합 검색 | cold start 0ms, precision 68% |
| 005 | 3방식 벤치마크 | BM25 71% > SemanticMap 68% |
| 006 | Model2Vec 증류 | 24.7MB, 265ms cold, 67% precision |

## 결론

- **BM25 단독이 최선의 비임베딩 방법** — 71%, 0ms, 의존성 0
- SemanticMap/Model2Vec은 BM25를 초과하지 못함
- **임베딩과 15%p 차이는 의미 검색 능력**에서 발생
- 실용적 선택: **BM25 기본 + 임베딩 옵션** (vector 의존성 있으면 83%, 없으면 71%)

## 부산물

- DART 공시 Taxonomy: 15개 카테고리, 자동 구축
- 동반 공시 PMI 그래프: 기업 이벤트 인과 추론 가능
- DART 특화 Model2Vec 모델: 24.7MB, 265ms cold start
