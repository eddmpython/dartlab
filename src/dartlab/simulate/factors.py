"""매크로 팩터 레지스트리 + 공통 식 SSOT : 팩터 추가 = 1행, 하류 전체 자동흡수 (L2.5 simulate).

덕지덕지 가드: 팩터↔베타컬럼 매핑(scenarioTree·scenarioSim·lattice 3중복)·변화식(rate 차분 vs
가격 수익률, table·scenarioSim 2중복)·base 점수 컬럼 인식(scenarioTree·lattice 2중복)·매크로
시리즈 하드코딩(table)을 전부 여기 한곳으로 접는다.

**자동흡수 메커니즘 (운영자 요구)**: 새 매크로 데이터가 생기면 `registerMacroFactor` 1줄(또는
MACRO_FACTORS 1행)로 등록한다. table.macroDaily(패널)·macroBetaByCodeWide(전종목 베타)·
scenarioSim(공분산·MC)·lattice(격자 커널)·scenarioTree(반응·네트워크)·profile(노출 축5)이 전부
이 레지스트리를 순회하므로 **하류 코드 수정 0** 으로 새 팩터가 베타·격자·시나리오·프로파일에
흡수된다. 소스 데이터 부재는 각 소비처가 결측으로 정직 처리 (0 대체 금지).

Layer: L2.5 simulate. polars 만 의존 (하향). 순수 선언 + 식.
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl


@dataclass(frozen=True)
class MacroFactor:
    """매크로 팩터 1행 계약. 등록 = 하류(패널·베타·격자·시나리오) 자동흡수.

    Args:
        factor: 팩터 id (베타 컬럼 = f"{factor}Beta").
        source: data/macro/<source>/observations.parquet 소스 폴더.
        seriesId: 그 소스의 시리즈 id.
        kind: "price"(변화 = 수익률) | "level"(변화 = 차분, 예 금리 %p).
        label: 사람용 이름.
    """

    factor: str
    source: str
    seriesId: str
    kind: str
    label: str = ""


# 핵심 3팩터 (검증 완료: 베타 실측·격자 커널·역사검증). 확장은 registerMacroFactor.
_REGISTRY: list[MacroFactor] = [
    MacroFactor("rate", "ecos", "BASE_RATE", "level", "한국 기준금리"),
    MacroFactor("fx", "ecos", "USDKRW", "price", "원/달러"),
    MacroFactor("oil", "fred", "DCOILWTICO", "price", "WTI 유가"),
]


def registerMacroFactor(mf: MacroFactor) -> None:
    """팩터 등록 (자동흡수 진입점). 같은 factor id 재등록은 교체 (멱등).

    Args:
        mf: MacroFactor 선언. 등록 즉시 macroDaily·macroBetaByCodeWide·factorCovariance·
            growLattice·scenarioResponse·profile 축5 가 순회에 포함한다 (하류 수정 0).
    """
    global _REGISTRY
    _REGISTRY = [f for f in _REGISTRY if f.factor != mf.factor] + [mf]


def unregisterMacroFactor(factor: str) -> None:
    """팩터 해제 (대칭 관리·테스트 정리). 핵심 3팩터 해제도 허용하되 소비처가 결측으로 정직 처리."""
    global _REGISTRY
    _REGISTRY = [f for f in _REGISTRY if f.factor != factor]


def macroFactors() -> list[MacroFactor]:
    """등록된 팩터 전수 (등록 순서 안정)."""
    return list(_REGISTRY)


def factorNames() -> list[str]:
    """팩터 id 목록 (하류 순회 축)."""
    return [f.factor for f in _REGISTRY]


def betaCol(factor: str) -> str:
    """팩터 → 베타 컬럼명 규약 (f"{factor}Beta"). 매핑 하드코딩 금지의 단일 규칙."""
    return f"{factor}Beta"


def factorBetaMap() -> dict[str, str]:
    """{factor: betaCol} 전수 (scenarioTree·scenarioSim·lattice 공용, 3중복 해소)."""
    return {f.factor: betaCol(f.factor) for f in _REGISTRY}


def macroChange(factor: str) -> pl.Expr:
    """팩터 일별 변화 Expr: level = 차분(%p), price = 수익률. 미등록 팩터는 price 규약."""
    kind = next((f.kind for f in _REGISTRY if f.factor == factor), "price")
    if kind == "level":
        return pl.col(factor) - pl.col(factor).shift(1)
    return pl.col(factor) / pl.col(factor).shift(1) - 1


def baseScoreExpr(df: pl.DataFrame) -> pl.Expr:
    """base 점수 컬럼 자동 인식 (baseScore|score|consensus) → Float64 Expr. 2중복 해소.

    Raises:
        ValueError: 세 컬럼 모두 부재.
    """
    for cand in ("baseScore", "score", "consensus"):
        if cand in df.columns:
            return pl.col(cand).cast(pl.Float64)
    raise ValueError("baseScores 에 score/consensus/baseScore 컬럼 필요")
