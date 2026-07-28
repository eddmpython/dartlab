"""capability 계약 조각을 하나로 합치는 merge primitive SSOT.

라우트 하나에 계약이 여럿 붙으면 requiredEvidence 나 artifactPolicy 같은 필드를 합쳐야
한다. 그 합치는 규칙을 분석 그래프 컴파일러(`analysisGraph`)와 카탈로그 빌더(`builder`)가
같은 본문으로 각자 갖고 있었다. 두 곳이 같은 계약을 읽어 서로 다른 그래프를 내면 카탈로그와
그래프가 어긋난다.

합치기 규약:
- 목록은 순서를 보존한 중복 제거다. 정렬하지 않는 이유는 계약에 적힌 근거 순서가 곧
  제시 순서라서다. 빈 문자열은 버린다.
- 매핑은 얕은 갱신이다. 나중에 온 계약이 이긴다. 중첩 dict 를 재귀 병합하지 않는 이유는
  정책 dict 가 통째로 하나의 결정이라, 반쯤 섞이면 어느 계약의 정책도 아닌 것이 나오기
  때문이다.
"""

from __future__ import annotations

from typing import Any


def _unique(values: Any) -> list[str]:
    """문자열로 좁힌 뒤 순서를 보존해 중복을 지운다. 빈 문자열은 버린다."""
    out: list[str] = []
    for value in values:
        text = str(value)
        if text and text not in out:
            out.append(text)
    return out


def _mergeDicts(values: Any) -> dict[str, Any]:
    """dict 만 골라 앞에서 뒤로 얕게 덮어쓴다. dict 가 아닌 것은 건너뛴다."""
    out: dict[str, Any] = {}
    for value in values:
        if isinstance(value, dict):
            out.update(value)
    return out
