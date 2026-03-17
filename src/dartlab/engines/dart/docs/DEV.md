# DART Docs Sections Development Guide

# DART Docs Development Guide

상세 문서:
- `src/dartlab/engines/dart/docs/dev/sections.md`
- `src/dartlab/engines/dart/docs/dev/learning.md`

핵심 원칙:
- `sections`가 docs source of truth다.
- markdown/table 경계를 버리지 않는다.
- 같은 topic 안의 원문 block 순서를 `blockOrder`로 보존한다.
- 셀에는 요약이 아니라 해당 기간의 원문 payload를 유지한다.
- table-heavy topic은 `sections`에서 다시 추출한다.
- 기존 docs 개별 parser는 archive/legacy fallback로 남긴다.
