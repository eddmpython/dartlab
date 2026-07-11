"""dartlab.webapi.browserApi 구조 검사 (dartlab import 없이 AST).

browser-as-server 의 데이터 라우터가 (1) 전 엔드포인트 async (pyodide 스레드 금지) (2) fastapi
top-level import 없음 (브라우저 wheel 은 fastapi 제외, buildBrowserApi 안에서 lazy) 를 지킨다.
무거운 dartlab import 없이 정적으로 본다.
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.audit.browserApiAsync import findSyncEndpoints

_SRC = Path(__file__).resolve().parents[2] / "src" / "dartlab" / "webapi" / "browserApi.py"


def test_allEndpointsAreAsync() -> None:
    """route 데코레이터 붙은 sync def 가 하나도 없어야 한다(G1)."""
    assert findSyncEndpoints(_SRC.read_text(encoding="utf-8")) == []


def test_fastapiIsLazyImported() -> None:
    """fastapi 는 top-level 이 아니라 함수 안에서만 import (브라우저 wheel 안전)."""
    tree = ast.parse(_SRC.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", "") or ""
            names = [a.name for a in node.names]
            assert "fastapi" not in mod and "fastapi" not in names, "fastapi top-level import 금지"


def test_buildBrowserApiExists() -> None:
    """공개 진입점 buildBrowserApi 가 있다."""
    tree = ast.parse(_SRC.read_text(encoding="utf-8"))
    funcs = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    assert "buildBrowserApi" in funcs
