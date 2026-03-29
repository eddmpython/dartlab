"""하위호환 re-export -- 실제 구현은 core/finance/fmt.py."""

from dartlab.core.finance.fmt import fmtBig, fmtPrice, fmtUnit

__all__ = ["fmtBig", "fmtPrice", "fmtUnit"]
