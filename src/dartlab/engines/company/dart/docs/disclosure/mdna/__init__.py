"""이사의 경영진단 및 분석의견(MD&A) 분석 모듈."""

from dartlab.engines.company.dart.docs.disclosure.mdna.pipeline import mdna
from dartlab.engines.company.dart.docs.disclosure.mdna.types import MdnaResult, MdnaSection

__all__ = ["mdna", "MdnaSection", "MdnaResult"]
