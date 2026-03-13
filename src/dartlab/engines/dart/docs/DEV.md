# DART Docs Sections Development Guide

# DART Docs Development Guide

상세 문서:
- `src/dartlab/engines/dart/docs/dev/sections.md`
- `src/dartlab/engines/dart/docs/dev/learning.md`

핵심 원칙:
- `sections`가 docs source of truth다.
- markdown/table 경계를 버리지 않는다.
- table-heavy topic은 `sections`에서 다시 추출한다.
- 기존 docs 개별 parser는 archive/legacy fallback로 남긴다.
