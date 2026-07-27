"""DART OpenAPI 임원거래 + 대량보유 — gather/types 변환.

이전 위치: gather/domains/dartApi.py (gather → providers cycle 의 한 축).
새 위치: providers/dart 안 — DART OpenAPI 호출 자체는 provider 책임. gather 는
provider 의 결과를 gather.types schema 로 받아쓸 뿐 (gather → providers 단방향).

이 파일은 providers/dart 내부에서 DART OpenAPI Dart 클라이언트 사용 + gather.types
schema (InsiderTrade/MajorHolder) 로 변환. gather/domains/dartApi.py 의 본체.
"""

from __future__ import annotations

import asyncio
import logging

from dartlab.core.polarsUtil import isEmptyDf

log = logging.getLogger(__name__)


# 자체 raw dataclass — providers/dart 가 gather.types 의존 없이 dict 반환.
# gather/insider.py 가 dict → gather.types.InsiderTrade/MajorHolder 변환 책임.
# (cycle 회피: providers → gather 의존 0, gather → providers 단방향만.)


def _getDart():
    """Dart OpenAPI 클라이언트 lazy 생성. API 키 미설정 시 None."""
    try:
        from dartlab.core.dartClient import dartCollector

        return dartCollector()
    except (ImportError, ValueError, OSError) as exc:
        log.debug("DART API 사용 불가: %s", exc)
        return None


async def fetchInsiderTradingRaw(stockCode: str, *, limit: int | None = None) -> list[dict]:
    """임원/주요주주 주식 거래 내역 raw dict — DART elestock.json.

    Capabilities:
        - DART OpenAPI elestock (임원·주요주주 특정증권등 소유상황보고) 호출.
        - 응답 row 를 표준화된 dict (date/name/position/tradeType/changeShares/afterShares
          /reason/source) 로 정규화. gather.types 의존성 없이 raw dict 만 반환 (cycle 회피).
        - DART API key 미설정 또는 호출 실패 시 silent — 빈 list 반환 + log.warning.

    Args:
        stockCode: 종목코드 (6 자리, 예 "005930").
        limit: 최대 행 수 상한 (룰 8). None 이면 무제한. 분석 용도면 20~100 권장.

    Returns:
        list[dict] — 각 거래 dict 의 표준 key: ``date`` (rcept_dt, 접수일) ·
        ``name`` (보고자) · ``position`` (직책 ofcps) · ``tradeType`` (장내/장외 거래 구분)
        · ``changeShares`` (변동 주식수) · ``afterShares`` (변동 후 보유) · ``reason``
        (변동 사유 ctr_motive) · ``source`` ("dart"). API key 부재 또는 빈 응답 시 ``[]``.

    Example:
        >>> import asyncio
        >>> # DART API key 가 설정된 환경에서:
        >>> # rows = asyncio.run(fetchInsiderTradingRaw("005930", limit=20))
        >>> # rows[0].keys()
        >>> # dict_keys(['date', 'name', 'position', 'tradeType', 'changeShares', 'afterShares', 'reason', 'source'])

    Guide:
        - "삼성전자 임원 거래" → ``await fetchInsiderTradingRaw("005930", limit=20)``
        - streaming pair 필요 시 ``iterInsiderTradingRaw`` (룰 10).
        - gather pipeline 안에서는 ``gather/insider.py`` 가 결과 dict → ``InsiderTrade``
          dataclass 변환 후 사용.

    SeeAlso:
        - ``iterInsiderTradingRaw`` — async iterator pair (룰 10).
        - ``fetchMajorShareholdersRaw`` — 5% 이상 대량보유 별도 endpoint.
        - ``dartlab.gather.dart.dart.Dart.executiveShares`` — 본 함수가 호출하는 raw client.

    Requires:
        - DART OpenAPI API key (환경변수 또는 ``dartKey`` registry).
        - polars — ``Dart.executiveShares`` 가 DataFrame 반환, ``iter_rows(named=True)`` 사용.
        - 네트워크 — opendart.fss.or.kr 도메인 접근.

    AIContext:
        Ask Workbench 의 "내부자 거래" / "임원 매매" 토픽 추론 시 호출. API key 부재 환경
        (test fixture / pyodide) 에서는 빈 list 반환이므로 caller 는 evidence 부재 메시지
        준비. 결과 dict 의 ``date`` 는 str (rcept_dt 8자리) — caller 가 date 객체 변환 필요.

    LLM Specifications:
        AntiPatterns:
            - 본 함수를 동기 컨텍스트에서 호출 → coroutine 미실행. 반드시 ``await``.
            - 무제한 limit (limit=None) 으로 분석 파이프라인에서 호출 → 룰 8 위반.
              분석 용 호출은 명시 limit 권장.
            - API key 부재 환경에서 결과 empty 를 "거래 0 건" 으로 해석 금지 — log
              메시지로 키 부재 확인.
        OutputSchema:
            - row: 거래 1 건.
            - column: 8 key dict (위 Returns 명시).
            - 정렬: DART 응답 순서 (보통 접수일 역순).
        Prerequisites:
            - ``DART_API_KEY`` 환경변수 또는 ``CredentialProvider`` 에 등록된 키.
            - 종목이 elestock 보고 의무 (상장 + 임원 보유) 회사여야 결과 존재.
        Freshness:
            - DART OpenAPI 실시간 — 임원 거래 발생 후 보통 5 영업일 이내 접수.
            - 본 함수는 cache 없음 — 호출자가 caching 책임.
        Dataflow:
            - ``Dart.executiveShares`` (OpenAPI) → 본 함수 정규화 → caller (gather/insider).
        TargetMarkets:
            - KR (DART). 미국 Form 4 은 ``providers/edgar/disclosure/form4`` (P-PR7).

    Raises:
        없음.
    """
    dart = _getDart()
    if dart is None:
        return []
    try:
        df = await asyncio.to_thread(dart.executiveShares, stockCode)
        if isEmptyDf(df):
            return []
        result: list[dict] = []
        for row in df.iter_rows(named=True):
            result.append(
                # 필드명은 DART elestock.json 실제 응답 기준이다. 예전에는 응답에 없는
                # `ofcps` 와 `ctr_motive` 를 읽어 직위와 사유가 언제나 빈 문자열이었고,
                # 소유수와 증감수를 서로 바꿔 읽어 거래 방향 자체가 뒤집혀 있었다.
                # 실측: 소유수 2,000 증감 1,000 인 행이 증감 2,000 보유 1,000 으로 나갔다.
                {
                    "date": str(row.get("rcept_dt", "")),
                    "name": str(row.get("repror", "")),
                    "position": str(row.get("isu_exctv_ofcps", "")),
                    # 거래 유형은 응답에 별도 필드가 없다. 증감 부호가 그 자체로 취득과
                    # 처분을 가르므로 파생한다. 없는 필드를 읽어 빈 문자열을 내보내는
                    # 것보다 있는 자료로 답하는 쪽이 맞다.
                    "tradeType": _tradeTypeOf(_safeInt(row.get("sp_stock_lmp_irds_cnt", 0))),
                    "changeShares": _safeInt(row.get("sp_stock_lmp_irds_cnt", 0)),
                    "afterShares": _safeInt(row.get("sp_stock_lmp_cnt", 0)),
                    # 사유 필드는 elestock 응답에 없다. 등기 여부는 있으므로 그것을 준다.
                    "reason": str(row.get("isu_exctv_rgist_at", "")),
                    "source": "dart",
                }
            )
        if limit is not None:
            result = result[:limit]
        return result
    except (ValueError, OSError, KeyError, TypeError) as exc:
        log.warning("DART executiveShares 실패 (%s): %s", stockCode, exc)
        return []


async def fetchMajorShareholdersRaw(stockCode: str, *, limit: int | None = None) -> list[dict]:
    """5% 이상 대량보유 변동 raw dict — DART majorstock.json.

    Capabilities:
        - DART OpenAPI majorstock (대량보유 상황보고) 호출.
        - 응답 row 를 표준 dict (holderName/shares/ratio/changeDate/changeType/source) 로
          정규화. gather.types 의존성 없음 (cycle 회피).
        - 5% 이상 보유 변동 (취득/처분/기타) 사건 추적.

    Args:
        stockCode: 종목코드 (6 자리).
        limit: 최대 행 수 상한 (룰 8). None 이면 무제한.

    Returns:
        list[dict] — 각 변동 dict: ``holderName`` (보고서명 또는 보고자) · ``shares``
        (보유 주식수) · ``ratio`` (지분율 %) · ``changeDate`` (rcept_dt 접수일) ·
        ``changeType`` (change_on 변동 사유) · ``source`` ("dart"). 빈 응답 시 ``[]``.

    Example:
        >>> import asyncio
        >>> # rows = asyncio.run(fetchMajorShareholdersRaw("005930", limit=10))
        >>> # set(rows[0].keys()) >= {"holderName", "shares", "ratio"}

    Guide:
        - "삼성전자 대량보유 변동" → ``await fetchMajorShareholdersRaw("005930", limit=20)``
        - 외국인 지분 추적, M&A 시그널 탐지 — caller 가 holderName 패턴 매칭.
        - streaming pair 필요 시 ``iterMajorShareholdersRaw``.

    SeeAlso:
        - ``iterMajorShareholdersRaw`` — async iterator pair (룰 10).
        - ``fetchInsiderTradingRaw`` — 임원 거래 별도 endpoint (elestock).
        - ``dartlab.gather.dart.dart.Dart.majorShareholders``.

    Requires:
        - DART OpenAPI API key.
        - polars — DataFrame iter_rows.
        - 네트워크.

    AIContext:
        Ask Workbench 의 "지분 변동" / "외국인 보유" / "M&A" 토픽에서 호출. ratio 가
        급변하면 (예 5% → 15%) M&A 가능성 시그널. caller 가 인용 시 changeDate +
        changeType 동행 표시.

    LLM Specifications:
        AntiPatterns:
            - 비-상장사 종목코드 → 빈 list (보고 의무 없음).
            - 매우 작은 limit (1~2) 으로 trend 분석 시도 → 데이터 부족.
            - ratio 의 절대값을 "현재 지분율" 로 해석 금지 — 변동 시점 snapshot 일 뿐.
        OutputSchema:
            - row: 변동 보고 1 건.
            - column: 6 key dict (위 Returns).
            - 정렬: DART 응답 순서.
        Prerequisites:
            - ``DART_API_KEY`` 등록.
            - 종목이 5% 이상 보유자 보고 사건 발생한 회사.
        Freshness:
            - 변동 발생 후 5 영업일 이내 보고 의무 → DART 접수 즉시 반영.
        Dataflow:
            - ``Dart.majorShareholders`` (OpenAPI) → 본 함수 정규화 → caller.
        TargetMarkets:
            - KR (DART). SC 13D/G (미국) 은 ``providers/edgar`` 별도 (P-PR7+ 후속).

    Raises:
        없음.
    """
    dart = _getDart()
    if dart is None:
        return []
    try:
        df = await asyncio.to_thread(dart.majorShareholders, stockCode)
        if isEmptyDf(df):
            return []
        result: list[dict] = []
        for row in df.iter_rows(named=True):
            result.append(
                # majorstock.json 실제 응답 기준. `report_nm` 과 `change_on` 은 응답에
                # 없어서 보고자명과 보고구분이 언제나 빈 문자열이었다.
                {
                    "holderName": str(row.get("repror", "")),
                    "shares": _safeInt(row.get("stkqy", 0)),
                    "ratio": _safeFloat(row.get("stkrt", 0)),
                    "changeDate": str(row.get("rcept_dt", "")),
                    "changeType": str(row.get("report_tp", "")),
                    "source": "dart",
                }
            )
        if limit is not None:
            result = result[:limit]
        return result
    except (ValueError, OSError, KeyError, TypeError) as exc:
        log.warning("DART majorShareholders 실패 (%s): %s", stockCode, exc)
        return []


async def iterInsiderTradingRaw(stockCode: str, *, limit: int | None = None):
    """``fetchInsiderTradingRaw`` 의 async iterator pair (룰 10).

    Capabilities:
        - 임원 거래 dict 를 한 건씩 streaming yield. 메모리 효율 (rows 한꺼번에 load 안 함).
        - 룰 10 강제 (collection 반환 함수는 iterator pair 동행).
        - 내부적으로 ``fetchInsiderTradingRaw`` 호출 후 generator 변환 — 현재는 lazy 효과
          제한적 (P-PR 후속 phase 에서 true streaming 으로 전환 검토).

    Args:
        stockCode: 종목코드 (6 자리).
        limit: 최대 yield 행 수.

    Yields:
        dict — ``fetchInsiderTradingRaw`` 와 동일 schema (8 key).

    Example:
        >>> import asyncio
        >>> async def _demo():
        ...     async for row in iterInsiderTradingRaw("005930", limit=10):
        ...         print(row["name"])
        >>> # asyncio.run(_demo())

    Guide:
        - "임원 거래 한 건씩 처리" → ``async for row in iterInsiderTradingRaw(...)``.
        - 전체 list 가 필요하면 ``fetchInsiderTradingRaw`` 사용.

    SeeAlso:
        - ``fetchInsiderTradingRaw`` — list 반환 변종.
        - ``iterMajorShareholdersRaw`` — 대량보유 streaming pair.

    Requires:
        - DART OpenAPI API key.
        - 네트워크.

    AIContext:
        대량 stockCode 순회 + 거래 필터링 파이프라인에서 메모리 부담 회피용. caller 가
        조기 break 로 lazy 효과 회수 가능.

    LLM Specifications:
        AntiPatterns:
            - generator 를 list 로 즉시 캐스팅 (``list(iter...)``) → ``fetchInsiderTradingRaw``
              직접 호출이 명확.
            - async iterator 를 동기 ``for`` 로 순회 → TypeError.
        OutputSchema:
            - yield item: 8 key dict (fetchInsiderTradingRaw Returns 참조).
        Prerequisites:
            - ``DART_API_KEY`` 등록.
        Freshness:
            - 실시간 (DART 접수 즉시).
        Dataflow:
            - ``fetchInsiderTradingRaw`` 결과 list → 본 함수 yield → caller.
        TargetMarkets:
            - KR (DART).

    Raises:
        없음.
    """
    rows = await fetchInsiderTradingRaw(stockCode, limit=limit)
    for r in rows:
        yield r


async def iterMajorShareholdersRaw(stockCode: str, *, limit: int | None = None):
    """``fetchMajorShareholdersRaw`` 의 async iterator pair (룰 10).

    Capabilities:
        - 5% 이상 대량보유 변동 dict 를 streaming yield. 룰 10 강제.
        - ``fetchMajorShareholdersRaw`` 결과를 generator 로 wrap.

    Args:
        stockCode: 종목코드 (6 자리).
        limit: 최대 yield 행 수.

    Yields:
        dict — ``fetchMajorShareholdersRaw`` 와 동일 6 key schema.

    Example:
        >>> import asyncio
        >>> async def _demo():
        ...     async for row in iterMajorShareholdersRaw("005930", limit=10):
        ...         print(row["holderName"])
        >>> # asyncio.run(_demo())

    Guide:
        - "대량보유 변동 streaming" → ``async for row in iterMajorShareholdersRaw(...)``.
        - 전체 list 가 필요하면 ``fetchMajorShareholdersRaw`` 사용.

    SeeAlso:
        - ``fetchMajorShareholdersRaw`` — list 반환 변종.
        - ``iterInsiderTradingRaw`` — 임원 거래 streaming pair.

    Requires:
        - DART OpenAPI API key.
        - 네트워크.

    AIContext:
        외국인 지분 / M&A 시그널 탐지 파이프라인에서 메모리 부담 회피용.

    LLM Specifications:
        AntiPatterns:
            - 동기 ``for`` 순회 → TypeError.
            - list 캐스팅이 필요하면 ``fetchMajorShareholdersRaw`` 직접 호출 권장.
        OutputSchema:
            - yield item: 6 key dict (fetchMajorShareholdersRaw Returns 참조).
        Prerequisites:
            - ``DART_API_KEY`` 등록.
        Freshness:
            - 실시간 (보고 5 영업일 이내 접수).
        Dataflow:
            - ``fetchMajorShareholdersRaw`` 결과 → 본 함수 yield → caller.
        TargetMarkets:
            - KR (DART).

    Raises:
        없음.
    """
    rows = await fetchMajorShareholdersRaw(stockCode, limit=limit)
    for r in rows:
        yield r


def _tradeTypeOf(changeShares: int) -> str:
    """증감 주식수 부호로 거래 유형을 가른다.

    DART elestock 응답에는 취득과 처분을 직접 적은 필드가 없다. 증감이 양수면 취득,
    음수면 처분이고 0 이면 보유 주식수만 정정된 보고라 어느 쪽도 아니다.
    """

    if changeShares > 0:
        return "취득"
    if changeShares < 0:
        return "처분"
    return ""


def _safeInt(val) -> int:
    """안전한 int 변환 — 콤마/기호 제거. None/실패 시 0."""
    if val is None:
        return 0
    try:
        return int(str(val).replace(",", "").replace("+", "").strip() or "0")
    except (ValueError, TypeError):
        return 0


def _safeFloat(val) -> float:
    """안전한 float 변환 — 콤마/기호 제거. None/실패 시 0.0."""
    if val is None:
        return 0.0
    try:
        return float(str(val).replace(",", "").replace("+", "").strip() or "0")
    except (ValueError, TypeError):
        return 0.0


class _ModuleInsiderRawProvider:
    """Module 함수를 InsiderRawProvider Protocol 로 어댑팅.

    Args:
        없음 — module-level singleton.

    Returns:
        instance — InsiderRawProvider Protocol 호환.

    Raises:
        없음.

    Example:
        >>> from dartlab.core.insiderRawProvider import getInsiderRawProvider
        >>> getInsiderRawProvider()  # _ModuleInsiderRawProvider singleton
    """

    @staticmethod
    async def fetchInsiderTradingRaw(stockCode: str, *, limit: int | None = None) -> list[dict]:
        """임원/주요주주 거래 raw dict 위임 — module 동명 함수 호출.

        Args:
            stockCode: 종목코드 (6 자리).
            limit: 최대 행 수 상한.

        Returns:
            list[dict] — module 함수 결과 그대로.

        Raises:
            없음 — module 함수가 흡수.

        Example:
            >>> # await provider.fetchInsiderTradingRaw("005930", limit=20)
        """
        return await fetchInsiderTradingRaw(stockCode, limit=limit)

    @staticmethod
    async def fetchMajorShareholdersRaw(stockCode: str, *, limit: int | None = None) -> list[dict]:
        """5% 이상 대량보유 변동 raw dict 위임 — module 동명 함수 호출.

        Args:
            stockCode: 종목코드 (6 자리).
            limit: 최대 행 수 상한.

        Returns:
            list[dict] — module 함수 결과 그대로.

        Raises:
            없음 — module 함수가 흡수.

        Example:
            >>> # await provider.fetchMajorShareholdersRaw("005930", limit=10)
        """
        return await fetchMajorShareholdersRaw(stockCode, limit=limit)


# DIP: gather/sources/insider 가 core.insiderRawProvider 통해 본 모듈 사용 — gather → providers
# cross 회피. import 시점 register.
from dartlab.core.insiderRawProvider import registerInsiderRawProvider  # noqa: E402

registerInsiderRawProvider(_ModuleInsiderRawProvider())
