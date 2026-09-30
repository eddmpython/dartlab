"""syncRecent.py 키 로테이션 로그 회귀.

GitHub Actions 는 secret 전체 문자열만 마스킹한다. 예전 로그는 한도 초과 시 키 앞 8 자를 찍어 공개 로그에
부분 비밀값이 남았다(CodeQL py/clear-text-logging-sensitive-data). 이제 키 순번만 찍는다.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_SCRIPT = Path(__file__).resolve().parents[2] / ".github" / "scripts" / "sync" / "syncRecent.py"
# 실제 키가 아닌 40 자 hex 더미 (DART 키 형식만 흉내).
_KEYS = [
    "3f9a1c7e5b2d8f4a6c0e9b1d7f3a5c8e2b4d6f0a",
    "9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d",
]


def _loadSyncRecent():
    spec = importlib.util.spec_from_file_location("syncRecentUnderTest", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _leaksKeyMaterial(text: str, key: str, window: int = 6) -> bool:
    """key 의 길이 window 이상 부분 문자열이 text 에 있으면 True."""
    return any(key[i : i + window] in text for i in range(len(key) - window + 1))


def test_key_rotation_log_prints_index_not_key(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """모든 키가 한도 초과여도 로그에는 키 #순번만 남고 키 문자열 조각은 없다."""
    import dartlab.core.dartClient as dartClientMod
    import dartlab.gather.dart.disclosure as gatherDisclosure
    from dartlab.core.dartClient import DartApiError

    triedKeys: list[str] = []

    def _fakeClient(apiKey: str | None = None, **_kwargs) -> str | None:
        return apiKey

    def _limitExceeded(client, **_kwargs):
        triedKeys.append(client)
        raise DartApiError("020", "사용한도를 초과하였습니다.")

    monkeypatch.setattr(dartClientMod, "DartClient", _fakeClient)
    monkeypatch.setattr(gatherDisclosure, "listFilings", _limitExceeded)

    syncRecent = _loadSyncRecent()
    with pytest.raises(RuntimeError, match="기존 pending 보존"):
        syncRecent._discoverNewFilings(",".join(_KEYS), 7, str(tmp_path))
    out = capsys.readouterr().out

    assert triedKeys == _KEYS
    assert "[syncRecent] API 한도 초과 (키 #1), 다음 키 시도" in out
    assert "[syncRecent] API 한도 초과 (키 #2), 다음 키 시도" in out
    for key in _KEYS:
        assert not _leaksKeyMaterial(out, key)


def test_sync_recent_source_has_no_key_slice_logging() -> None:
    """스크립트 소스에 키 slice 를 문자열에 끼워 찍는 코드가 없다."""
    source = _SCRIPT.read_text(encoding="utf-8")

    assert "apiKey[:" not in source
    assert "{apiKey" not in source
