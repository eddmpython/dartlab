"""note 택소노미 생성기 — 전 corpus XBRL 학습 → (scope, 제목) → 표준 NT_ 코드 (noteTaxonomyData.py).

``dechunkNotes`` 가 옛 주석 덩어리를 분해할 때 쓰는 뼈대(``noteTaxonomyData.NOTE_TAXONOMY``)를 생성한다.
2023+ 보고서의 XBRL-태깅 주석행(disclosureKey=``NT_D######``, xbrlClass not null)에서 ``(scope, 정규화제목)
→ disclosureKey`` 빈도를 전 종목 집계 → **dominant**(최빈 비율 ≥ ``dominanceRatio``) 제목만 채택해
한 제목이 여러 코드로 갈리는 false-merge(추상 제목 '회계정책'·'기타금융자산' 류)를 제외한다. cross-company
학습이라 자기는 XBRL 안 해도 남의 XBRL 에서 표준코드를 받는다.

생성물 SSOT — ``spineData`` 와 같은 패턴(순수 .py, git 추적). 사람 미수정, 생성기로만 갱신.

재생성: ``python -X utf8 -m dartlab.providers.dart.panel.build --noteTaxonomy``.

LLM Specifications:
    AntiPatterns:
        - per-title 의미 hardcode 금지 — 정부 XBRL 태깅 빈도에서 학습.
        - 모호 제목(무지배 코드)에 임의 코드 부여 금지 — dominanceRatio 미달은 제외(narrative 유지).
        - parquet 저장 금지 — 순수 .py.
    OutputSchema:
        - ``buildNoteTaxonomy(*, panelBaseDir, minFreq, dominanceRatio) -> dict[str, str]``.
        - ``renderModule(taxonomy) -> str`` / ``buildAndWrite(*, outModulePath, ...) -> dict``.
    Prerequisites:
        - data/dart/panel/{code}.parquet (period>=2023 필터) (XBRL itemized 주석행). polars.
    Freshness:
        - corpus 확대·정밀화 시 재생성 + 전수 재빌드.
    Dataflow:
        - parquet glob → (scope, norm제목)→Counter[NT_] → dominant 채택 → 모듈 직렬화.
    TargetMarkets:
        - KR (DART).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

import polars as pl

import dartlab.config as _cfg

from ..mapper import normalizeTitle as _norm  # 제목 정규화 단일 SSOT (build 검출·read 정렬 공유)
from .codegen import _ruffFormat  # 생성물 ruff 정본화 단일 SSOT (spineBuilder 와 공유)

_log = logging.getLogger(__name__)
_STD_RE = r"^NT_D\d+$"  # 정부표준 scope-strip 코드만 (회사확장 NT_C_U*/DI*/DS* 노이즈 제외)
_DEFAULT_MODULE = Path(__file__).resolve().parent / "noteTaxonomyData.py"


def buildNoteTaxonomy(
    *, panelBaseDir: Path | str | None = None, minFreq: int = 3, dominanceRatio: float = 0.8
) -> dict[str, str]:
    """전 corpus XBRL 주석행 → ``(scope|정규화제목) → dominant 표준 NT_ 코드`` 학습.

    Args:
        panelBaseDir: panel artifact base (기본 ``data/dart/panel``).
        minFreq: 제목별 총 출현 빈도 하한 (노이즈 컷).
        dominanceRatio: 최빈 코드 빈도/총빈도 하한 — 미달(모호) 제목은 제외(false-merge 회피).

    Returns:
        ``{"scope|정규화제목": "NT_D######"}`` (정렬). 모호·희소 제목 미포함.

    Raises:
        No explicit exceptions; unreadable parquet files are skipped.

    Example:
        >>> isinstance(buildNoteTaxonomy(panelBaseDir="missing"), dict)
        True
    """
    base = Path(panelBaseDir) if panelBaseDir else Path(_cfg.dataDir) / "dart" / "panel"
    files = sorted(base.glob("*.parquet"))  # flat: {code}.parquet (회사당 1파일, 전 period)
    agg: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for f in files:
        try:
            df = pl.read_parquet(str(f), columns=["disclosureKey", "xbrlClass", "blockLeaf", "period"])
        except (OSError, pl.exceptions.PolarsError):
            continue
        nt = df.filter(
            (pl.col("period") >= "2023")  # XBRL itemized 주석은 2023+ (옛 period-shard 202* glob 대체)
            & pl.col("disclosureKey").str.contains(_STD_RE)
            & pl.col("xbrlClass").is_not_null()
            & pl.col("blockLeaf").is_not_null()
        )
        for r in nt.iter_rows(named=True):
            t = _norm(r["blockLeaf"])
            if not (2 <= len(t) <= 20):
                continue
            scope = "standalone" if "_S" in (r["xbrlClass"] or "")[:5] else "consolidated"
            agg[f"{scope}|{t}"][r["disclosureKey"]] += 1

    taxonomy: dict[str, str] = {}
    for key, counter in agg.items():
        total = sum(counter.values())
        if total < minFreq:
            continue
        code, freq = max(counter.items(), key=lambda kv: kv[1])
        if freq / total >= dominanceRatio:  # dominant-only — 무지배(모호) 제목 제외
            taxonomy[key] = code
    return dict(sorted(taxonomy.items()))


def _q(s: str) -> str:
    """ruff 호환 double-quote 직렬화 (생성물 재포맷 0)."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def renderModule(taxonomy: dict[str, str]) -> str:
    """택소노미 dict → ``noteTaxonomyData.py`` 소스 문자열 (NOTE_TAXONOMY literal).

    Args:
        taxonomy: ``{"scope|title": "NT_D..."}`` mapping.

    Returns:
        Python module source with a ``NOTE_TAXONOMY`` literal.

    Raises:
        No explicit exceptions.

    Example:
        >>> "NOTE_TAXONOMY" in renderModule({})
        True
    """
    header = (
        '"""note 택소노미 SSOT — 정규화 (scope, 항목제목) → 정부 표준 NT_ 코드 (생성물).\n\n'
        "DART XBRL 주석 코드는 정부 표준이라 회사 무관(재고자산 연결=NT_D826380·별도=NT_D826385).\n"
        "옛 단일 주석 덩어리를 N.제목 헤더로 분해할 때 각 노트에 이 표준 코드를 부여 → 최근 NT_ 주석\n"
        "행과 같은 disclosureKey(rowIdentity)로 수평화 정합. dominant-only(모호 제목 제외)라 정밀.\n\n"
        "재생성: ``python -X utf8 -m dartlab.providers.dart.panel.build --noteTaxonomy``\n"
        "(``build.noteTaxonomy.buildNoteTaxonomy`` — 전 종목 2023+ XBRL 최빈·dominant).\n"
        '"""\n\n'
        "from __future__ import annotations\n\n"
        '# 키 = "scope|정규화제목" (공백·괄호·· 제거). 값 = NT_ canonicalKey.\n'
        "NOTE_TAXONOMY: dict[str, str] = {\n"
    )
    body = "".join(f"    {_q(k)}: {_q(v)},\n" for k, v in taxonomy.items())
    return header + body + "}\n"


def buildAndWrite(*, outModulePath: Path | str | None = None, verbose: bool = True, **kw) -> dict[str, int]:
    """택소노미 학습 → ``noteTaxonomyData.py`` write + ruff 정본화.

    Args:
        outModulePath: 생성 모듈 경로. None = ``build/noteTaxonomyData.py``.
        verbose: 진행 로그.
        **kw: ``buildNoteTaxonomy`` 인자(minFreq, dominanceRatio, panelBaseDir).

    Returns:
        ``{"entries": 항목수}``.

    Raises:
        OSError: output path cannot be written.

    Example:
        >>> callable(buildAndWrite)
        True
    """
    taxonomy = buildNoteTaxonomy(**kw)
    outPath = Path(outModulePath) if outModulePath else _DEFAULT_MODULE
    outPath.write_text(renderModule(taxonomy), encoding="utf-8")
    _ruffFormat(outPath)
    if verbose:
        _log.info("noteTaxonomy 생성: %s (entries=%d)", outPath, len(taxonomy))
    return {"entries": len(taxonomy)}
