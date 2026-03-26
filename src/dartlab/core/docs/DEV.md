# common/docs — 문서 공통 유틸

## 구조

```
common/docs/
├── diff.py         # sections 기간간 변화 감지 (hash + difflib)
├── bridge.py       # topic → metadata 브릿지
└── topicGraph.py   # topic 간 의존성 그래프
```

## diff.py — 공시 변화 감지

DART/EDGAR 공통으로 사용하는 기간간 텍스트 diff 엔진.

- **hash 기반 1차 감지**: 기간별 sections 셀 해시 비교 → 변경 여부 판단
- **difflib 2차 상세**: 변경된 셀만 줄 단위 세부 diff 생성
- **출력**: topic × period 변화 매트릭스 (변화율, 추가/삭제/수정 분류)

## bridge.py — docs 통합 헬퍼

topic 메타데이터(chapter, blockType, source) 조회 및 sections 간 브릿지.

## topicGraph.py — topic 관계 그래프

topic 간 의존성/연관 관계를 그래프로 표현. insight/watch 등에서 소비.

## 소비자

- `analysis/watch/` — diff 결과를 중요도 스코어링에 사용
- `ai/context/` — diff 변화율을 LLM 컨텍스트에 포함
- `common/finance/prediction.py` — diff_change_rate를 시나리오 확률 재가중에 사용
