"""이사의 경영진단 및 분석의견(MD&A) 분석 모듈."""

from dartlab.finance.mdna.pipeline import mdna
from dartlab.finance.mdna.types import MdnaSection, MdnaResult

__all__ = ["mdna", "MdnaSection", "MdnaResult"]
