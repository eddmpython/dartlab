"""guide 연동 헬퍼 — 모든 사용자 접점에서 이 모듈만 호출하면 guide가 개입한다.

병목 전략: 815개 에러 지점을 하나하나 수정하는 대신,
5개 사용자 접점(CLI, Server, Python API, MCP, AI Runtime)에서
이 헬퍼를 호출하면 모든 내부 에러에 guide 안내가 자동 포함된다.
"""

from __future__ import annotations


def wrapError(error: Exception, *, feature: str | None = None, stockCode: str | None = None) -> str:
    """에러 → guide 안내 포함 메시지. 모든 접점에서 이것만 호출.

    Args:
        error: 발생한 예외.
        feature: "data", "ai", "finance" 등. None이면 자동 추론.
        stockCode: 관련 종목코드 (있으면 readiness에 전달).

    Returns:
        원본 에러 메시지 + guide 안내가 합쳐진 문자열.
    """
    try:
        from dartlab.guide import guide

        resolvedFeature = feature or inferFeature(error)
        kwargs = {}
        if stockCode:
            kwargs["stockCode"] = stockCode
        guideMsg = guide.handleError(error, feature=resolvedFeature)
        if guideMsg and guideMsg != f"오류: {error}":
            return f"{error}\n\n{guideMsg}"
    except ImportError:
        pass
    return str(error)


def inferFeature(error: Exception) -> str | None:
    """에러 타입/메시지에서 관련 feature 자동 추론."""
    errStr = str(error).lower()

    # AI/provider 관련
    if any(kw in errStr for kw in ("api_key", "apikey", "provider", "oauth", "openai", "gemini", "ollama")):
        return "ai"

    # 재무 데이터 관련
    if any(kw in errStr for kw in ("finance", "parquet", "재무", "financial")):
        return "finance"

    # 데이터 부재
    if isinstance(error, FileNotFoundError):
        return "data"

    # 네트워크
    if isinstance(error, (ConnectionError, TimeoutError)):
        return "ai"

    return None


def cliCompany(codeOrName: str):
    """CLI용 Company 생성 + guide 에러 래핑.

    모든 CLI command에서 Company() 생성 시 이 함수를 사용하면
    에러 발생 시 guide 안내가 자동 포함된 CLIError가 발생한다.

    Args:
        codeOrName: 종목코드 또는 회사명.

    Returns:
        Company 인스턴스.

    Raises:
        CLIError: Company 생성 실패 시 guide 안내 포함.
    """
    import dartlab

    try:
        return dartlab.Company(codeOrName)
    except (ValueError, FileNotFoundError, OSError, RuntimeError) as exc:
        from dartlab.cli.services.errors import CLIError

        raise CLIError(wrapError(exc, feature="data", stockCode=codeOrName)) from exc
