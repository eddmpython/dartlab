"""L2 4엔진 (analysis · credit · quant · macro) 호출 계약 일관성 회귀.

Phase 8 정렬 — 가이드 DF 컬럼 / Company-bound 진입점 / kwarg 명명 / 레지스트리 구조.
"""

from __future__ import annotations

import ast
from dataclasses import is_dataclass
from pathlib import Path

import polars as pl
import pytest

# ── 공개 계약 엔진 호출체 ──────────────────────────────────


@pytest.mark.unit
def test_contract_engines_are_all_callable():
    """`_CONTRACT_ENGINES` 에 실린 엔진은 전부 `dartlab.{engine}(...)` 로 불려야 한다.

    배선이 세 곳(`_LAZY_ATTRS` · 모듈 `__getattr__` · `_makeCallableModule` 팩토리)에
    흩어져 있던 동안, 계약 엔진이 통째로 빠져도 어느 쪽도 그걸 몰랐다. 실제로 강행규칙
    계약 목록에 실려 있던 `frame`·`synth`·`reference`·`story` 넷은 호출체가 없었고
    `reference` 는 속성 자체가 없어 AttributeError 였다.
    """
    import dartlab
    from dartlab import _CONTRACT_ENGINES

    broken = []
    for name in _CONTRACT_ENGINES:
        obj = getattr(dartlab, name, None)
        if obj is None or not callable(obj):
            broken.append(f"{name}({'없음' if obj is None else type(obj).__name__})")
    assert not broken, "계약 엔진인데 호출체가 없다: " + ", ".join(broken)


@pytest.mark.unit
def test_contract_engine_aliases_resolve_to_same_object():
    """엔진 별칭은 본체와 같은 것을 준다 (`data` 는 `dataHub` 의 옛 이름)."""
    import dartlab
    from dartlab import _ENGINE_ALIASES

    for alias, target in _ENGINE_ALIASES.items():
        assert getattr(dartlab, alias) is getattr(dartlab, target), f"별칭 {alias} 는 {target} 와 같아야 한다"


@pytest.mark.unit
def test_internal_l15_packages_have_no_call_surface():
    """계약이 아닌 L1.5 가공층에는 호출 표면이 없어야 한다.

    `frame`·`synth`·`reference` 는 분석엔진이 소비하는 내부 층이다 (engine spec 없음).
    여기에 호출체가 생기면 강행규칙이 금지한 새 계약 표면이 몰래 는 것이다.
    """
    import dartlab
    from dartlab import _CONTRACT_ENGINES

    for name in ("frame", "synth", "reference"):
        assert name not in _CONTRACT_ENGINES, f"{name} 은 계약 엔진이 아니다"
        obj = getattr(dartlab, name, None)
        assert obj is None or not callable(obj), f"dartlab.{name} 에 호출 표면이 생겼다"


# ── 가이드 DF 표준 컬럼 ────────────────────────────────────


@pytest.mark.unit
def test_4engine_guide_returns_dataframe():
    """4엔진 Company-bound 무인자 호출 → polars DataFrame + 공통 컬럼."""
    import dartlab

    c = dartlab.Company("005930")
    common = {"axis", "label", "description", "example"}
    for name in ("analysis", "credit", "quant", "macro"):
        df = getattr(c, name)()
        assert isinstance(df, pl.DataFrame), f"c.{name}() not DataFrame"
        cols = set(df.columns)
        assert common.issubset(cols), f"c.{name} missing cols: {common - cols}"


# ── Company-bound 진입점 ───────────────────────────────────


@pytest.mark.unit
def test_company_has_4_engine_methods():
    """Company 에 analysis/credit/quant/macro 모두 존재."""
    import dartlab

    c = dartlab.Company("005930")
    for name in ("analysis", "credit", "quant", "macro"):
        assert hasattr(c, name), f"Company.{name} missing"


@pytest.mark.unit
def test_macro_company_bound_market_routing():
    """c.macro 가 KR 기본, EDGAR 회사는 US 위임."""
    import dartlab

    kr = dartlab.Company("005930")
    g_kr = kr.macro()
    assert isinstance(g_kr, pl.DataFrame)


@pytest.mark.unit
def test_phase10_h2_review_secondary_on_company():
    """Phase 10 H2 helper는 Python 하위호환만 유지하고 canonical capability에는 싣지 않는다."""
    import dartlab
    from dartlab.reference.capability import buildCapabilities

    c = dartlab.Company("005930")
    for name in ("causalWeights", "valuationImpact", "storyTree", "narrativeDiff"):
        assert callable(getattr(c, name)), f"Company.{name} compatibility method missing"
        assert f"Company.{name}" not in buildCapabilities()


@pytest.mark.unit
def test_phase10_section_act_field():
    """Phase 10 F1 — SectionMeta.act 필드가 23섹션 + 3메타 모두 설정."""
    from dartlab.story.catalog import SECTIONS

    # 모든 섹션이 act 필드 보유
    for s in SECTIONS:
        assert hasattr(s, "act"), f"{s.key} missing act"
        assert s.act in (0, 1, 2, 3, 4, 5, 6), f"{s.key} invalid act={s.act}"

    # 6막 모두 최소 1 섹션
    acts = {s.act for s in SECTIONS}
    for a in (1, 2, 3, 4, 5, 6):
        assert a in acts, f"act {a} has no section"


@pytest.mark.unit
def test_phase10_invariants_20():
    """Phase 10 F2 — 불변량 20개 구현."""
    from dartlab.story.validators.validators import _INVARIANTS

    assert len(_INVARIANTS) >= 20, f"불변량 {len(_INVARIANTS)}개 (20 미만)"


@pytest.mark.unit
def test_phase10_storyValidation_in_all_reportTypes():
    """Phase 10 F4 — 11 reportType 전부 storyValidation 포함."""
    from dartlab.story.reportTypes import REPORT_TYPES

    for key, rt in REPORT_TYPES.items():
        assert "storyValidation" in rt.sectionOrder, f"{key} missing storyValidation"


# ── kwargs 명명 ────────────────────────────────────────────


@pytest.mark.unit
def test_quant_axis_alias_for_metric(monkeypatch):
    """quant: axis= (정규) + metric= (호환 alias) 둘 다 동작."""
    import dartlab
    import dartlab.quant.screen.axTechnical as technicalModule

    prices = pl.DataFrame(
        {
            "date": pl.date_range(pl.date(2026, 1, 1), pl.date(2026, 3, 31), "1d", eager=True),
            "open": [100.0] * 90,
            "high": [101.0] * 90,
            "low": [99.0] * 90,
            "close": [100.0] * 90,
            "volume": [1000] * 90,
        }
    )
    monkeypatch.setattr(technicalModule, "fetchOhlcv", lambda *args, **kwargs: prices)

    c = dartlab.Company("005930")
    a = c.quant(axis="지표")
    b = c.quant(metric="지표")
    assert a is not None
    assert b is not None


# ── credit 레지스트리 통일 ─────────────────────────────────


@pytest.mark.unit
def test_credit_axis_registry_uses_dataclass():
    """credit/_AXIS_REGISTRY 는 @dataclass _AxisEntry 로 통일 (4엔진 동일 패턴)."""
    from dartlab.credit import _AXIS_REGISTRY

    assert isinstance(_AXIS_REGISTRY, dict)
    assert len(_AXIS_REGISTRY) >= 7
    for entry in _AXIS_REGISTRY.values():
        assert is_dataclass(entry), f"{entry} is not a dataclass"
        assert hasattr(entry, "axis")
        assert hasattr(entry, "label")
        assert hasattr(entry, "group")


@pytest.mark.unit
def test_credit_guide_has_group_column():
    """credit 가이드 DF 도 group 컬럼 보유 (4엔진 통일)."""
    import dartlab

    df = dartlab.credit()
    assert "group" in df.columns


# ── L2 cross-import 회귀 가드 ──────────────────────────────


# L2 cross-import 룰 (옵션 C 하이브리드 — 2026-04-27)
#
# 큰 레포 표준 (sklearn / pandas / polars / django) 패턴 적용:
#   - 수학 primitive (dict/숫자 반환 함수) 는 어느 L2 에서나 import 자유
#   - 도메인 결정 결과 (Result/Score/Axis/Grade dataclass, mapTo* 매핑 함수) 만 import 금지
#   - 결과 결합은 review/story 위임
#
# 심볼명 패턴 검사:
#   - 차단: 대문자 시작 + Result/Score/Axis/Grade 접미사 (dataclass), mapTo*/estimateGrade*/notchGrade* (매핑)
#   - 허용: 그 외 모두 (소문자 함수 + 일반 클래스)
#
import re

# 결과 dataclass = 대문자 시작 + 접미사. 소문자 시작 = 함수 (수학/유틸).
_BLOCKED_DATACLASS_PATTERNS = [
    re.compile(r"^[A-Z].*Result$"),
    re.compile(r"^[A-Z].*Score$"),
    re.compile(r"^[A-Z].*Axis$"),
    re.compile(r"^[A-Z].*Grade$"),
]
# 매핑 함수 (소문자 함수지만 도메인 룰 임)
_BLOCKED_MAPPING_PATTERNS = [
    re.compile(r"^mapTo"),
    re.compile(r"^estimateGrade"),
    re.compile(r"^notchGrade"),
]


def _classifySymbol(name: str) -> str:
    """심볼명 → 'blocked' / 'allowed'.

    차단:
      - 결과 dataclass: ``MertonResult``, ``CreditGapResult``, ``DistressScore`` 등
      - 매핑 함수: ``mapTo20Grade``, ``estimateGrade``
    허용 (그 외 모두):
      - 소문자 시작 함수: ``solveMerton``, ``calcSurvivalWeight``, ``ghsCrisisScore`` 등
        — 수학 primitive 가정 (dict/숫자 반환). 결과 dataclass 가 함수 시그니처에 들어가
        있어도 import 형태로 잡지 않음 (review 가 합치는 게 사상)
      - 대문자 시작인데 Result/Score/Axis/Grade 접미사 없는 클래스: 알 수 없음 → 허용
    """
    for p in _BLOCKED_DATACLASS_PATTERNS:
        if p.match(name):
            return "blocked"
    for p in _BLOCKED_MAPPING_PATTERNS:
        if p.match(name):
            return "blocked"
    return "allowed"


@pytest.mark.unit
def test_no_l2_cross_imports():
    """L2 엔진 간 상호 import — 심볼명 패턴으로 결과/매핑만 차단, 수학 primitive 는 허용.

    옵션 C 하이브리드 (2026-04-27): 절대 금지 룰 → 결과 dataclass/매핑 함수만 차단.
    수학 함수 (solve*/calc*/apply*/classify*) 는 자유 import — 결과 결합은 review 일임.
    """
    root = Path(__file__).resolve().parent.parent.parent / "src" / "dartlab"
    engines = ["analysis", "credit", "quant", "macro"]
    blocked_imports = []
    for src_engine in engines:
        src_dir = root / src_engine
        if not src_dir.exists():
            continue
        for py in src_dir.rglob("*.py"):
            try:
                tree = ast.parse(py.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom) or not node.module:
                    continue
                mod = node.module
                for other in engines:
                    if other == src_engine:
                        continue
                    if mod != f"dartlab.{other}" and not mod.startswith(f"dartlab.{other}."):
                        continue
                    # 모듈 자체 import (`from dartlab.credit import X`) 는 X 명으로 판정
                    for alias in node.names:
                        sym = alias.name
                        if _classifySymbol(sym) != "blocked":
                            continue
                        blocked_imports.append((src_engine, other, str(py.relative_to(root)), node.lineno, sym))
    assert not blocked_imports, "L2 cross-import 결과/매핑 심볼 차단:\n" + "\n".join(
        f"  {sl}/{p}:{ln} → {oth}.{s}" for sl, oth, p, ln, s in blocked_imports
    )
