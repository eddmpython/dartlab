"""AI 코드 실행 stdout에서 VizSpec 마커 추출.

``emit_chart()`` / ``emit_diagram()``이 stdout에 삽입한 마커를
파싱하여 VizSpec dict 리스트를 반환하고, 마커를 텍스트에서 제거한다.

마커 형식::

    <!--DARTLAB_VIZ:{json}:VIZ_END-->
"""

from __future__ import annotations

import json
import re

_MARKER_RE = re.compile(r"<!--DARTLAB_VIZ:(.*?):VIZ_END-->", re.DOTALL)


def extract_viz_specs(stdout: str) -> tuple[str, list[dict]]:
    """stdout에서 VizSpec 마커를 추출하고 텍스트에서 제거.

    Args:
        stdout: 코드 실행 결과 문자열.

    Returns:
        (마커 제거된 stdout, VizSpec dict 리스트).
        파싱 실패한 마커는 무시한다.
    """
    specs: list[dict] = []

    for match in _MARKER_RE.finditer(stdout):
        raw = match.group(1).strip()
        try:
            spec = json.loads(raw)
            if isinstance(spec, dict):
                specs.append(spec)
        except (json.JSONDecodeError, TypeError):
            continue

    cleaned = _MARKER_RE.sub("", stdout).strip()
    return cleaned, specs
