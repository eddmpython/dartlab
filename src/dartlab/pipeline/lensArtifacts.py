"""공개 터미널용 Lens Product JSON artifact 발행 경계.

계산은 각 분석 엔진과 Story collector가 담당한다. 이 모듈은 공개 bundle에서
내부 원본 결과를 제거하고 JSON 직렬화 가능성을 검증한 뒤 원자적으로 저장한다.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_SAFE_TARGET = re.compile(r"^[A-Za-z0-9._-]+$")
_ENGINES = ("analysis", "credit", "industry", "quant", "macro")


def buildLensArtifact(company: Any, *, refresh: bool = False) -> dict[str, Any]:
    """한 회사의 공개 Lens Product bundle을 계산하고 검증한다."""
    from dartlab.story.lensProducts import collectLensProducts, publicLensBundle

    bundle = publicLensBundle(collectLensProducts(company, refresh=refresh))
    if bundle is None:
        raise ValueError("공개 lens bundle을 만들 수 없습니다.")
    _validatePublicBundle(bundle)
    return bundle


def _validatePublicBundle(bundle: dict[str, Any]) -> None:
    from dartlab.synth.lensContract import validatePublicLensBundle

    validatePublicLensBundle(bundle)

    target = str(bundle.get("target") or "").strip()
    if not target or not _SAFE_TARGET.fullmatch(target):
        raise ValueError(f"안전하지 않은 lens artifact target: {target!r}")

    # default 변환을 허용하지 않는다. 엔진 결과에 DataFrame, 날짜 객체, NaN 등이
    # 새어 나오면 발행 시점에 즉시 실패시켜 Python과 브라우저 계약 드리프트를 막는다.
    json.dumps(bundle, ensure_ascii=False, allow_nan=False)


def unavailableLensArtifact(target: str, *, market: str, reason: str) -> dict[str, Any]:
    """회사 계산 실패도 공개 표면에서 사라지지 않도록 결손 bundle을 만든다."""
    from dartlab.story.lensTensions import classifyLensTensions

    normalizedTarget = str(target).strip()
    bundle = {
        "schemaVersion": 1,
        "target": normalizedTarget,
        "market": str(market).upper(),
        "engines": list(_ENGINES),
        "products": {},
        "tensions": classifyLensTensions({}),
        "statusCounts": {},
        "gaps": [
            {
                "engine": engine,
                "status": "blocked",
                "reason": str(reason)[:240],
            }
            for engine in _ENGINES
        ],
        "noComposite": True,
    }
    _validatePublicBundle(bundle)
    return bundle


def _writeBundle(bundle: dict[str, Any], outputDir: str | Path) -> Path:
    _validatePublicBundle(bundle)

    output = Path(outputDir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    target = str(bundle["target"])
    destination = (output / f"{target}.json").resolve()
    if destination.parent != output:
        raise ValueError("lens artifact 출력 경로가 outputDir 밖을 가리킵니다.")

    payload = json.dumps(bundle, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(destination)
    return destination


def writeLensArtifact(
    company: Any,
    outputDir: str | Path,
    *,
    refresh: bool = False,
    minProducts: int = 1,
) -> Path:
    """공개 bundle을 ``{outputDir}/{target}.json``에 원자적으로 기록한다."""
    if minProducts < 0 or minProducts > 5:
        raise ValueError("minProducts는 0 이상 5 이하여야 합니다.")

    bundle = buildLensArtifact(company, refresh=refresh)
    productCount = len(bundle["products"])
    if productCount < minProducts:
        raise RuntimeError(f"발행 가능한 lens product가 {productCount}개로 하한 {minProducts}개보다 적습니다.")

    return _writeBundle(bundle, outputDir)


def writeUnavailableLensArtifact(
    target: str,
    outputDir: str | Path,
    *,
    market: str,
    reason: str,
) -> Path:
    """제품 계산 실패 회사를 다섯 결손 렌즈로 원자 저장한다."""
    return _writeBundle(unavailableLensArtifact(target, market=market, reason=reason), outputDir)


__all__ = [
    "buildLensArtifact",
    "unavailableLensArtifact",
    "writeLensArtifact",
    "writeUnavailableLensArtifact",
]
