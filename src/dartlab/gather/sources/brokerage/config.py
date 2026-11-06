"""증권사 리서치 보드 레지스트리 — 관리 SSOT.

증권사 추가·수정·중단은 이 dict 한 곳만 건든다 (url + 메커니즘 + 카테고리 + enabled).
mechanism: htmlTable(서버렌더 표) · htmlList(서버렌더 ul>li) · spaAjax(JS 셸 — deferred).
categories: {reportType 라벨 → 보드 URL} — 카테고리가 곧 리포트 구분(reportType).
enabled=False = browser 자동화 필요로 deferred (note 참조).
"""

from __future__ import annotations

_MIRAE = "https://securities.miraeasset.com/bbs/board/message/list.do?categoryId="
_NH = "https://m.nhqv.com/research/boardList?rshPprDitCd="
_YUANTA = "https://www.myasset.com/myasset/research/rs_list/rs_list.cmd?cd006=&cd008=&cd007="
_HANYANG = "https://www.hygood.co.kr/board/"
_BOOKOOK = "https://www.bookook.co.kr/research/"

BROKERS: dict[str, dict] = {
    # --- 서버렌더 = 작동 ---
    "miraeasset": {
        "name": "미래에셋",
        "mechanism": "htmlTable",
        "enc": "cp949",
        "enabled": True,
        "categories": {
            "기업분석": _MIRAE + "1800",
            "산업분석": _MIRAE + "1525",
            "투자전략": _MIRAE + "1527",
        },
    },
    "nh": {
        "name": "NH투자",
        "mechanism": "htmlList",
        "enc": None,
        "enabled": True,
        "dynamicReportType": True,  # report_type 을 행별 p.sort(ETF·전략·기업…)로 재라벨 → 헬스 카테고리별 검사 제외(총량만)
        "categories": {
            "기업분석": _NH + "01",
            "시황전략": _NH + "02",
        },
    },
    "yuanta": {
        "name": "유안타",
        "mechanism": "htmlTable",
        "enc": None,
        "enabled": True,
        "categories": {
            "투자전략": _YUANTA + "RB30",
        },
        "note": "메타 작동, 링크는 onclick 역추출 미완 → 카테고리 URL fallback",
    },
    "hanyang": {
        "name": "한양",
        "mechanism": "htmlTable",
        "enc": None,
        "enabled": True,
        "categories": {
            "기업분석": _HANYANG + "00000000-0000-0000-0000-000009000001",
            "이슈분석": _HANYANG + "00000000-0000-0000-0000-000009000002",
            "채권분석": _HANYANG + "00000000-0000-0000-0000-000009000003",
            "시황": _HANYANG + "00000000-0000-0000-0000-000009000004",
        },
        "note": "서버렌더 표(2026-11 개편, Next.js), 제목은 링크 없는 버튼이라 글 주소는 같은 페이지 서버 데이터의 글 번호로 만든다. 제목에 종목코드 내장·PDF 는 한양 자기 서버(hygood.co.kr) 링크아웃",
    },
    "bookook": {
        "name": "부국",
        "mechanism": "htmlTable",
        "enc": "cp949",
        "enabled": True,
        "categories": {
            "기업분석": _BOOKOOK + "research_5",
            "시황": _BOOKOOK + "research_1",
        },
        "note": "서버렌더 표(cp949). per-report 링크 부재(detail=in-page 펼침·PDF=POST /file/download) → 보드 URL fallback(유안타 동형). 제목에 종목코드 내장",
    },
    # --- SPA/AJAX = deferred (초기 HTML 에 데이터·엔드포인트 없음 → browser 자동화 필요) ---
    # 빅 증권사 SPA 는 단순 셸+AJAX 가 아니라 안티봇 게이트라 무브라우저 직호출 불가:
    #   kiwoom = EverSafe(eversafeThreat/CD-14000) JS 토큰, hana = FNN client secret/세션.
    # 네이버 금융 리서치 목록은 서버렌더(33사 전부)지만 PDF 가 100% 네이버 CDN(stock.pstatic.net)
    # 호스팅 = DB권+무단재배포 회색이라 채택 안 함(각 증권사 자체 보드만 인덱싱).
    "koreainvestment": {
        "name": "한국투자",
        "mechanism": "spaAjax",
        "enc": None,
        "enabled": False,
        "categories": {"전체": "https://securities.koreainvestment.com/main/research/Main.jsp"},
        "note": "엔드포인트가 외부 JS 번들에 있음",
    },
    "kb": {
        "name": "KB증권",
        "mechanism": "spaAjax",
        "enc": None,
        "enabled": False,
        "categories": {"전체": "https://rc.kbsec.com/"},
        "note": "SPA 셸",
    },
    "kiwoom": {
        "name": "키움",
        "mechanism": "spaAjax",
        "enc": None,
        "enabled": False,
        "categories": {"전체": "https://www.kiwoom.com/h/invest/research/VAnalCRView"},
        "note": "AJAX 로드, 엔드포인트 외부 JS",
    },
    "hana": {
        "name": "하나",
        "mechanism": "spaAjax",
        "enc": None,
        "enabled": False,
        "categories": {"전체": "https://www.hanaw.com/main/research/researchReform/RC_000100_T1.cmd"},
        "note": "AJAX 로드 (필터 셸만 서버렌더)",
    },
}


def enabledBrokers() -> dict[str, dict]:
    """enabled=True 증권사만 추린 dict 반환 (deferred SPA 제외).

    Args:
        없음.

    Returns:
        dict[str, dict] — broker key → 설정 dict (enabled 인 것만).

    Raises:
        없음 — 빈 dict 도 정상 반환.

    Requires:
        모듈 상수 ``BROKERS`` (관리 SSOT).

    Example::

        from dartlab.gather.sources.brokerage.config import enabledBrokers
        list(enabledBrokers())   # ['miraeasset', 'nh', 'yuanta', 'hanyang', 'bookook']
    """
    return {k: v for k, v in BROKERS.items() if v.get("enabled")}
