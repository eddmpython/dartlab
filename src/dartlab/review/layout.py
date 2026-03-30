"""review 레이아웃 설정."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReviewLayout:
    """리뷰 렌더링 레이아웃 설정."""

    # 들여쓰기 (칸)
    indentH1: int = 0  # 대제목
    indentH2: int = 3  # 중제목
    indentBody: int = 6  # 콘텐츠 (텍스트, 지표, 테이블, 플래그)

    # 간격 (빈 줄 수)
    gapAfterH1: int = 1  # 대제목 아래
    gapAfterH2: int = 1  # 중제목 아래
    gapBetween: int = 2  # 섹션 간 구분 (중제목 앞)

    # 구분선
    separatorWidth: int = 56

    # 섹션 순서 (None이면 레지스트리 등록 순서 그대로)
    sectionOrder: list[str] | None = None

    # 섹션 헬퍼 텍스트 표시 여부
    helper: bool = True

    # detail 모드: True면 전체 블록, False면 summary만 표시
    detail: bool = True


DEFAULT_LAYOUT = ReviewLayout()
