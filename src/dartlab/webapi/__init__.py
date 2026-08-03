"""dartlab 브라우저 HTTP 서빙 계층 (browser-as-server SSOT).

브라우저(pyodide) 안에서 dartlab 의 공개 계약을 FastAPI(ASGI)로 노출한다. Service Worker 가
페이지 fetch 를 이 앱으로 넘기면 백엔드(:8400) 없이 브라우저가 dartlab 서버가 된다.

`dartlab.server`(:8400, 395 엔드포인트, sync)와 별개다. 그쪽은 fastapi 를 eager import 해서
브라우저 wheel(fastapi 제외)에서 못 부른다. 여기는 fastapi 를 `buildBrowserApi()` 안에서 lazy
import 하므로 wheel import 시점엔 fastapi 가 없어도 안전하다.

실행 SSOT는 pyodide 커널 하나이고, 노트북 execute와 이 데이터 API가 그 한 커널을 공유한다.
"""

from __future__ import annotations

from dartlab.webapi.browserApi import buildBrowserApi

__all__ = ["buildBrowserApi"]
