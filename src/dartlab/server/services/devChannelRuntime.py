from __future__ import annotations

import base64
import io
import subprocess
import threading
from typing import Any

from dartlab.channel import DevTunnelSetupError, setupDevtunnel
from dartlab.core.logger import getLogger

logger = getLogger(__name__)

# 셋업 예외 문자열 (subprocess 출력·로컬 경로 포함) 은 응답에 싣지 않는다. 상세는 서버 로그에만 남기고
# 응답에는 예외와 무관한 고정 안내만 둔다 (수동 설치 경로와 Linux 자동 설치 동의 방법 유지).
_START_FAILED_MESSAGE = (
    "Dev Channel을 시작하지 못했습니다. 서버 콘솔 로그를 확인하세요. "
    "devtunnel 수동 설치: https://learn.microsoft.com/azure/developer/dev-tunnels/get-started "
    "(Linux 자동 설치는 DARTLAB_DEVTUNNEL_AUTOINSTALL=1 환경변수로 동의한 뒤 다시 시도)"
)


class DevChannelRuntime:
    """DevChannelRuntime — TODO 한국어 클래스 설명."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._url: str | None = None
        self._process: subprocess.Popen | None = None
        self._error: str | None = None

    def status(self) -> dict[str, Any]:
        """status — TODO 한국어 동작 설명."""
        with self._lock:
            running = self._process is not None and self._process.poll() is None
            if not running:
                self._process = None
            url = self._url if running else None
            return self._buildStatus(url=url, running=running, error=self._error)

    def start(self, *, port: int, autoYes: bool = True) -> dict[str, Any]:
        """DevTunnels 채널을 시작하고 현재 상태를 반환한다.

        Args:
            port: 터널로 노출할 로컬 Web UI 포트.
            autoYes: devtunnel 설치·로그인 확인 질문에 자동 동의할지 여부.

        Returns:
            dict. kind/label/running/url/qrDataUrl/error. 셋업 실패 시 running=False 이고
            error 는 예외와 무관한 고정 안내 문구다 (예외 상세는 서버 로그에만 남긴다).

        Raises:
            DevTunnelSetupError 는 raise 하지 않고 상태 dict 의 error 로 바꾼다. 그 밖의 예외는
            그대로 전파한다.

        Example:
            >>> status = devChannelRuntime.start(port=8400)
            >>> sorted(status)[:3]
            ['error', 'kind', 'label']
        """
        with self._lock:
            if self._process is not None and self._process.poll() is None and self._url:
                return self._buildStatus(url=self._url, running=True, error=None)
            self._error = None

        try:
            url, process = setupDevtunnel(port=port, autoYes=autoYes)
        except DevTunnelSetupError as exc:
            logger.warning("Dev Channel 시작 실패: %s", exc)
            with self._lock:
                self._error = _START_FAILED_MESSAGE
            return self._buildStatus(url=None, running=False, error=_START_FAILED_MESSAGE)

        with self._lock:
            self._url = url
            self._process = process
            self._error = None
            return self._buildStatus(url=url, running=True, error=None)

    def stop(self) -> dict[str, Any]:
        """stop — TODO 한국어 동작 설명."""
        with self._lock:
            process = self._process
            self._process = None
            self._url = None
            self._error = None
        if process is not None and process.poll() is None:
            process.terminate()
        return self._buildStatus(url=None, running=False, error=None)

    def shutdown(self) -> None:
        """shutdown — TODO 한국어 동작 설명."""
        self.stop()

    def _buildStatus(self, *, url: str | None, running: bool, error: str | None) -> dict[str, Any]:
        qr_data_url = _qrDataUrl(url) if url else None
        return {
            "kind": "devtunnel",
            "label": "Dev Channel",
            "running": running,
            "url": url,
            "qrDataUrl": qr_data_url,
            "error": error,
        }


def _qrDataUrl(url: str | None) -> str | None:
    if not url:
        return None
    try:
        import qrcode
        from qrcode.image.svg import SvgPathImage

        qr = qrcode.QRCode(border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(image_factory=SvgPathImage)
        buf = io.BytesIO()
        img.save(buf)
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"
    except Exception:
        return None


devChannelRuntime = DevChannelRuntime()
