"""GuideDesk — dartlab 안내 데스크.

모든 축이 이 객체만 호출하면 된다.
"""

from __future__ import annotations

from typing import Any

from dartlab.guide.readiness import (
    ReadinessResult,
    ReadyStatus,
    getChecker,
    listFeatures,
)
from dartlab.guide.credentials import CredentialManager, EnvironmentSnapshot
from dartlab.guide.search import searchCapabilities, formatSearchResults
from dartlab.guide.capabilities import build_capability_summary, get_capability_specs
from dartlab.guide.messaging import suggest


class GuideDesk:
    """dartlab 안내 데스크 — 단일 진입점.

    사용법::

        from dartlab.guide import guide

        guide.checkReady("finance", stockCode="005930")
        guide.whatCanIDo("재무 분석")
        guide.envSnapshot()
        guide.forAi("삼성전자 분석해줘")
    """

    def __init__(self) -> None:
        self.credentials = CredentialManager()

    # ── 1. 준비 상태 점검 ──

    def checkReady(self, feature: str, **kwargs: Any) -> ReadinessResult:
        """기능 준비 상태 점검.

        Args:
            feature: "data", "ai", "finance", "valuation", "dart_key" 등.
            **kwargs: 기능별 파라미터 (stockCode, provider 등).

        Returns:
            ReadinessResult — status, issues, guideText() 포함.
        """
        checker = getChecker(feature)
        if checker is None:
            return ReadinessResult(
                feature=feature,
                status=ReadyStatus.UNKNOWN,
                issues=[],
            )
        return checker(**kwargs)

    def checkReadyAll(self, features: list[str], **kwargs: Any) -> dict[str, ReadinessResult]:
        """여러 기능을 한 번에 점검."""
        return {f: self.checkReady(f, **kwargs) for f in features}

    def require(self, feature: str, **kwargs: Any) -> None:
        """기능이 준비되지 않으면 RuntimeError + 안내 메시지."""
        result = self.checkReady(feature, **kwargs)
        if not result.ok:
            raise RuntimeError(result.guideText())

    # ── 2. 능력 질의 ──

    def whatCanIDo(self, question: str = "", *, topK: int = 10) -> str:
        """'너 뭐 할 수 있어?' 대응."""
        if not question.strip():
            summary = build_capability_summary()
            env = self.envSnapshot()
            lines = [
                "dartlab 능력 요약:",
                f"  총 {summary.get('total', 0)}개 API 사용 가능",
                f"  데이터 디렉토리: {env.dataDir}",
                f"  DART API 키: {'설정됨' if env.dartKey.configured else '미설정'}",
                f"  AI 기본 provider: {env.aiDefaultProvider or '미설정'}",
                "",
                "종류별:",
            ]
            for kind, count in summary.get("byKind", {}).items():
                lines.append(f"  - {kind}: {count}개")
            lines.append("")
            lines.append('특정 기능 검색: guide.whatCanIDo("재무 분석")')
            return "\n".join(lines)

        results = searchCapabilities(question, topK=topK)
        if not results:
            return f"'{question}'에 해당하는 기능을 찾지 못했습니다."

        lines = [f"'{question}' 관련 기능:\n"]
        for key, entry, _score in results:
            lines.append(f"  - {key}: {entry.get('summary', '')}")
            if guideText := entry.get("guide"):
                firstLine = guideText.split("\n")[0]
                lines.append(f"    사용법: {firstLine}")
        return "\n".join(lines)

    def describe(self, funcName: str) -> str | None:
        """특정 기능의 안내 텍스트."""
        return suggest(funcName)

    # ── 3. 환경 스냅샷 ──

    def envSnapshot(self) -> EnvironmentSnapshot:
        """전체 환경 상태를 스냅샷으로 반환."""
        return self.credentials.snapshot()

    # ── 4. AI 인터페이스 ──

    def forAi(self, question: str) -> dict[str, Any]:
        """AI 시스템 프롬프트 빌드 시 호출.

        Returns dict:
            capabilitiesText: 관련 API 설명 (프롬프트 주입용)
            availableProviders: 사용 가능 provider 목록
            dartKeyAvailable: DART 키 여부
            dataDir: 데이터 경로
        """
        results = searchCapabilities(question, topK=15)
        capText = formatSearchResults(results) if results else "관련 기능을 찾지 못했습니다."
        env = self.envSnapshot()
        available = [
            pid for pid, cred in env.aiProviders.items()
            if cred.configured
        ]
        return {
            "capabilitiesText": capText,
            "availableProviders": available,
            "dartKeyAvailable": env.dartKey.configured,
            "dataDir": env.dataDir,
            "defaultProvider": env.aiDefaultProvider,
        }

    # ── 5. 에러 → 안내 변환 ──

    def handleError(self, error: Exception, *, feature: str | None = None) -> str:
        """에러를 사용자 친화적 안내 메시지로 변환.

        readiness 기반 안내 → 에러 타입별 구체적 분류 → 일반 폴백 순으로 처리.
        """
        # 1) readiness 기반 안내 (feature가 주어졌고, 준비 안 됐을 때)
        if feature:
            result = self.checkReady(feature)
            if not result.ok:
                return result.guideText()

        # 2) 에러 타입별 구체적 분류
        errType = type(error).__name__
        errStr = str(error)
        errLow = errStr.lower()

        # 파일 미존재 → 데이터 안내
        if isinstance(error, FileNotFoundError):
            return (
                f"파일을 찾을 수 없습니다: {errStr}\n"
                "  dartlab.downloadAll() 또는 dartlab.collect()로 데이터를 준비하세요."
            )

        # 권한 에러 → 로그인/키 안내
        if isinstance(error, PermissionError):
            return f"권한 오류: {errStr}\n  dartlab.setup()으로 인증을 확인하세요."

        # ChatGPT OAuth 에러
        if errType == "ChatGPTOAuthError":
            if any(kw in errLow for kw in ("token", "expire", "login")):
                return (
                    "ChatGPT 인증이 만료되었습니다.\n"
                    '  dartlab.setup("chatgpt")으로 다시 로그인하세요.'
                )
            if any(kw in errLow for kw in ("rate", "limit")):
                return "ChatGPT 요청 한도에 도달했습니다. 잠시 후 다시 시도해주세요."
            return f"ChatGPT 연결 오류: {errStr}\n  dartlab.setup(\"chatgpt\")으로 재인증하세요."

        # OpenAI / API 키 에러
        if errType == "OpenAIError" or "api_key" in errLow or "apikey" in errLow:
            return (
                "AI 설정이 필요합니다.\n"
                "  dartlab.setup()으로 API 키를 확인하거나 다른 provider를 선택하세요."
            )

        # Gemini 에러
        if errType in ("ServerError", "ClientError", "APIError") or "google" in errType.lower() or "genai" in errType.lower():
            if "503" in errStr or "unavailable" in errLow or "high demand" in errLow:
                return "Gemini 서버가 일시적으로 혼잡합니다. 잠시 후 다시 시도해주세요."
            if "429" in errStr or "rate" in errLow or "quota" in errLow or "resource_exhausted" in errLow:
                return "Gemini 요청 한도에 도달했습니다. 잠시 후 다시 시도해주세요."
            if "401" in errStr or "403" in errStr or "unauthenticated" in errLow or "permission" in errLow:
                return "Gemini API 키가 유효하지 않습니다.\n  dartlab.setup(\"gemini\")으로 키를 확인하세요."
            if "400" in errStr or "invalid" in errLow:
                return f"Gemini 요청 오류: {errStr}"
            return f"Gemini 연결 오류: {errStr}\n  잠시 후 다시 시도해주세요."

        # Ollama / 로컬 모델
        if "connection" in errLow and ("refused" in errLow or "11434" in errLow):
            return (
                "Ollama가 실행 중이지 않습니다.\n"
                "  ollama serve로 시작한 뒤 다시 시도하세요.\n"
                '  미설치: dartlab.setup("ollama")'
            )

        # 네트워크 / 타임아웃
        if isinstance(error, (ConnectionError, TimeoutError)):
            return (
                "AI 서버에 연결할 수 없습니다.\n"
                "  네트워크를 확인하거나 잠시 후 다시 시도해주세요.\n"
                "  다른 provider 시도: dartlab.setup()"
            )

        # 토큰/컨텍스트 초과
        if any(kw in errLow for kw in ("context", "token limit", "too long", "max_tokens")):
            return f"입력이 너무 깁니다: {errStr}\n  --exclude 옵션으로 컨텍스트를 줄여보세요."

        # 3) 일반 폴백
        return f"오류: {errStr}"

    # ── 6. 메타 ──

    def listFeatures(self) -> list[str]:
        """등록된 모든 checker feature 목록."""
        return listFeatures()


# ── 싱글턴 ──

_desk: GuideDesk | None = None


def getDesk() -> GuideDesk:
    """전역 GuideDesk 인스턴스."""
    global _desk
    if _desk is None:
        _desk = GuideDesk()
    return _desk
