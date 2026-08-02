"""DartLab 설치형 agent runtime 공개 표면."""

from __future__ import annotations

from dataclasses import dataclass

from .kernel import ask


@dataclass(frozen=True)
class RuntimeConfig:
    """프로세스 안에서 선호하는 설치형 agent runtime."""

    runtimeId: str | None = None

    @property
    def provider(self) -> str | None:
        """Sig: provider() -> str | None.

        Args: 없음.
        Returns: 호환 이름으로 runtimeId를 반환한다.
        Example: `config.provider == config.runtimeId`.
        """
        return self.runtimeId


ProviderConfig = RuntimeConfig
_CONFIG = RuntimeConfig()


def configure(runtimeId: str | None = None, **kwargs) -> RuntimeConfig:
    """Sig: configure(runtimeId=None, **kwargs) -> RuntimeConfig.

    Args: runtimeId 또는 호환 provider 값은 codex, claude, cline 중 하나다.
    Returns: 프로세스 선호 RuntimeConfig다.
    Raises: ValueError if a direct-model provider is requested.
    Example: `dartlab.llm.configure(runtimeId="cline")`.
    """
    global _CONFIG
    selected = runtimeId or kwargs.get("provider")
    if selected not in {None, "codex", "claude", "cline"}:
        raise ValueError("DartLab은 direct-model provider를 지원하지 않습니다. 설치형 agent runtime을 선택하세요")
    _CONFIG = RuntimeConfig(selected)
    return _CONFIG


def getConfig(runtimeId: str | None = None, **kwargs) -> RuntimeConfig:
    """Sig: getConfig(runtimeId=None, **kwargs) -> RuntimeConfig.

    Args: 선택적 runtimeId 또는 호환 provider 값이다.
    Returns: 명시 값 또는 현재 프로세스 선호 설정이다.
    Raises: ValueError if an unknown runtime is requested.
    Example: `config = getConfig()`.
    """
    selected = runtimeId or kwargs.get("provider")
    if selected:
        return configure(selected)
    return _CONFIG


def templates(name: str | None = None):
    """Sig: templates(name=None) -> dict[str, str] | str | None.

    Args: 선택적 template 이름이다.
    Returns: 런타임 분석 template 설명이다.
    Example: `templates("dartlab-agent-runtime")`.
    """
    items = {"dartlab-agent-runtime": "설치형 agent CLI와 DartLab MCP를 결합한 근거 기반 분석"}
    return items.get(name) if name else items


def saveTemplate(name: str, *, content: str | None = None, file: str | None = None) -> dict[str, str | None]:
    """Sig: saveTemplate(name, *, content=None, file=None) -> dict[str, str | None].

    Args: 이름과 선택적 내용 또는 파일이다.
    Returns: 호환 확인 payload다.
    Example: `saveTemplate("mine", content="...")`.
    """
    return {"name": name, "content": content, "file": file}


__all__ = ["ProviderConfig", "RuntimeConfig", "ask", "configure", "getConfig", "saveTemplate", "templates"]
