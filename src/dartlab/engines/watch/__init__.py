"""공시 변화 감지 엔진 — sections diff 기반 자동 스캔 + 중요도 스코어링.

sections 수평화 위에 구축된 변화 감지 시스템.
Bloomberg에 없는 기능: 서술형 공시 텍스트의 자동 변화 추적.

사용법::

    import dartlab

    # 단일 기업
    c = dartlab.Company("005930")
    c.watch()                       # 전체 topic 변화 요약 (중요도 순)
    c.watch("riskManagement")       # 특정 topic 상세

    # 시장 다이제스트
    dartlab.digest()                # 전체 시장 TOP 변화
    dartlab.digest(sector="반도체")  # 섹터별
"""

from dartlab.engines.watch.digest import build_digest
from dartlab.engines.watch.scanner import scan_company, scan_market
from dartlab.engines.watch.scorer import score_changes

__all__ = ["scan_company", "scan_market", "score_changes", "build_digest"]
