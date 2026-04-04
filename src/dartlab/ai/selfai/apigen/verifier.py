"""Sandbox 검증기 — 생성된 코드를 DartlabCodeExecutor로 실행하여 검증.

APIGen 파이프라인의 핵심: 실행 성공한 코드만 학습 데이터로 채택.
이것이 "7B가 GPT-4를 이겼다"의 비밀 — 100% 검증된 데이터.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class VerifyResult:
    """검증 결과."""

    success: bool
    code: str
    output: str
    error: str | None = None


def verify(code: str, stock_code: str | None = None, timeout: int = 30) -> VerifyResult:
    """코드를 sandbox에서 실행하여 검증.

    Args:
        code: 실행할 Python 코드
        stock_code: 종목코드 (Company 생성용)
        timeout: 실행 타임아웃 (초)

    Returns:
        VerifyResult — success=True면 학습 데이터로 채택 가능
    """
    try:
        from dartlab.ai.tools.coding import DartlabCodeExecutor

        executor = DartlabCodeExecutor()
        result = executor.execute(code, stockCode=stock_code, timeout=timeout)

        is_error = any(kw in result for kw in ("Error", "Traceback", "실행 오류"))
        if is_error:
            return VerifyResult(success=False, code=code, output="", error=result)

        # 너무 짧은 출력은 의미 없음
        if len(result.strip()) < 10:
            return VerifyResult(success=False, code=code, output=result, error="출력 너무 짧음")

        return VerifyResult(success=True, code=code, output=result)

    except ImportError:
        return VerifyResult(success=False, code=code, output="", error="DartlabCodeExecutor 미사용")
    except (OSError, RuntimeError, TimeoutError) as e:
        return VerifyResult(success=False, code=code, output="", error=str(e))


def verifyBatch(
    items: list[dict],
    output_path: Path | str,
    *,
    timeout: int = 30,
    max_items: int | None = None,
) -> dict[str, int]:
    """질문 목록을 배치 검증하여 통과/실패로 분리 저장.

    Args:
        items: [{"question": str, "code": str, "stock_code": str|None, ...}]
        output_path: 결과 저장 경로 (verified.jsonl, failed.jsonl)
        timeout: 실행 타임아웃
        max_items: 최대 검증 수 (None이면 전부)

    Returns:
        {"verified": N, "failed": M, "total": T}
    """
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    verified_path = output_path / "verified.jsonl"
    failed_path = output_path / "failed.jsonl"

    verified = 0
    failed = 0
    total = min(len(items), max_items or len(items))

    with open(verified_path, "w", encoding="utf-8") as vf, \
         open(failed_path, "w", encoding="utf-8") as ff:

        for i, item in enumerate(items[:total]):
            if i > 0 and i % 50 == 0:
                log.info("검증 진행: %d/%d (verified=%d, failed=%d)", i, total, verified, failed)

            code = item.get("code", "")
            stock_code = item.get("stock_code")

            result = verify(code, stock_code=stock_code, timeout=timeout)

            record = {
                **item,
                "verified": result.success,
                "output": result.output[:2000] if result.success else "",
                "error": result.error or "",
            }

            if result.success:
                vf.write(json.dumps(record, ensure_ascii=False) + "\n")
                verified += 1
            else:
                ff.write(json.dumps(record, ensure_ascii=False) + "\n")
                failed += 1

    return {"verified": verified, "failed": failed, "total": total}
