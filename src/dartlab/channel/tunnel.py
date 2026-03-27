"""Pluggable Tunnel Backends.

지원 백엔드:
- cloudflare (pycloudflared) — 기본, 무료+무제한, 계정 불필요
- ngrok (pyngrok) — SSE 완벽, authtoken 필요
- ssh (localhost.run) — 설치 0, SSH 기반
"""

from __future__ import annotations

import atexit
import logging
import re
import subprocess
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class TunnelProvider(ABC):
    """터널 백엔드 추상 클래스."""

    name: str = "base"

    @abstractmethod
    def start(self, port: int) -> str:
        """터널을 시작하고 public URL을 반환한다."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """터널을 정리한다."""
        ...


class NgrokTunnel(TunnelProvider):
    """pyngrok 기반 ngrok 터널."""

    name = "ngrok"

    def __init__(self):
        self._public_url: str | None = None

    def start(self, port: int) -> str:
        try:
            from pyngrok import ngrok
        except ImportError as exc:
            raise RuntimeError(
                "ngrok 터널을 사용하려면 pyngrok을 설치하세요:\n  uv pip install dartlab[channel-ngrok]"
            ) from exc

        try:
            tunnel = ngrok.connect(port, "http")
        except Exception as exc:
            msg = str(exc)
            if "ERR_NGROK_4018" in msg or "authtoken" in msg.lower():
                raise RuntimeError(
                    "ngrok은 authtoken이 필요합니다.\n"
                    "  1) https://dashboard.ngrok.com 에서 무료 계정 생성\n"
                    "  2) ngrok config add-authtoken <YOUR_TOKEN>\n"
                    "  또는 --tunnel cloudflare 를 사용하세요 (무료, 계정 불필요)"
                ) from exc
            raise RuntimeError(f"ngrok 터널 시작 실패: {msg}") from exc
        self._public_url = str(tunnel.public_url)
        # HTTPS 강제
        if self._public_url.startswith("http://"):
            self._public_url = self._public_url.replace("http://", "https://", 1)

        atexit.register(self.stop)
        return self._public_url

    def stop(self) -> None:
        try:
            from pyngrok import ngrok

            ngrok.disconnect(self._public_url)
            ngrok.kill()
        except (ImportError, OSError) as e:
            logger.debug("ngrok cleanup: %s", e)


class CloudflareTunnel(TunnelProvider):
    """pycloudflared 기반 Cloudflare 터널.

    주의: Quick Tunnel은 SSE 버퍼링 이슈가 있음.
    등록된 Cloudflare 계정 사용 권장.
    """

    name = "cloudflare"

    def __init__(self):
        self._process = None

    def _ensure_pycloudflared(self) -> None:
        """pycloudflared가 없으면 사용자에게 설치 여부를 묻는다."""
        try:
            import pycloudflared  # noqa: F401
        except ImportError:
            import sys

            print("\n  Cloudflare 터널에 pycloudflared 패키지가 필요합니다.")
            try:
                answer = input("  지금 설치하시겠습니까? [Y/n] ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = "n"

            if answer in ("", "y", "yes", "ㅛ"):
                print("  설치 중...", flush=True)
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "pycloudflared>=0.3"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    raise RuntimeError(
                        "pycloudflared 설치 실패.\n"
                        "  수동 설치: uv pip install pycloudflared\n"
                        "  또는: uv pip install dartlab[channel]"
                    )
                print("  설치 완료!\n", flush=True)
            else:
                raise RuntimeError(
                    "설치를 취소했습니다.\n"
                    "  수동 설치: uv pip install pycloudflared\n"
                    "  또는: uv pip install dartlab[channel]"
                )

    def start(self, port: int) -> str:
        self._ensure_pycloudflared()

        from pycloudflared import try_cloudflare

        info = try_cloudflare(port=port)
        url = info.tunnel
        if not url.startswith("http"):
            url = f"https://{url}"
        logger.warning(
            "Cloudflare Quick Tunnel 사용 중 — SSE 스트리밍 버퍼링 이슈가 있을 수 있습니다.\n"
            "  실시간 스트리밍이 필요하면 --tunnel ngrok 을 사용하세요."
        )
        return url

    def stop(self) -> None:
        pass  # pycloudflared가 프로세스 관리


class SshTunnel(TunnelProvider):
    """SSH 기반 터널 (localhost.run).

    설치 불필요, SSH만 있으면 동작.
    E2E 암호화 — 제공자가 트래픽을 볼 수 없음.
    """

    name = "ssh"

    def __init__(self):
        self._process = None

    def start(self, port: int) -> str:
        try:
            self._process = subprocess.Popen(
                [
                    "ssh",
                    "-o",
                    "StrictHostKeyChecking=no",
                    "-R",
                    f"80:localhost:{port}",
                    "nokey@localhost.run",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            import time

            for _ in range(15):
                time.sleep(1)
                if self._process.stdout:
                    line = self._process.stdout.readline()
                    match = re.search(r"(https://[a-z0-9]+\.lhr\.life)", line)
                    if not match:
                        match = re.search(r"(https://\S+\.localhost\.run\S*)", line)
                    if match:
                        url = match.group(1).rstrip()
                        atexit.register(self.stop)
                        return url
            raise RuntimeError("localhost.run에서 URL을 가져올 수 없습니다.")
        except FileNotFoundError as exc:
            raise RuntimeError("SSH 터널을 사용하려면 ssh 클라이언트가 필요합니다.") from exc

    def stop(self) -> None:
        if self._process:
            self._process.terminate()
            self._process = None


# ---------------------------------------------------------------------------
# 팩토리
# ---------------------------------------------------------------------------

_PROVIDERS: dict[str, type[TunnelProvider]] = {
    "ngrok": NgrokTunnel,
    "cloudflare": CloudflareTunnel,
    "ssh": SshTunnel,
}


def create_tunnel(backend: str = "cloudflare") -> TunnelProvider:
    """터널 백엔드를 생성한다.

    Args:
        backend: "ngrok" | "cloudflare" | "ssh"
    """
    cls = _PROVIDERS.get(backend)
    if cls is None:
        available = ", ".join(_PROVIDERS)
        raise ValueError(f"알 수 없는 터널 백엔드: {backend!r}. 사용 가능: {available}")
    return cls()
