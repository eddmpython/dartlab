"""Universe live layout fixture와 browser reference를 같은 local origin에서 제공한다.

Capabilities
    Static visual reference와 실행 시점 bounded scene fixture JSON을 HTTP로 제공한다.

AIContext
    AI 역할: 긴 fixture를 browser CLI 인자에 복제하지 않고 live projection 결과를 전달한다.

Guide
    browserLayoutAudit.ps1 전용 임시 서버이며 production runtime 또는 public API가 아니다.

When
    U0-V02 Chrome, Firefox, WebKit replay audit를 실행할 때 사용한다.

How
    시작 시 fixture를 한 번 고정하고 static file 및 fixture endpoint를 같은 snapshot으로 제공한다.

Requires
    liveLayoutFixture module과 localhost port bind 권한이 필요하다.

Raises
    OSError: Public artifact load 또는 localhost bind가 실패했을 때 발생한다.
    ValueError: Live bounded fixture 계약이 깨졌을 때 발생한다.

Example
    ``uv run python -X utf8 -m tests._attempts.dartlabUniverse.visual.liveLayoutServer``

See Also
    tests/_attempts/dartlabUniverse/visual/browserLayoutAudit.ps1

결과
    layoutReference.html과 /liveLayoutFixtures.json을 같은 origin에서 제공한다.
"""

from __future__ import annotations

import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from tests._attempts.dartlabUniverse.visual.liveLayoutFixture import loadLiveLayoutFixtures


class LayoutRequestHandler(SimpleHTTPRequestHandler):
    """고정된 live fixture endpoint를 추가한 static file handler."""

    fixturePayload = b"[]"

    def do_GET(self) -> None:
        """Fixture endpoint 또는 static reference 요청을 처리한다.

        Capabilities
            Fixture JSON에는 no-store header를 붙이고 나머지는 static handler에 위임한다.
        AIContext
            AI 역할: 시작 시 고정된 fixture payload만 반환한다.
        Args
            없음.
        Returns
            없음.
        Guide
            Endpoint 확장은 browser audit에 필요한 최소 범위로 제한한다.
        When
            Local audit browser가 HTTP GET을 보낼 때 호출된다.
        How
            URL path exact match 뒤 bytes payload를 기록한다.
        Requires
            main이 fixturePayload와 static directory를 초기화해야 한다.
        Raises
            OSError: Client socket 기록이 실패했을 때 발생한다.
        Example
            ``GET /liveLayoutFixtures.json``
        See Also
            :func:`main`.
        """

        if urlsplit(self.path).path == "/liveLayoutFixtures.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(self.fixturePayload)))
            self.end_headers()
            self.wfile.write(self.fixturePayload)
            return
        super().do_GET()

    def log_message(self, format: str, *args: object) -> None:
        """Browser replay 중 기본 access log를 억제한다.

        Capabilities
            반복 reload가 stdout 결과를 오염하지 않게 한다.
        AIContext
            AI 역할: audit measurement와 HTTP access noise를 분리한다.
        Args
            format: Base handler log format.
            args: Format에 대응하는 값.
        Returns
            없음.
        Guide
            실패 진단이 필요하면 명시적 audit log를 별도로 추가한다.
        When
            Base HTTP handler가 access log를 남기려 할 때 호출된다.
        How
            입력을 소비하지 않고 즉시 반환한다.
        Requires
            SimpleHTTPRequestHandler override 계약이 필요하다.
        Raises
            예외를 발생시키지 않는다.
        Example
            ``handler.log_message("%s", "request")``
        See Also
            :meth:`do_GET`.
        """

        return


def main() -> int:
    """Live layout browser audit server를 실행한다.

    Capabilities
        한 snapshot의 fixture와 static reference를 localhost에서 제공한다.
    AIContext
        AI 역할: production service가 아닌 bounded audit server만 연다.
    Args
        없음.
    Returns
        Server가 정상 종료되면 0.
    Guide
        Caller는 audit 종료 시 process를 반드시 종료한다.
    When
        browserLayoutAudit.ps1이 cross-browser replay를 시작할 때 실행한다.
    How
        Fixture를 한 번 load한 뒤 ThreadingHTTPServer를 bind한다.
    Requires
        Public artifact 접근과 사용 가능한 localhost port가 필요하다.
    Raises
        OSError: Artifact load 또는 port bind가 실패했을 때 발생한다.
        ValueError: Fixture projection 계약이 깨졌을 때 발생한다.
    Example
        ``python -m tests._attempts.dartlabUniverse.visual.liveLayoutServer --port 8765``
    See Also
        tests/_attempts/dartlabUniverse/visual/browserLayoutAudit.ps1
    """

    parser = argparse.ArgumentParser(description="Serve Universe live layout browser audit")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    LayoutRequestHandler.fixturePayload = json.dumps(
        loadLiveLayoutFixtures(),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    visualRoot = Path(__file__).resolve().parent
    handler = partial(LayoutRequestHandler, directory=str(visualRoot))
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
