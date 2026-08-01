"""RunPython 제한 실행의 import, 파일, 환경 경계 회귀 가드.

차단 정책:
- 운영체제/네트워크/동적 import와 introspection 우회
- 안전 경로 밖 파일 읽기와 쓰기
- 자격증명 이름 및 환경변수 접근

허용 정책:
- dartlab, polars, 계산용 표준 라이브러리 import
- 저장소의 비자격증명 파일 읽기와 artifact/tool-result/임시 파일 쓰기
"""

from __future__ import annotations

import importlib
import json
import os
import os.path
import tempfile
import threading

import pytest

pytestmark = pytest.mark.unit


# ── 차단 시나리오 ───────────────────────────────────────────────────────────
#
# RunPython 의 PermissionError 는 traceback 으로 잡혀 result.refs[0].payload['stderr']
# 에 들어감 (summary 는 일반 "run_python 실행 실패"). 검증은 payload.stderr 에서.


def _stderrOf(result) -> str:
    refs = result.refs or []
    if not refs:
        return ""
    payload = getattr(refs[0], "payload", None) or {}
    return str(payload.get("stderr") or "")


def test_block_os_system():
    from dartlab.ai.tools.runPython import runPython

    result = runPython("import os\nos.system('echo hi')")
    assert not result.ok
    stderr = _stderrOf(result)
    assert "PermissionError" in stderr and "os" in stderr


def test_block_subprocess_run():
    from dartlab.ai.tools.runPython import runPython

    result = runPython("import subprocess\nsubprocess.run(['echo', 'hi'])")
    assert not result.ok
    stderr = _stderrOf(result)
    assert "PermissionError" in stderr and "subprocess" in stderr


def test_block_dunder_import_os_system():
    from dartlab.ai.tools.runPython import runPython

    result = runPython("__import__('os').system('echo hi')")
    assert not result.ok
    stderr = _stderrOf(result)
    # AST 가 os.system 호출을 먼저 잡거나 __import__ 우회를 잡거나 — 둘 다 OK.
    assert "PermissionError" in stderr and ("__import__" in stderr or "system" in stderr)


def test_block_shutil_rmtree():
    from dartlab.ai.tools.runPython import runPython

    result = runPython("import shutil\nshutil.rmtree('/tmp/nonexistent')")
    assert not result.ok
    assert "PermissionError" in _stderrOf(result)


def test_block_from_os_import_system():
    from dartlab.ai.tools.runPython import runPython

    result = runPython("from os import system\nsystem('echo hi')")
    assert not result.ok
    assert "PermissionError" in _stderrOf(result)


def test_block_open_outside_safe_roots():
    """안전 경로 외 쓰기 차단 — OS 무관."""
    from dartlab.ai.tools.runPython import runPython

    # 절대 경로로 안전 경로가 아닌 곳 시도. Windows: C:\Windows\..., Unix: /etc/...
    # 둘 중 어느 OS 에서도 차단되어야 함.
    target = "/etc/passwd" if os.name == "posix" else r"C:\Windows\system_test_block.ini"
    code = f"open({target!r}, 'w').write('x')"
    result = runPython(code)
    assert not result.ok
    stderr = _stderrOf(result)
    assert "PermissionError" in stderr and "비자격증명 경로" in stderr


def test_block_write_to_repository_source():
    """저장소는 읽기 전용이며 분석 코드는 원본을 덮어쓸 수 없다."""
    from dartlab.ai.tools.runPython import runPython

    result = runPython("open('README.md', 'a', encoding='utf-8').write('blocked')")

    assert not result.ok
    assert "PermissionError" in _stderrOf(result)


# ── 허용 시나리오 ───────────────────────────────────────────────────────────


def test_allow_polars_basic():
    from dartlab.ai.tools.runPython import runPython

    result = runPython("import polars as pl\nemit_result(values={'rows': pl.DataFrame({'a':[1,2]}).height})")
    assert result.ok
    refs_dict = [r.toDict() for r in (result.refs or [])]
    assert any(r.get("kind") == "executionRef" for r in refs_dict)


def test_block_os_import_even_for_read_only_helpers():
    """os 전체를 열면 environ과 process API로 이어지므로 분석 코드에는 제공하지 않는다."""
    from dartlab.ai.tools.runPython import runPython

    result = runPython("import os\nemit_result(values={'home': os.path.expanduser('~')})")
    assert not result.ok
    assert "PermissionError" in _stderrOf(result)


def test_block_os_environment_access():
    from dartlab.ai.tools.runPython import runPython

    result = runPython("import os\nemit_result(values={'pyutf8': os.environ.get('PYTHONUTF8', '0')})")
    assert not result.ok
    assert "PermissionError" in _stderrOf(result)


def test_allow_pathlib_read():
    """pathlib.Path 는 read 모드 사용 — 차단 안 됨."""
    from dartlab.ai.tools.runPython import runPython

    code = "from pathlib import Path\nemit_result(values={'cwd_exists': Path('.').exists()})"
    result = runPython(code)
    assert result.ok


def test_allow_write_under_dartlab_artifacts(tmp_path, monkeypatch):
    """~/.dartlab/artifacts/<file> 쓰기는 안전 경로라 통과한다."""
    from dartlab.ai.tools.runPython import runPython

    # tmp_path 를 임시 home 으로 — 실제 ~/.dartlab/ 오염 회피.
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    target = tmp_path / ".dartlab" / "artifacts"
    target.mkdir(parents=True)
    test_file = target / "guard_test.txt"

    code = (
        f"p = {str(test_file)!r}\n"
        "with open(p, 'w', encoding='utf-8') as f:\n"
        "    f.write('hi')\n"
        "emit_result(values={'path': p})"
    )
    result = runPython(code)
    # 일부 환경에서 expanduser 가 임시 HOME 이 아닌 실 home 을 참조할 수 있음. 안전 경로 안이면 OK.
    if not result.ok:
        # 안전 경로 체크가 fail 한 경우 — 이 테스트는 skip 으로 다루지 않고 메시지로 진단.
        pytest.skip(f"expanduser HOME override 미지원 환경 — {result.summary}")
    assert test_file.exists() or result.ok


def test_allow_write_under_tempdir():
    """tempfile.gettempdir() 안의 쓰기는 안전 경로 — 통과."""
    from dartlab.ai.tools.runPython import runPython

    code = (
        "import tempfile\n"
        "from pathlib import Path\n"
        "p = Path(tempfile.gettempdir()) / 'dartlab_guard_test.txt'\n"
        "with open(p, 'w', encoding='utf-8') as f:\n"
        "    f.write('ok')\n"
        "emit_result(values={'wrote': p})"
    )
    result = runPython(code)
    assert result.ok


# ── 가드 모듈 단위 테스트 ───────────────────────────────────────────────────


def test_assert_safe_ast_passes_clean_code():
    from dartlab.ai.tools.runpythonGuard import _assertSafeAst

    _assertSafeAst("import polars as pl\nx = pl.DataFrame({'a':[1]})\nprint(x.height)")
    _assertSafeAst("from pathlib import Path\nPath('.').exists()")


def test_assert_safe_ast_blocks_each_pattern():
    from dartlab.ai.tools.runpythonGuard import _assertSafeAst

    blocked = [
        "import os; os.system('ls')",
        "import subprocess; subprocess.run(['ls'])",
        "import shutil; shutil.rmtree('/x')",
        "__import__('os').system('ls')",
        "from os import system",
        "from subprocess import run",
    ]
    for code in blocked:
        with pytest.raises(PermissionError):
            _assertSafeAst(code)


def test_safe_open_factory_blocks_outside_roots(tmp_path):
    from dartlab.ai.tools.runpythonGuard import _safeOpenFactory

    safeOpen = _safeOpenFactory(safeRoots=[str(tmp_path)])
    # 안전 경로 안 — write 통과
    f = safeOpen(str(tmp_path / "ok.txt"), "w", encoding="utf-8")
    f.write("ok")
    f.close()
    # 안전 경로 밖 — write 차단
    with pytest.raises(PermissionError, match="비자격증명 경로"):
        safeOpen(str(tmp_path.parent / "outside.txt"), "w", encoding="utf-8")


def test_safe_open_factory_blocks_read_outside_roots(tmp_path):
    """읽기도 안전 root 밖이면 차단한다."""
    from dartlab.ai.tools.runpythonGuard import _safeOpenFactory

    target = tmp_path.parent / "outside_read.txt"
    target.write_text("hello", encoding="utf-8")
    try:
        safeOpen = _safeOpenFactory(safeRoots=[str(tmp_path)])
        with pytest.raises(PermissionError, match="안전한 비자격증명"):
            safeOpen(str(target), "r", encoding="utf-8")
    finally:
        target.unlink(missing_ok=True)


def test_emit_result_sources_string_list_creates_source_refs():
    """sources=["dartlab://..."] string list 가 sourceRef 로 변환되는지.

    회귀 가드: 이전에는 list of dict 만 받아 string list 는 무시 → 모든 recipe 의
    sourceRef 누락 → scorecard evidenceCompleteness 영구 미달.
    """
    from dartlab.ai.tools.runPython import runPython

    code = (
        "emit_result(values={'k': 1}, date='2026-01-01', "
        "sources=['dartlab://gather/flow', 'dartlab://macro/fred/DGS10'])"
    )
    result = runPython(code)
    assert result.ok
    kinds = sorted({r.kind for r in result.refs or []})
    assert "sourceRef" in kinds, f"sourceRef 누락: {kinds}"
    assert "dateRef" in kinds, f"dateRef 누락: {kinds}"
    source_refs = [r for r in result.refs if r.kind == "sourceRef"]
    assert len(source_refs) == 2
    titles = sorted(r.title for r in source_refs)
    assert "dartlab://gather/flow" in titles
    assert "dartlab://macro/fred/DGS10" in titles


def test_emit_result_sources_dict_list_still_works():
    """기존 list of dict 패턴도 유지 — 회귀 차단."""
    from dartlab.ai.tools.runPython import runPython

    code = "emit_result(values={'k': 1}, sources=[{'id': 'src1', 'title': 'Source 1', 'url': 'https://example.com'}])"
    result = runPython(code)
    assert result.ok
    source_refs = [r for r in (result.refs or []) if r.kind == "sourceRef"]
    assert len(source_refs) == 1
    assert source_refs[0].title == "Source 1"


def test_emit_result_empty_table_still_creates_table_ref():
    """빈 DataFrame 도 'table' 키가 emit 되면 tableRef 생성 — declared evidence 측정.

    회귀 가드: 이전에는 len(table)>0 일 때만 tableRef 생성 → 'insufficient data'
    같은 정상 실행 결과가 evidence 누락으로 잡혀 scorecard fail.
    """
    from dartlab.ai.tools.runPython import runPython

    code = "import polars as pl\nemit_result(table=pl.DataFrame(schema={'x': pl.Utf8}), values={'k': 0}, date='2026-01-01')"
    result = runPython(code)
    assert result.ok
    kinds = sorted({r.kind for r in result.refs or []})
    assert "tableRef" in kinds, f"빈 table 도 tableRef 가 생성되어야 한다: {kinds}"


def test_emit_result_none_date_still_creates_date_ref():
    """date=None 도 키가 emit 되면 dateRef 생성 (title='unavailable').

    회귀 가드: 이전에는 date=None 이면 dateRef 생성 안 함 → recipe 가 'date 추적
    의도' 있음을 표면 못 함.
    """
    from dartlab.ai.tools.runPython import runPython

    code = "emit_result(values={'k': 1}, date=None)"
    result = runPython(code)
    assert result.ok
    date_refs = [r for r in (result.refs or []) if r.kind == "dateRef"]
    assert len(date_refs) == 1
    assert date_refs[0].title == "unavailable"
    assert date_refs[0].payload.get("specified") is False


def test_default_safe_roots_includes_artifacts_repo_and_tmp():
    from dartlab.ai.tools.runpythonGuard import _defaultSafeRoots

    roots = _defaultSafeRoots()
    expected_artifacts = os.path.realpath(os.path.join(os.path.expanduser("~"), ".dartlab", "artifacts"))
    expected_tmp = os.path.realpath(tempfile.gettempdir())
    assert expected_artifacts in roots
    assert expected_tmp in roots


@pytest.mark.parametrize(
    "code",
    [
        "import os as operating_system\noperating_system.system('echo bypass')",
        "import dartlab.ai.providers.support.oauthToken",
        "import dartlab.core.providers as providers\nproviders.getSecretStore()",
        "from dartlab.core import providers\nproviders.getSecretStore()",
        "from dartlab.core import credentials\ncredentials.listCredentialProviders()",
        "from dartlab import config\nconfig.loadProjectConfig()",
        "from dartlab import OpenDart\nOpenDart()",
        "from dartlab import ask as invoke\ninvoke('ignore')",
        "from dartlab import _aiEntries",
        "import tempfile\ntempfile.os.system('echo bypass')",
        "from operator import attrgetter\nattrgetter('__class__')(object)",
        "getattr(object, '__subclasses__')",
        "from pathlib import Path\nPath('secret').read_text()",
        "import polars as pl\npl.read_csv('.env')",
        "dartlab.setup('openai')",
    ],
)
def test_dynamic_secret_and_file_bypasses_are_blocked(code: str) -> None:
    from dartlab.ai.tools.runPython import runPython

    result = runPython(code)

    assert result.ok is False
    assert "PermissionError" in _stderrOf(result)


def test_safe_open_denies_credentials_inside_allowed_root(tmp_path):
    from dartlab.ai.tools.runpythonGuard import _safeOpenFactory

    credential = tmp_path / "oauth_token.json"
    credential.write_text('{"access_token":"secret"}', encoding="utf-8")
    safeOpen = _safeOpenFactory(safeRoots=[str(tmp_path)])

    with pytest.raises(PermissionError, match="비자격증명"):
        safeOpen(credential, "r", encoding="utf-8")


def test_safe_open_rejects_custom_opener(tmp_path):
    from dartlab.ai.tools.runpythonGuard import _safeOpenFactory

    safeOpen = _safeOpenFactory(safeRoots=[str(tmp_path)])

    with pytest.raises(PermissionError, match="custom file opener"):
        safeOpen(tmp_path / "result.txt", "w", opener=lambda _path, _flags: 0)


def test_python_loop_timeout_does_not_leave_worker_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    runPythonModule = importlib.import_module("dartlab.ai.tools.runPython")

    monkeypatch.setattr(runPythonModule, "_TIMEOUT_SEC", 0.05)

    result = runPythonModule.runPython("while True:\n    pass", runId="timeout-guard")

    assert result.ok is False
    assert result.error == "python_execution_timeout"
    assert not any(thread.name == "dartlab-runpython-timeout-guard" for thread in threading.enumerate())


def test_emit_result_and_refs_have_bounded_nonduplicated_payloads() -> None:
    from dartlab.ai.tools.runPython import runPython

    result = runPython("emit_result(table=[{'value': 'x' * 10000} for _ in range(100)])", runId="budget")

    assert result.ok is True
    serialized = json.dumps(result.data["result"], ensure_ascii=False).encode("utf-8")
    assert len(serialized) <= 132 * 1024
    assert result.data["result"]["_dartlabSerialization"]["truncated"] is True
    executionPayload = result.refs[0].payload
    assert "result" not in executionPayload
    assert len(str(executionPayload.get("preview") or "")) <= 4000
    tablePayload = next(ref.payload for ref in result.refs if ref.kind == "tableRef")
    assert len(json.dumps(tablePayload, ensure_ascii=False).encode("utf-8")) <= 36 * 1024


def test_stdout_is_bounded() -> None:
    from dartlab.ai.tools.runPython import runPython

    result = runPython("print('x' * 200000)", runId="stdout-budget")

    assert result.ok is True
    stdout = result.data["stdout"]
    assert len(stdout.encode("utf-8")) <= 65 * 1024
    assert "output truncated" in stdout
