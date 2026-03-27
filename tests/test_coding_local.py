"""LocalPythonBackend 안전성 + 기능 테스트."""

import pytest

pytestmark = pytest.mark.unit

from dartlab.ai.tools.coding import LocalPythonBackend, _validateCode

# ══════════════════════════════════════
# AST 안전성 검증
# ══════════════════════════════════════


def test_validateCode_safe():
    code = "import math\nprint(math.sqrt(16))"
    assert _validateCode(code) == []


def test_validateCode_forbidden_import():
    code = "import os\nos.system('rm -rf /')"
    violations = _validateCode(code)
    assert len(violations) >= 1
    assert any("os" in v for v in violations)


def test_validateCode_forbidden_subprocess():
    code = "import subprocess\nsubprocess.run(['ls'])"
    violations = _validateCode(code)
    assert any("subprocess" in v for v in violations)


def test_validateCode_forbidden_eval():
    code = "eval('1+1')"
    violations = _validateCode(code)
    assert any("eval" in v for v in violations)


def test_validateCode_forbidden_exec():
    code = "exec('print(1)')"
    violations = _validateCode(code)
    assert any("exec" in v for v in violations)


def test_validateCode_forbidden_open():
    code = "f = open('/etc/passwd')"
    violations = _validateCode(code)
    assert any("open" in v for v in violations)


def test_validateCode_forbidden_network():
    code = "import requests\nrequests.get('http://evil.com')"
    violations = _validateCode(code)
    assert any("requests" in v for v in violations)


def test_validateCode_forbidden_dunder_import():
    code = "__import__('os')"
    violations = _validateCode(code)
    assert any("__import__" in v for v in violations)


def test_validateCode_allowed_modules():
    code = "import json\nimport datetime\nimport collections\nprint('ok')"
    assert _validateCode(code) == []


def test_validateCode_polars_allowed():
    code = "import polars as pl\ndf = pl.DataFrame({'a': [1, 2, 3]})\nprint(df)"
    assert _validateCode(code) == []


def test_validateCode_numpy_allowed():
    code = "import numpy as np\narr = np.array([1, 2, 3])\nprint(arr.mean())"
    assert _validateCode(code) == []


def test_validateCode_syntax_error():
    code = "def foo(\n"
    violations = _validateCode(code)
    assert len(violations) == 1
    assert "구문 오류" in violations[0]


def test_validateCode_from_import_forbidden():
    code = "from socket import socket"
    violations = _validateCode(code)
    assert any("socket" in v for v in violations)


def test_validateCode_unknown_module():
    code = "import boto3"
    violations = _validateCode(code)
    assert any("boto3" in v for v in violations)


# ══════════════════════════════════════
# LocalPythonBackend 실행
# ══════════════════════════════════════


def test_backend_inspect():
    backend = LocalPythonBackend()
    info = backend.inspect()
    assert info["available"] is True
    assert info["name"] == "local_python"
    assert "polars" in info["allowedModules"]


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


def test_backend_forbidden_code_blocked():
    backend = LocalPythonBackend()
    result = backend.run_task("", code="import os\nos.system('echo hi')")
    assert "[보안 위반]" in result.answer


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
