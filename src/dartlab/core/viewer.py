"""공시 뷰어 공통 런처. DART/EDGAR Company.view()에서 사용."""

from __future__ import annotations


def launchViewer(companyId: str, *, port: int = 8400) -> None:
    """브라우저에서 공시 뷰어를 엽니다.

    로컬 서버를 자동으로 띄우고 브라우저를 열어서
    해당 회사의 전체 공시를 탐색할 수 있습니다.

    Args:
        companyId: 종목코드(DART) 또는 ticker(EDGAR).
        port: 로컬 서버 포트.
    """
    import socket
    import threading
    import time
    import webbrowser

    def _is_port_in_use(p: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", p)) == 0

    if not _is_port_in_use(port):

        def _run() -> None:
            import uvicorn

            uvicorn.run("dartlab.server:app", host="127.0.0.1", port=port, log_level="warning")

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        for _ in range(30):
            if _is_port_in_use(port):
                break
            time.sleep(0.1)

    url = f"http://127.0.0.1:{port}/?company={companyId}"
    webbrowser.open(url)
