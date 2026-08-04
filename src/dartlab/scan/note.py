"""scan 주석(note) 횡단 reader. 전종목 note lineitem 을 개념별 prebuild 에서 읽는다.

Capabilities:
    - prebuild ``note/{bareName}.parquet`` (long: stockCode/account/label/period/value) 을 읽어 특정
      주석 개념(재고자산·리스·법인세·판관비 등)의 전종목 lineitem 횡단면을 반환한다. 카탈로그 registered
      단일축 note 를 account/ratio 원자 축과 같은 결로 스크리닝 가능하게 노출한다.

Args:
    Public entry point accepts note conceptId (또는 한글 label/bareName).

Returns:
    long DataFrame (종목x항목x기간) + valueNum 파생.

Example:
    >>> import dartlab
    >>> dartlab.scan("note", "재고자산")                      # doctest: +SKIP
    >>> dartlab.scan("note")                                   # 가용 note 개념 목록

Guide:
    절대 금액 cross-company 비교는 단위 정규화된 finance scan 이 SSOT. 본 축은 노트 하위분류(재고
    상품/제품/원재료, 리스 부채/자산, 법인세 당기/이연 등)의 항목 단위 횡단이다. 회사별 원표 렌더는
    터미널이 담당한다. read-time panel 파싱은 OOM 이라 하지 않는다 (prebuild consolidation SSOT).

SeeAlso:
    ``scan.builders.kr.notes`` (prebuild source) · ``scan.salesByProduct`` (동료 공시파생 축)
    · ``providers.dart.panel.cell.readNoteStatement`` (단일 종목 노트 추출).

Requires:
    prebuild ``data/dart/scan/note/{bareName}.parquet`` (HF 자동 다운로드, best-effort).

AIContext:
    Agent 가 ``scan("note", 이름)`` 호출 시 dispatch. "재고 세분 급증", "리스부담 상위", "법인세율
    이상치" 스크리닝 source. 개념 목록은 ``scan("note")`` (target 없이). 후보는 Company.panel 로 검증.

LLM Specifications:
    AntiPatterns: read-time panel 파싱 금지. 절대금액 cross-company 비교 금지 (finance scan 이 SSOT).
    OutputSchema: stockCode·account·label·period·value(raw)·valueNum(파생 float).
    Prerequisites: prebuild note/{bareName}.parquet 존재 (첫 베이크 전이면 빈 프레임).
    Freshness: 주간 full scan prebuild 사이클 산출물.
    Dataflow: HF note/{bareName}.parquet -> lazy read -> valueNum 파생.
    TargetMarkets: KR DART 정기보고서 주석.
"""

from __future__ import annotations

import polars as pl

from dartlab.scan.builders.kr.notes import SCAN_NOTE_CONCEPTS
from dartlab.scan.io.parquet import _downloadScanFile, _ensureScanData, _maybeRefreshScanFile

_NOTE_READ_SCHEMA = {
    "stockCode": pl.Utf8,
    "account": pl.Utf8,
    "label": pl.Utf8,
    "period": pl.Utf8,
    "value": pl.Utf8,
    "valueNum": pl.Float64,
}

# 사용자 입력(conceptId / bareName / 한글 label) -> bareName(파일명) 해소 맵. 카탈로그 SSOT 도출.
_RESOLVE: dict[str, str] = {}
for _bare, _ntKey, _label in SCAN_NOTE_CONCEPTS:
    _RESOLVE[_bare] = _bare
    _RESOLVE[f"note.{_bare}"] = _bare
    _RESOLVE[_label] = _bare


def _emptyFrame() -> pl.DataFrame:
    """note reader 빈 결과 (returned schema 고정, 축 무회귀)."""
    return pl.DataFrame(schema=_NOTE_READ_SCHEMA)


def _resolveBare(conceptId: str) -> str | None:
    """conceptId / bareName / 한글 label -> bareName(파일명). 미매칭 None."""
    if conceptId in _RESOLVE:
        return _RESOLVE[conceptId]
    return _RESOLVE.get(str(conceptId).removeprefix("note."))


def _valueNumExpr() -> pl.Expr:
    """raw value(콤마·삼각형 음수·괄호) -> Float64 valueNum (벡터 파싱, salesByProduct._num 동형)."""
    s = pl.col("value").cast(pl.Utf8).str.strip_chars()
    neg = (
        s.str.starts_with("△")
        | s.str.starts_with("▲")
        | s.str.starts_with("(")
        | s.str.starts_with("-")
        | s.str.starts_with("−")
        | s.str.ends_with(")")
    )
    digits = s.str.replace_all(r"[^0-9.]", "")
    val = pl.when(digits.str.len_chars() == 0).then(None).otherwise(digits.cast(pl.Float64, strict=False))
    return pl.when(neg).then(-val).otherwise(val).alias("valueNum")


def scanNote(conceptId: str, *, freq: str = "Y") -> pl.DataFrame:
    """전종목 단일 주석(note) 개념의 항목x기간 횡단 (카탈로그 registered 단일축 note).

    Parameters
    ----------
    conceptId : str
        주석 개념 식별자. conceptId(``"note.inventory"``) · bareName(``"inventory"``) · 한글
        label(``"재고자산"``) 모두 가능. 목록은 :func:`scanNoteList` 또는 ``scan("note")``.
    freq : {"Y"}, default "Y"
        Phase 1 은 연간(사업보고서 당기/전기 연장)만 굽는다. 시그니처 일관성용, 현재 무시.

    Returns
    -------
    pl.DataFrame
        long 컬럼:

        - stockCode (str): 종목코드
        - account (str): 정규화 항목명 (회사 간 join 키)
        - label (str): 최신 filing 표시명
        - period (str): 연도 (예 "2024")
        - value (str): raw valueRaw (콤마·삼각형 음수 원형)
        - valueNum (float): value 벡터 파싱값 (스크리닝용, 비숫자 null)

        미등록 conceptId 또는 첫 베이크 전이면 빈 DataFrame (축 무회귀).

    Raises
    ------
    polars.PolarsError
        note parquet 손상 시.

    Examples
    --------
    >>> import dartlab
    >>> df = dartlab.scan("note", "재고자산")                             # doctest: +SKIP
    >>> df.filter(pl.col("period") == "2024").sort("valueNum", descending=True).head()  # doctest: +SKIP

    Capabilities:
        - prebuild ``note/{bareName}.parquet`` 을 read + valueNum 파생. read-time panel 파싱 없음.
        - 첫 베이크 전이거나 파일 부재 시 빈 DataFrame (축 무회귀, "데이터 없음" 표시).

    AIContext:
        노트 하위분류 횡단 스크리닝 source. 카탈로그 registered 단일축 note 를 굽는다. 절대금액 비교는
        단위 이질이라 항목/기간 단위 비율·추세로 판단하고 후보는 Company.panel 로 검증.

    Guide:
        - 개념 목록은 ``scan("note")`` (target 없이) 또는 :func:`scanNoteList`.
        - account 는 정규화 항목명(회사 간 동일 항목 join), label 은 표시명. valueNum 으로 정렬/필터.

    When:
        cross-company 노트 lineitem 스크리닝 시.

    How:
        ``_ensureScanData`` 로 표준 필수본 확인 후 ``note/{bareName}.parquet`` best-effort 단일 다운로드.
        있으면 read + valueNum 파생, 없으면 빈 프레임.

    Requires:
        prebuild ``data/dart/scan/note/{bareName}.parquet`` (:func:`buildNotes` 산출).

    SeeAlso:
        - :func:`scanNoteList` (가용 note 개념) · :func:`dartlab.scan.builders.kr.notes.buildNotes`
        - :func:`dartlab.providers.dart.panel.cell.readNoteStatement` (단일 종목 노트)
    """
    bare = _resolveBare(conceptId)
    if bare is None:
        return _emptyFrame()

    scanDir = _ensureScanData()
    path = scanDir / "note" / f"{bare}.parquet"
    if not path.exists():
        # note 는 _REQUIRED 아님 (첫 베이크 전 404 로 타 축 깨짐 방지). 단일 best-effort.
        try:
            _downloadScanFile(scanDir, f"note/{bare}.parquet")
        except (ExceptionGroup, OSError, RuntimeError, ValueError):
            return _emptyFrame()
    else:
        # HF 는 매일 갱신되므로 TTL 게이트 후 ETag 재검증 (실패 시 로컬 유지).
        _maybeRefreshScanFile(scanDir, f"note/{bare}.parquet")
    if not path.exists():
        return _emptyFrame()

    df = pl.read_parquet(str(path))
    if df.is_empty() or "value" not in df.columns:
        return _emptyFrame()
    return df.with_columns(_valueNumExpr())


def scanNoteList() -> list[dict[str, str]]:
    """가용 note 개념 목록 (카탈로그 registered 단일축 note).

    Returns
    -------
    list[dict[str, str]]
        - name : str -- ``scan("note", name)`` 에 넣는 bareName (예 "inventory").
        - label : str -- 한글 주석명 (예 "재고자산").
        - conceptId : str -- 카탈로그 conceptId (예 "note.inventory").
        - disclosureKey : str -- 주석 표준코드 (예 "NT_D826380").

    Raises
    ------
    없음.

    Examples
    --------
    >>> dartlab.scan("note")                    # doctest: +SKIP
    >>> [r["name"] for r in scanNoteList()][:3]  # doctest: +SKIP

    Capabilities:
        - :data:`SCAN_NOTE_CONCEPTS` (카탈로그 도출) 를 목록 dict 로. ``scan("note")`` target 없는 호출의
          가이드 source.

    AIContext:
        사용자가 "어떤 주석 스크리닝 가능?" 물을 때 축 목록 제공. name 을 ``scan("note", name)`` 에 사용.

    Guide:
        - name(bareName) 또는 label(한글) 또는 conceptId 로 :func:`scanNote` 호출 가능.

    When:
        note 축 target 미지정 호출 시 (scanClass._listForAxis).

    How:
        :data:`SCAN_NOTE_CONCEPTS` 순회 -> dict 리스트.

    Requires:
        ``dartlab.scan.builders.kr.notes.SCAN_NOTE_CONCEPTS`` (카탈로그 registered 단일축 note).

    SeeAlso:
        - :func:`scanNote` · :data:`dartlab.scan.builders.kr.notes.SCAN_NOTE_CONCEPTS`
    """
    return [
        {"name": bare, "label": label, "conceptId": f"note.{bare}", "disclosureKey": ntKey}
        for bare, ntKey, label in SCAN_NOTE_CONCEPTS
    ]


__all__ = ["scanNote", "scanNoteList"]
