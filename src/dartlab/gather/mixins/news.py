"""Gather news/dartDoc mixin — 뉴스 RSS + DART 공시 원문 2 메서드."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl

from ..infra.http import runAsync
from ..infra.telemetry import emitGatherFetch
from ..sources import naverNews as _naver
from ..sources import news as _news
from ..types import SourceAttemptsExhaustedError
from .context import GatherMixinContext


class _GatherNewsMixin(GatherMixinContext):
    """뉴스 + DART 공시 원문 메서드 모음 — Gather 클래스 2 메서드."""

    def news(self, query: str, *, market: str = "KR", days: int = 30) -> "pl.DataFrame":
        """뉴스 검색 — KR=네이버 우선(+Google 폴백), 그 외 Google News RSS.

        Capabilities:
            - KR: 네이버 검색 API 우선 (제목+스니펫). 키 미설정/빈결과 시 Google News RSS 폴백.
            - KR 외: Google News RSS
            - circuit breaker + TTL 캐시 (DARTLAB_TTL_NEWS override)
            - DataFrame: date, title, source, url, description 컬럼

        AIContext:
            - sentiment / event-driven 분석의 외부 신호 원천
            - 본문은 untrusted external — provider 가 [EXTERNAL CONTENT START] 마커 적용
            - 소스는 내부 라우팅 (반환 source 컬럼이 naver/google_news 구분)

        Guide:
            query 는 자유 문자열 (종목명 + 키워드 조합 가능). 네이버 결과는 라이브
            표시용 (비영속) — 공개 적재는 별도 private 경로 (naverNews archive).

        When:
            sentiment / event 분석 / catalyst 모니터링 시.

        How:
            KR → naverNews._fetchAsync → (빈결과) news._fetchAsync(google) → toDataFrame.

        Args:
            query: 검색어 (종목명, 키워드 등).
            market: "KR" 또는 "US". 기본 "KR".
            days: 최근 N일 뉴스 (Google 경로). 기본 30.

        Returns:
            pl.DataFrame — date, title, source, url, description, provider, fetchedAt 컬럼.
            결과 없으면 빈 DataFrame.

        Requires:
            없음 (네이버 키 없으면 자동 Google 폴백 — 기존 동작 보존).

        Raises:
            ValueError / SourceUnavailableError — 입력 또는 최종 fallback 공급자 실패.

        Example::

            g = getDefaultGather()
            g.news("삼성전자")                # KR — 네이버 우선
            g.news("Apple", market="US")     # US — Google News
            g.news("반도체", days=7)          # 최근 7일

        See Also:
            ``dartDoc`` — DART 공시 본문 (RSS 가 아닌 viewer 직접).
        """
        t0 = time.monotonic()
        cacheHit = False
        try:
            if not isinstance(query, str) or not query.strip():
                raise ValueError("news query는 비어 있지 않은 문자열이어야 합니다")
            normalizedMarket = market.upper()
            if normalizedMarket not in {"KR", "US"}:
                raise ValueError(f"news market은 KR/US만 지원합니다: {market!r}")
            if days < 1:
                raise ValueError(f"news days는 1 이상이어야 합니다: {days}")

            from ..infra.cache import buildCacheSlot

            cacheSlot = buildCacheSlot("news", market=normalizedMarket, days=days)
            cached = self._cache.getTyped(query, cacheSlot)
            if cached is not None:
                cacheHit = True
                return cached  # type: ignore[return-value]
            if normalizedMarket == "KR":
                attempts: list[tuple[str, Exception]] = []
                naverSucceeded = False
                try:
                    items = runAsync(_naver._fetchAsync(query, market=normalizedMarket, client=self._client))
                    naverSucceeded = True
                except ValueError:
                    raise
                except Exception as exc:
                    attempts.append(("naver_news", exc))
                    items = []
                if not items:
                    try:
                        items = runAsync(
                            _news._fetchAsync(
                                query,
                                market=normalizedMarket,
                                days=days,
                                client=self._client,
                            )
                        )
                    except ValueError:
                        raise
                    except Exception as exc:
                        attempts.append(("google_news", exc))
                        if not naverSucceeded:
                            raise SourceAttemptsExhaustedError("news", attempts) from exc
                        items = []
                    provider = "google_news"
                else:
                    provider = "naver_news"
            else:
                try:
                    items = runAsync(
                        _news._fetchAsync(
                            query,
                            market=normalizedMarket,
                            days=days,
                            client=self._client,
                        )
                    )
                except ValueError:
                    raise
                except Exception as exc:
                    raise SourceAttemptsExhaustedError("news", [("google_news", exc)]) from exc
                provider = "google_news"
            df = _news.toDataFrame(items, provider=provider)
            if not df.is_empty():
                self._cache.putTyped(query, cacheSlot, df)
            return df
        finally:
            emitGatherFetch("news", (time.monotonic() - t0) * 1000, cacheHit=cacheHit, market=market)

    def dartDoc(self, rceptNo: str) -> "pl.DataFrame":
        """DART 공시 viewer 원문 fetch (14자리 rcept_no, 무인증).

        Capabilities:
            - 14자리 rcept_no 만으로 공시 원문 fetch
            - viewer 인덱스 페이지 (dsaf001/main.do) sub-doc 목차 파싱
            - 각 섹션 HTML → 텍스트 (테이블 마크다운 보존)
            - API key 불필요 (providers/dart/openapi 와 분리)
            - rate limit + circuit breaker + TTL 캐시 (gather/infra 자동)

        Args:
            rceptNo: 14자리 접수번호 (예: "20240315000123").

        Returns:
            pl.DataFrame — section_order, title, url, text 컬럼.

        Requires:
            네트워크 (dart viewer 무인증 접근).

        Raises:
            InvalidRceptNoError: rceptNo 가 14자리 숫자 아님.
            DocumentNotFoundError: viewer 가 sub-doc 을 반환하지 않음.

        Untrusted Body:
            viewer 본문은 외부 1차 출처지만 AI 엔진 소비 시
            ``Ref.sourceType="external"`` 마커로 감싸야 한다 (호출자 책임).

        Example::

            g = getDefaultGather()
            df = g.dartDoc("20240315000123")
        """
        t0 = time.monotonic()
        try:
            from dartlab.gather.dart.viewer import fetch as _fetchDartDoc

            return _fetchDartDoc(rceptNo, client=self._client)
        finally:
            emitGatherFetch("dartDoc", (time.monotonic() - t0) * 1000, cacheHit=False, market="KR")
