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

from dartlab.scan.watch.digest import build_digest
from dartlab.scan.watch.scanner import scan_company, scan_market
from dartlab.scan.watch.scorer import score_changes


def scanDigest(*, format: str = "dataframe", top_n: int = 30, **kwargs) -> object:
    """시장 전체 공시 변화 다이제스트 (scan_market + build_digest 래핑)."""
    df = scan_market(top_n=top_n, **kwargs)
    return build_digest(df, format=format, top_n=top_n)


__all__ = ["scan_company", "scan_market", "score_changes", "build_digest", "scanDigest"]
