"""DartLab 메시징 채널 어댑터.

지원 플랫폼:
- telegram (python-telegram-bot) — polling 기반, 공개 URL 불필요
- slack (slack-bolt) — Socket Mode, 공개 URL 불필요
- discord (discord.py) — Gateway, slash command
"""

from __future__ import annotations

from dartlab.channel.adapters.base import ChannelAdapter

_ADAPTER_MAP: dict[str, str] = {
    "telegram": "dartlab.channel.adapters.telegram",
    "slack": "dartlab.channel.adapters.slack",
    "discord": "dartlab.channel.adapters.discord",
}


def create_adapter(platform: str, **kwargs) -> ChannelAdapter:
    """플랫폼별 어댑터를 생성한다.

    Args:
        platform: "telegram" | "slack" | "discord"
        **kwargs: 플랫폼별 인자 (token 등)
    """
    module_path = _ADAPTER_MAP.get(platform)
    if module_path is None:
        available = ", ".join(_ADAPTER_MAP)
        raise ValueError(f"알 수 없는 채널: {platform!r}. 사용 가능: {available}")

    import importlib

    mod = importlib.import_module(module_path)
    return mod.create(**kwargs)


__all__ = ["ChannelAdapter", "create_adapter"]
