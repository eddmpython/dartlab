"""Company에서 Macro 전파 제품으로 넘길 교차 렌즈 문맥 조립기.

Macro 엔진은 Company나 Analysis를 직접 import하지 않는다. 공개 Company facade가
이미 계산한 Industry 위치와 Analysis 대표 근거를 이 모듈에서 얇게 직렬화한다.
"""

from __future__ import annotations

from typing import Any


def buildMacroCompanyContext(company: Any) -> dict[str, Any]:
    """회사 가치사슬 위치와 대표 재무 근거를 Macro 전파 입력으로 변환한다."""
    stockCode = str(getattr(company, "stockCode", "") or "unknown")
    sectorKey = None
    industryEvidence = None
    companyEvidence: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []

    try:
        industry = company.industry()
        if isinstance(industry, dict):
            sectorKey = industry.get("chainId") or industry.get("industry")
            if sectorKey:
                industryEvidence = {
                    "id": "industry.chainPosition",
                    "label": "가치사슬 위치",
                    "value": {
                        "chainId": sectorKey,
                        "stage": industry.get("stage"),
                        "stageLabel": industry.get("stageLabel") or industry.get("stageName"),
                    },
                    "status": "derived",
                    "sourceRef": f"dartlab://industry/{stockCode}/position",
                }
        if not sectorKey:
            gaps.append(
                {
                    "id": "macro.company.sectorKey",
                    "status": "missing",
                    "reason": "검증된 가치사슬 산업 위치를 찾지 못했습니다.",
                    "sourceRef": f"dartlab://industry/{stockCode}",
                }
            )
    except (KeyError, ValueError, TypeError, AttributeError, RuntimeError, OSError) as exc:
        gaps.append(
            {
                "id": "macro.company.industry",
                "status": "missing",
                "reason": f"산업 위치 계산이 완료되지 않았습니다 ({type(exc).__name__}).",
                "sourceRef": f"dartlab://industry/{stockCode}",
            }
        )

    try:
        analysis = company.analysis("종합평가")
        product = analysis.get("product") if isinstance(analysis, dict) else None
        drivers = product.get("drivers") if isinstance(product, dict) else None
        if isinstance(drivers, list):
            for row in drivers:
                if not isinstance(row, dict) or not row.get("label"):
                    continue
                companyEvidence.append(
                    {
                        "id": f"analysis.{row.get('id') or 'driver'}",
                        "label": str(row["label"]),
                        "value": row.get("value"),
                        "unit": row.get("unit"),
                        "period": row.get("period"),
                        "direction": row.get("direction"),
                        "status": "derived",
                        "sourceRef": f"dartlab://analysis/{stockCode}/product/drivers/{row.get('id') or 'driver'}",
                    }
                )
        if not companyEvidence:
            gaps.append(
                {
                    "id": "macro.company.financialEvidence",
                    "status": "missing",
                    "reason": "Macro 전달경로와 대조할 대표 재무 근거가 없습니다.",
                    "sourceRef": f"dartlab://analysis/{stockCode}/product",
                }
            )
    except (KeyError, ValueError, TypeError, AttributeError, RuntimeError, OSError) as exc:
        gaps.append(
            {
                "id": "macro.company.analysis",
                "status": "missing",
                "reason": f"대표 재무 근거 계산이 완료되지 않았습니다 ({type(exc).__name__}).",
                "sourceRef": f"dartlab://analysis/{stockCode}",
            }
        )

    if industryEvidence is not None:
        companyEvidence.append(industryEvidence)
    return {
        "stockCode": stockCode,
        "sectorKey": sectorKey,
        "companyEvidence": companyEvidence,
        "contextGaps": gaps,
    }


__all__ = ["buildMacroCompanyContext"]
