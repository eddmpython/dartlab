"""K-IFRS 주석 통합 접근.

사용법::

    c = Company("005930")
    c.notes.inventory           # 재고자산 DataFrame
    c.notes["재고자산"]          # 동일
    c.notes.keys()              # 지원 항목 목록
    c.notes.all()               # 전체 dict

주석 항목 추가 시 core/registry.py의 notes 카테고리에 DataEntry를 추가하고,
아래 _NOTES_DISPATCH에 디스패치 정보를 추가하면 자동 반영됨.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import polars as pl


# 주석별 디스패치 정보: 영문명 → (호출 모듈, 한글 키워드, extractor)
# "notesDetail"이면 _call_notesDetail(한글키워드) 호출, 아니면 _call_module(모듈명) 호출.
_NOTES_DISPATCH: OrderedDict[str, tuple[str, str, Any]] = OrderedDict([
    ("receivables",        ("notesDetail",    "매출채권",         lambda r: r.tableDf)),
    ("inventory",          ("notesDetail",    "재고자산",         lambda r: r.tableDf)),
    ("tangibleAsset",      ("tangibleAsset",  "유형자산",         lambda r: r.movementDf)),
    ("intangibleAsset",    ("notesDetail",    "무형자산",         lambda r: r.tableDf)),
    ("investmentProperty", ("notesDetail",    "투자부동산",       lambda r: r.tableDf)),
    ("affiliates",         ("affiliates",     "관계기업",         lambda r: r.movementDf)),
    ("borrowings",         ("notesDetail",    "차입금",           lambda r: r.tableDf)),
    ("provisions",         ("notesDetail",    "충당부채",         lambda r: r.tableDf)),
    ("eps",                ("notesDetail",    "주당이익",         lambda r: r.tableDf)),
    ("lease",              ("notesDetail",    "리스",             lambda r: r.tableDf)),
    ("segments",           ("segments",       "부문정보",         lambda r: r.revenue)),
    ("costByNature",       ("costByNature",   "비용의성격별분류", lambda r: r.timeSeries)),
])

# core/registry.py와 동기화된 외부 인터페이스 (하위 호환)
_REGISTRY = _NOTES_DISPATCH

# 한글→영문 역매핑
_KR_MAP: dict[str, str] = {v[1]: k for k, v in _REGISTRY.items()}


class Notes:
    """K-IFRS 주석 데이터 통합 접근.

    영문 속성 또는 한글 딕셔너리 키로 접근 가능.
    접근 시 lazy 로딩 + 캐싱.
    """

    def __init__(self, company: Any):
        object.__setattr__(self, "_company", company)
        object.__setattr__(self, "_cache", {})

    def __getattr__(self, name: str) -> pl.DataFrame | None:
        if name.startswith("_"):
            raise AttributeError(name)
        if name in _REGISTRY:
            return self._get(name)
        raise AttributeError(f"Notes에 '{name}' 항목이 없습니다. 지원: {list(_REGISTRY.keys())}")

    def __getitem__(self, key: str) -> pl.DataFrame | None:
        eng = _KR_MAP.get(key, key)
        if eng not in _REGISTRY:
            raise KeyError(f"Notes에 '{key}' 항목이 없습니다. 지원: {list(_KR_MAP.keys())}")
        return self._get(eng)

    def _get(self, name: str) -> pl.DataFrame | None:
        if name in self._cache:
            return self._cache[name]

        spec = _REGISTRY[name]
        module, krName, extractor = spec

        from dartlab import config
        if config.verbose:
            print(f"  ▶ {self._company.corpName} · {krName}")

        try:
            if module == "notesDetail":
                result = self._company._call_notesDetail(krName)
            else:
                result = self._company._call_module(module)
            df = extractor(result) if result else None
        except (FileNotFoundError, ValueError, KeyError, AttributeError, TypeError):
            df = None

        self._cache[name] = df
        return df

    def all(self) -> dict[str, pl.DataFrame | None]:
        """모든 주석 항목을 dict로 반환."""
        return {name: self._get(name) for name in _REGISTRY}

    def keys(self) -> list[str]:
        """지원하는 영문 속성명 목록."""
        return list(_REGISTRY.keys())

    def keys_kr(self) -> list[str]:
        """지원하는 한글 키워드 목록."""
        return list(_KR_MAP.keys())

    def __repr__(self) -> str:
        cached = [k for k in _REGISTRY if k in self._cache]
        return f"Notes({len(cached)}/{len(_REGISTRY)} loaded)"

    def __contains__(self, key: str) -> bool:
        return key in _REGISTRY or key in _KR_MAP
