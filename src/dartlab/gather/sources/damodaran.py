"""Damodaran 국가 ERP(equity risk premium) 외부 fetch — pages.stern.nyu.edu/~adamodar.

``ctryprem.html``(국가별 Moody's rating + adj default spread + total ERP) 다운로드·파싱 →
구조화 dict. 외부 fetch = gather(Extract) SSOT 라 본 모듈에 둔다 — ISO2 매핑 + reference/data/
damodaranDefaults.json 병합·쓰기(sink)는 호출자(.github/scripts/sync/updateDamodaranERP)
책임. Damodaran 연 2회(1·7월) 갱신.
"""

from __future__ import annotations

import logging
import re
import urllib.request

from ..types import SourceUnavailableError

log = logging.getLogger(__name__)

DAMODARAN_ERP_URL = "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html"


def _fetchHtml(timeout: float = 30.0) -> str:
    """Damodaran ctryprem.html 원문 다운로드 (인코딩 자동 감지)."""
    try:
        req = urllib.request.Request(DAMODARAN_ERP_URL, headers={"User-Agent": "dartlab/1.0 (research)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — 고정 https 도메인
            raw = resp.read()
            for enc in ("utf-8", "windows-1252", "latin-1"):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw.decode("utf-8", errors="replace")
    except (OSError, ValueError) as exc:
        raise SourceUnavailableError("Damodaran ERP 원문을 가져올 수 없습니다") from exc


def _extractMatureMarketERP(html: str) -> float | None:
    """Mature market equity risk premium (US base) 추출 — 'mature market ... N.NN%' 패턴."""
    m = re.search(r"mature\s+market[^.]*?(\d+\.\d+)\s*%", html, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def _extractCountries(html: str) -> dict[str, dict]:
    """국가 테이블 파싱 (관대한 tr/td regex — 표 형태 변화 대응).

    표준 컬럼: Country | Rating | Adj Default Spread | Total ERP | Country Risk Premium.
    각 행은 ``{name: {"rawNumbers": [float, ...]}}`` — 컬럼 순서 해석은 호출자(sink).
    """
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL | re.IGNORECASE)
    out: dict[str, dict] = {}
    for row in rows:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL | re.IGNORECASE)
        if len(cells) < 4:
            continue
        clean = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
        name = clean[0]
        if not name or len(name) > 50:
            continue
        nums: list[float] = []
        for c in clean[1:]:
            m = re.search(r"(\d+\.\d+)\s*%?", c)
            if m:
                try:
                    nums.append(float(m.group(1)))
                except ValueError:
                    pass
        if len(nums) < 2:
            continue
        out[name] = {"rawNumbers": nums}
    return out


def getDamodaranCountryErp(*, timeout: float = 30.0) -> dict:
    """Damodaran ctryprem.html → 구조화 국가 ERP dict. 외부 fetch=gather SSOT.

    Capabilities: Damodaran 국가 ERP 페이지 다운로드 + mature market ERP·국가별 raw 숫자 파싱 → dict.
    AIContext: internal source fetch — AI 직접 호출 X. reference/damodaranDefaults.json 갱신 sink 가 소비.
    Guide: 결과의 컬럼 순서 해석(total ERP·CRP)·ISO2 매핑은 호출자(sink) 책임 — 본 함수는 fetch+파싱만.
    When: damodaranDefaults.json 월간 갱신(updateDamodaranERP) 등 Damodaran ERP 원천 수집 시.
    How: _fetchHtml → _extractMatureMarketERP + _extractCountries 조합 → dict 반환.

    Args:
        timeout: HTTP 타임아웃(초).

    Returns:
        ``{"matureMarketERP": float, "countries": {name: {"rawNumbers": [float]}}}``.

    Raises:
        SourceUnavailableError: 네트워크, 디코드 또는 페이지 schema 실패.

    Example:
        >>> out = getDamodaranCountryErp()  # doctest: +SKIP
        >>> set(out) >= {"matureMarketERP", "countries"}  # doctest: +SKIP
        True

    Requires:
        네트워크 (``pages.stern.nyu.edu/~adamodar`` ctryprem.html). stdlib(urllib·re) 만.

    SeeAlso:
        _extractMatureMarketERP · _extractCountries : 파싱 하위 단계.
        .github/scripts/sync/updateDamodaranERP : 본 fetch 를 위임 호출하는 sink.
    """
    html = _fetchHtml(timeout=timeout)
    matureMarketErp = _extractMatureMarketERP(html)
    countries = _extractCountries(html)
    if matureMarketErp is None or not countries:
        raise SourceUnavailableError("Damodaran ERP 페이지 schema를 해석할 수 없습니다")
    return {
        "matureMarketERP": matureMarketErp,
        "countries": countries,
    }
