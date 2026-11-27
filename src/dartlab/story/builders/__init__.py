"""story 블록 빌더 — 도메인별 분해 (debt-honesty P3-3). 옛 builders.py 6,111줄 god-file → 도메인
모듈. 외부 호출계약 `from dartlab.story.builders import X` 는 본 __init__ 재export 로 보존.
"""

from __future__ import annotations

# _shared = 공유 imports·모듈상수(_storyCurrency 등)·헬퍼(_fmtAmtShort·_extractSeries·_flagsBlock·
# _timelineTable 등). 외부가 `from dartlab.story.builders import _helper` 로 쓰던 계약 보존
# (registry·narrative 등). __all__ 이 _ 이름까지 명시해 * 재export 됨.
from dartlab.story.builders._shared import *  # noqa: F401,F403
from dartlab.story.builders.asset import *  # noqa: F401,F403
from dartlab.story.builders.capital import *  # noqa: F401,F403
from dartlab.story.builders.cashflow import *  # noqa: F401,F403
from dartlab.story.builders.credit import *  # noqa: F401,F403
from dartlab.story.builders.filing import *  # noqa: F401,F403
from dartlab.story.builders.forecast import *  # noqa: F401,F403
from dartlab.story.builders.governance import *  # noqa: F401,F403
from dartlab.story.builders.macro import *  # noqa: F401,F403
from dartlab.story.builders.market import *  # noqa: F401,F403
from dartlab.story.builders.peer import *  # noqa: F401,F403
from dartlab.story.builders.profitability import *  # noqa: F401,F403
from dartlab.story.builders.quality import *  # noqa: F401,F403
from dartlab.story.builders.revenue import *  # noqa: F401,F403
from dartlab.story.builders.story import *  # noqa: F401,F403
from dartlab.story.builders.valuation import *  # noqa: F401,F403
