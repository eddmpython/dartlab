"""Codex CLI introspection and execution helpers."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Any

_CODEX_CONFIG_PATH = Path.home() / ".codex" / "config.toml"
_DEFAULT_CODEX_MODELS = [
    "gpt-5.4",
    "gpt-5.3",
    "gpt-5.3-codex",
    "gpt-5.2",
    "gpt-5.2-codex",
    "gpt-5.1",
    "gpt-5.1-codex",
    "gpt-5.1-codex-mini",
    "o3",
    "o4-mini",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
]
_CODING_KEYWORDS = (
    "코드",
    "코딩",
    "구현",
    "수정",
    "패치",
    "리팩터링",
    "버그",
    "테스트",
    "파일",
    "함수",
    "클래스",
    "모듈",
    "컴포넌트",
    "diff",
    "patch",
    "fix",
    "implement",
    "refactor",
    "edit",
    "write code",
    "update file",
)
_CODE_FILE_HINT = re.compile(r"\.(py|svelte|js|ts|tsx|jsx|json|toml|md|yml|yaml|css|html)\b", re.IGNORECASE)


def codex_path() -> str | None:
    """Resolve Codex CLI executable."""
    return shutil.which("codex")


def _run_codex_meta_command(*args: str, timeout: int = 10) -> tuple[int, str, str] | None:
    """Run a short Codex CLI command and capture text output."""
    exe = codex_path()
    if not exe:
        return None
    try:
        result = subprocess.run(
            [exe, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeDecodeError):
        return None
    return result.returncode, (result.stdout or "").strip(), (result.stderr or "").strip()


def load_codex_config() -> dict[str, Any]:
    """Load ~/.codex/config.toml if present."""
    if not _CODEX_CONFIG_PATH.exists():
        return {}
    try:
        with _CODEX_CONFIG_PATH.open("rb") as fh:
            data = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def get_codex_configured_model() -> str | None:
    """Return model configured in Codex CLI config, if any."""
    data = load_codex_config()
    root_model = data.get("model")
    if isinstance(root_model, str) and root_model.strip():
        return root_model.strip()

    profile_name = data.get("profile") or data.get("default_profile")
    profiles = data.get("profiles")
    if isinstance(profile_name, str) and isinstance(profiles, dict):
        profile = profiles.get(profile_name)
        if isinstance(profile, dict):
            profile_model = profile.get("model")
            if isinstance(profile_model, str) and profile_model.strip():
                return profile_model.strip()

    if isinstance(profiles, dict):
        for profile in profiles.values():
            if isinstance(profile, dict):
                profile_model = profile.get("model")
                if isinstance(profile_model, str) and profile_model.strip():
                    return profile_model.strip()

    return None


def get_codex_model_catalog() -> list[str]:
    """Build a model catalog from Codex config + ChatGPT/Codex provider fallback."""
    models: list[str] = []
    configured = get_codex_configured_model()
    if configured:
        models.append(configured)

    models.extend(_DEFAULT_CODEX_MODELS)

    if not models:
        models.append("gpt-4.1")

    seen: set[str] = set()
    unique: list[str] = []
    for model in models:
        if model and model not in seen:
            seen.add(model)
            unique.append(model)
    return unique


def _extract_commands(help_text: str) -> list[str]:
    """Parse command names from help output."""
    help_text = help_text if isinstance(help_text, str) else str(help_text)
    commands: list[str] = []
    in_commands = False
    for line in help_text.splitlines():
        stripped = line.rstrip()
        if stripped.startswith("Commands:"):
            in_commands = True
            continue
        if not in_commands:
            continue
        if stripped.startswith("Arguments:") or stripped.startswith("Options:"):
            break
        if not line.startswith("  "):
            continue
        token = stripped.split()[0]
        if token:
            commands.append(token)
    return commands


def _extract_sandbox_modes(help_text: str) -> list[str]:
    """Parse sandbox modes from help output."""
    help_text = help_text if isinstance(help_text, str) else str(help_text)
    match = re.search(r"possible values:\s*([^\]]+)", help_text)
    if not match:
        return []
    values = match.group(1)
    return [value.strip() for value in values.split(",") if value.strip()]


def _parse_login_status(stdout: str, stderr: str, returncode: int) -> tuple[bool, str | None, str | None]:
    """Parse `codex login status` output into authentication metadata."""
    text = (stdout or stderr or "").strip()
    lowered = text.lower()

    if returncode != 0:
        return False, None, text or None

    authenticated = "logged in" in lowered or "authenticated" in lowered
    auth_mode = None
    if "chatgpt" in lowered:
        auth_mode = "chatgpt"
    elif "api key" in lowered or "api-key" in lowered:
        auth_mode = "api_key"

    return authenticated, auth_mode, text or None


def inspect_codex_cli() -> dict[str, Any]:
    """Inspect installed Codex CLI features from live help output."""
    result: dict[str, Any] = {
        "installed": False,
        "version": None,
        "configuredModel": get_codex_configured_model(),
        "authenticated": False,
        "authMode": None,
        "loginStatus": None,
        "commands": [],
        "execCommands": [],
        "sandboxModes": [],
        "supportsLogin": False,
        "supportsLogout": False,
        "supportsJson": False,
        "supportsWorkspaceWrite": False,
        "supportsDangerFullAccess": False,
        "supportsMcp": False,
        "supportsReview": False,
        "supportsApply": False,
    }

    version_info = _run_codex_meta_command("--version")
    if version_info is None:
        return result

    returncode, stdout, _stderr = version_info
    if returncode != 0:
        return result

    result["installed"] = True
    result["version"] = stdout or None

    root_help = _run_codex_meta_command("--help")
    if root_help is not None and root_help[0] == 0:
        help_text = root_help[1]
        commands = _extract_commands(help_text)
        result["commands"] = commands
        result["supportsLogin"] = "login" in commands
        result["supportsLogout"] = "logout" in commands
        result["supportsMcp"] = "mcp" in commands
        result["supportsReview"] = "review" in commands
        result["supportsApply"] = "apply" in commands

    login_status = _run_codex_meta_command("login", "status")
    if login_status is not None:
        authenticated, auth_mode, status_text = _parse_login_status(*login_status[1:], login_status[0])
        result["authenticated"] = authenticated
        result["authMode"] = auth_mode
        result["loginStatus"] = status_text

    exec_help = _run_codex_meta_command("exec", "--help")
    if exec_help is not None and exec_help[0] == 0:
        help_text = exec_help[1]
        result["execCommands"] = _extract_commands(help_text)
        sandbox_modes = _extract_sandbox_modes(help_text)
        result["sandboxModes"] = sandbox_modes
        result["supportsWorkspaceWrite"] = "workspace-write" in sandbox_modes
        result["supportsDangerFullAccess"] = "danger-full-access" in sandbox_modes
        result["supportsJson"] = "--json" in help_text

    return result


def logout_codex_cli(timeout: int = 15) -> None:
    """Remove stored Codex CLI authentication."""
    info = inspect_codex_cli()
    if not info.get("installed"):
        raise FileNotFoundError("Codex CLI가 설치되어 있지 않습니다.")

    result = _run_codex_meta_command("logout", timeout=timeout)
    if result is None:
        raise RuntimeError("Codex CLI 로그아웃 명령을 실행할 수 없습니다.")

    returncode, _stdout, stderr = result
    if returncode != 0:
        raise RuntimeError(stderr or "Codex CLI 로그아웃에 실패했습니다.")


def infer_codex_sandbox(messages: list[dict[str, str]], override: str | None = None) -> str:
    """Choose a Codex sandbox based on explicit override, env, and user intent."""
    info = inspect_codex_cli()
    sandbox_modes = set(info.get("sandboxModes") or [])

    requested = override or os.environ.get("DARTLAB_CODEX_SANDBOX")
    if requested and (not sandbox_modes or requested in sandbox_modes):
        return requested

    user_text = "\n".join(m.get("content", "") for m in messages if m.get("role") == "user")
    if _looks_like_code_task(user_text) and "workspace-write" in sandbox_modes:
        return "workspace-write"
    return "read-only"


def _looks_like_code_task(text: str) -> bool:
    """Heuristic for repo-editing intent."""
    lowered = text.lower()
    if any(keyword in lowered for keyword in _CODING_KEYWORDS):
        return True
    return bool(_CODE_FILE_HINT.search(text))


def build_codex_exec_command(*, model: str | None = None, sandbox: str = "read-only") -> list[str]:
    """Build a non-interactive Codex exec command."""
    cmd = ["codex", "exec", "-", "--json", "--skip-git-repo-check", "--sandbox", sandbox]
    if model:
        cmd.extend(["--model", model])
    return cmd


def parse_codex_jsonl(output: str) -> tuple[str, dict[str, int] | None]:
    """Extract final answer and usage from Codex JSONL output."""
    answer = ""
    usage: dict[str, int] = {}

    for line in output.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type", "")
        if event_type == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message":
                answer = item.get("text", "")
        elif event_type == "turn.completed":
            turn_usage = event.get("usage", {})
            if turn_usage:
                usage["prompt_tokens"] = turn_usage.get("input_tokens")
                usage["completion_tokens"] = turn_usage.get("output_tokens")
                prompt_tokens = usage.get("prompt_tokens") or 0
                completion_tokens = usage.get("completion_tokens") or 0
                if prompt_tokens or completion_tokens:
                    usage["total_tokens"] = prompt_tokens + completion_tokens

    return answer, usage or None


def run_codex_exec(
    prompt: str,
    *,
    model: str | None = None,
    sandbox: str = "read-only",
    cwd: str | None = None,
    timeout: int = 300,
) -> tuple[str, dict[str, int] | None]:
    """Run Codex CLI in non-interactive JSON mode."""
    cmd = build_codex_exec_command(model=model, sandbox=sandbox)

    try:
        result = subprocess.run(
            cmd,
            input=prompt.encode("utf-8"),
            capture_output=True,
            timeout=timeout,
            shell=False,
            cwd=cwd,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(f"Codex CLI 응답 시간 초과 ({timeout}초)") from exc

    if result.returncode != 0:
        raw_err = result.stderr or b""
        stderr = raw_err.decode("utf-8", errors="replace").strip() if isinstance(raw_err, bytes) else raw_err.strip()
        raise RuntimeError(f"Codex CLI 오류 (exit {result.returncode}):\n{stderr}")

    raw_out = result.stdout or b""
    stdout = raw_out.decode("utf-8", errors="replace") if isinstance(raw_out, bytes) else raw_out
    answer, usage = parse_codex_jsonl(stdout)
    if not answer:
        raise RuntimeError("Codex CLI에서 응답을 추출할 수 없습니다.")
    return answer, usage
