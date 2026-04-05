"""코드 생성기 — 질문에 대한 올바른 dartlab 코드를 생성.

2가지 소스:
1. 라우터 규칙 기반 (즉시, 정확)
2. Ollama fallback (규칙 미매칭 시)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)


def generateCode(item: dict) -> dict:
    """질문 항목에 대한 코드를 생성.

    Args:
        item: {"question": str, "tool": str, "group": str|None, "axis": str|None,
               "stock_code": str|None, "corp_name": str|None}

    Returns:
        item에 "code" 필드가 추가된 dict
    """
    from dartlab.ai.selfai.router.engine import RouteResult, _code_for_route

    tool = item.get("tool", "")
    group = item.get("group")
    axis = item.get("axis")
    stock_code = item.get("stock_code")

    # 라우터 코드 템플릿 생성
    r = RouteResult(
        tool=tool,
        group=group,
        axis=axis,
        needs_company=stock_code is not None,
        confidence=0.9,
        source="apigen",
    )
    code = _code_for_route(r, stock_code)

    if code:
        item["code"] = code
        return item

    # 규칙에서 코드 생성 안 되면 Ollama fallback
    code = _ollamaCodeGen(item)
    if code:
        item["code"] = code
    else:
        item["code"] = ""

    return item


def _ollamaCodeGen(item: dict) -> str | None:
    """Ollama로 코드 생성 (규칙 미매칭 시 fallback)."""
    try:
        import urllib.request

        question = item.get("question", "")
        stock_code = item.get("stock_code", "")

        prompt = (
            "dartlab 금융분석 플랫폼의 Python 코드를 생성하라. "
            "코드만 출력하고 설명은 하지 마라.\n\n"
            "사용 가능한 도구:\n"
            '- c.analysis("financial", "축") — 재무분석 (축: 수익성, 성장성, 안정성 등)\n'
            '- c.credit(detail=True) — 신용등급\n'
            '- dartlab.scan("축") — 시장비교\n'
            '- dartlab.macro("축") — 매크로 (축: 사이클, 금리, 자산, 심리, 유동성)\n'
            '- c.gather("price") — 주가\n'
            "- c.quant() — 기술적분석\n"
            '- dartlab.search("키워드") — 공시검색\n\n'
        )
        if stock_code:
            prompt += f'c = dartlab.Company("{stock_code}") 가 이미 생성되어 있다.\n\n'
        prompt += f"질문: {question}\n코드:"

        payload = json.dumps(
            {
                "model": "qwen3:1.7b",
                "messages": [
                    {"role": "system", "content": "Python 코드만 출력하라. 설명 없이."},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "think": False,
                "options": {"temperature": 0.1, "num_predict": 512},
            }
        ).encode()

        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            content = data.get("message", {}).get("content", "")

        # ```python ... ``` 블록 추출
        import re

        match = re.search(r"```python\s*\n(.*?)```", content, re.DOTALL)
        if match:
            return match.group(1).strip()

        # 코드블록 없으면 전체 텍스트를 코드로
        if content.strip():
            return content.strip()

        return None

    except (OSError, json.JSONDecodeError, TimeoutError):
        return None


def generateBatch(
    items: list[dict],
    output_path: Path | str | None = None,
) -> list[dict]:
    """배치 코드 생성.

    Args:
        items: question_gen에서 생성된 질문 목록
        output_path: 결과 저장 경로 (None이면 저장 안 함)

    Returns:
        코드가 추가된 항목 목록
    """
    results = []
    for i, item in enumerate(items):
        result = generateCode(item)
        if result.get("code"):
            results.append(result)

        if (i + 1) % 50 == 0:
            log.info("코드 생성 진행: %d/%d (유효 %d)", i + 1, len(items), len(results))

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    return results
