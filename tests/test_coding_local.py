"""LocalPythonBackend 기능 테스트."""

import pytest

pytestmark = pytest.mark.unit

from dartlab.ai.tools.coding import LocalPythonBackend, _validateCode

# ══════════════════════════════════════
# 구문 검증 (보안 제한 없음 — 구문만 확인)
# ══════════════════════════════════════


def test_validateCode_safe():
    code = "import math\nprint(math.sqrt(16))"
    _validateCode(code)  # should not raise


def test_validateCode_any_module_allowed():
    """제한 없음 — 어떤 모듈이든 import 가능."""
    code = "import os\nimport requests\nimport subprocess"
    _validateCode(code)  # should not raise


def test_validateCode_syntax_error():
    code = "def foo(\n"
    with pytest.raises(SyntaxError):
        _validateCode(code)


# ══════════════════════════════════════
# LocalPythonBackend 실행
# ══════════════════════════════════════


def test_backend_inspect():
    backend = LocalPythonBackend()
    info = backend.inspect()
    assert info["available"] is True
    assert info["name"] == "local_python"
    assert info["restrictions"] == "none (unrestricted local execution)"


def test_backend_no_code():
    backend = LocalPythonBackend()
    result = backend.run_task("test prompt")
    assert "[오류]" in result.answer


def test_backend_simple_code():
    backend = LocalPythonBackend()
    result = backend.run_task("", code="print(2 + 3)")
    assert result.backend == "local_python"
    assert "5" in result.answer
    assert result.metadata["returncode"] == 0


def test_backend_math_code():
    backend = LocalPythonBackend()
    result = backend.run_task("", code="import math\nprint(math.pi)")
    assert "3.14" in result.answer


def test_backend_unrestricted_execution():
    """제한 없음 — os, open 등 자유 실행."""
    backend = LocalPythonBackend()
    result = backend.run_task("", code="import os\nprint(os.getcwd())")
    assert result.metadata["returncode"] == 0


def test_backend_timeout():
    backend = LocalPythonBackend(maxTimeout=10)
    result = backend.run_task("", code="import time\ntime.sleep(30)", timeout_seconds=2)
    assert "[시간 초과]" in result.answer


def test_backend_runtime_error():
    backend = LocalPythonBackend()
    result = backend.run_task("", code="1/0")
    assert "[실행 오류]" in result.answer
    assert "ZeroDivision" in result.answer


def test_backend_data_injection():
    backend = LocalPythonBackend()
    result = backend.run_task(
        "",
        code="print(data['name'])",
        dataJson='{"name": "Samsung"}',
    )
    assert "Samsung" in result.answer


def test_backend_multiline_output():
    backend = LocalPythonBackend()
    code = "for i in range(5):\n    print(f'line {i}')"
    result = backend.run_task("", code=code)
    assert "line 0" in result.answer
    assert "line 4" in result.answer
