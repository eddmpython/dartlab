# 이슈 관리

GitHub Issue → 수정 → 테스트 → 커밋의 추적 체계.

## 원칙

**별도 이슈 폴더/문서를 만들지 않는다.** 기존 인프라 3개가 역할 분담한다:

| 역할 | 어디에 | 예시 |
|------|--------|------|
| 원인 분석 + 논의 | **GitHub Issue** | `gh issue view 15` |
| 재발 방지 | **기능별 테스트 파일** | `test_select.py` 안에 regression 케이스 |
| 코드 변경 이유 | **커밋 메시지** | `fix: select 세전이익 매핑 오류 (#15)` |

## 연결 구조

```
테스트 docstring: """Regression for #15."""
        │
        ▼
커밋 메시지: fix: ... (#15)
        │
        ▼
GitHub Issue #15: 근본 원인, 재현 코드, 논의 전부
```

역추적: 테스트 깨짐 → docstring에서 `#15` 발견 → Issue에서 원인 확인 → `git log --grep="#15"`로 수정 코드 확인.

## 이슈 수정 절차

1. **재현**: 로컬에서 버그 재현 (수동 실행)
2. **원인 분석**: 코드 추적, 근본 원인 파악
3. **테스트 작성**: 기능별 테스트 파일에 regression 케이스 추가
   - docstring에 `Regression for #N` 표기
   - 수정 전 FAIL 확인
4. **수정**: 코드 수정
   - 수정 후 PASS 확인
5. **커밋**: `fix: 설명 (#N)` 형식
   - GitHub이 자동으로 Issue에 커밋 링크 연결
6. **Issue 답변**: 원인 + 해결 요약, `Fixes #N`으로 자동 닫기

## 테스트 위치

이슈별 파일을 만들지 않는다. 기능별 테스트 파일에 통합:

```
tests/
├── test_select.py       ← select 관련 이슈 (#14, #15)
├── test_company.py      ← Company 관련 이슈
├── test_analysis.py     ← analysis 관련 이슈
└── ...
```

## 금지

- `tests/issues/` 폴더 생성 금지 — 파일 무한 증식
- 이슈별 마크다운 문서 생성 금지 — GitHub Issue가 이미 추적
- 이슈 번호 없는 regression 테스트 금지 — 나중에 왜 있는지 모름
