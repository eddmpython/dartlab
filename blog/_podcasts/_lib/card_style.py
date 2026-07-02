"""카드 시각 언어 상수 (파이썬 미러).

정본(시각 SSOT)은 프론트다. 이 파일은 팟캐스트 스틸 렌더가 카드와 같은 룩을 내도록
그 값을 파이썬으로 포팅한 미러다. 값이 바뀌면 여기도 동기화한다.
  - 팔레트: landing/src/lib/cards/theme.ts 의 CARD
  - 편집 카드 그레이스케일 필터: landing/src/lib/cards/CardSlide.svelte 의 .pm-editorial .bg
드리프트 가드: tests 에서 이 상수들이 위 정본값과 일치하는지 검사한다.
"""

from __future__ import annotations

import re

# theme.ts CARD 팔레트 (hex -> RGB)
ACCENT_RGB = (255, 63, 111)  # CARD.accent #ff3f6f (rose, 한 구절 강조)
INK_RGB = (246, 248, 251)  # CARD.text #f6f8fb (본문 흰색)
MUTED_RGB = (216, 226, 240)  # CARD.textMuted #d8e2f0 (부제)
DIM_RGB = (154, 163, 173)  # CARD.textDim #9aa3ad (풋터)
BG_RGB = (5, 8, 17)  # CARD.bgDark #050811 (scrim 베이스)

# CardSlide .pm-editorial .bg filter: grayscale(0.82) contrast(1.04) brightness(1.04)
GRAYSCALE = 0.82
CONTRAST = 1.04
BRIGHTNESS = 1.04


def accent_parts(text: str) -> list[tuple[str, bool]]:
    """theme.ts accentParts 포팅: `[[구절]]` 을 (text, accent) 토막으로 쪼갠다."""
    out: list[tuple[str, bool]] = []
    for part in re.split(r"(\[\[[^\]]+\]\])", str(text or "")):
        if part == "":
            continue
        match = re.match(r"^\[\[([^\]]+)\]\]$", part)
        out.append((match.group(1), True) if match else (part, False))
    return out
