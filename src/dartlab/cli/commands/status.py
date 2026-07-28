"""`dartlab status` command."""

from __future__ import annotations

from dartlab.cli.context import PROVIDERS
from dartlab.cli.services.runtime import configureDartlab


def _providerStatus(providerName: str) -> dict:
    """provider 하나의 연결 상태. 예전 `dartlab.llm.status` 자리.

    그 이름은 표면에서 빠졌고 `dartlab.ai` 에 `status` 속성이 없다. 그래서 `dartlab status`
    를 치면 첫 provider 에서 AttributeError 로 죽었다. 표 머리만 찍히고 본문이 없었다.
    지금 살아 있는 조각은 설정 모듈의 가용 판정과 모델 해소기 둘이라 여기서 합친다.

    Returns:
        ``{"available": bool, "model": str}``. ollama 는 설치·구동 정보를 덧붙인다.
    """
    from dartlab.ai.settings.aiSetup import _checkProviderAvailable
    from dartlab.ai.settings.modelResolver import resolveDefaultModel

    available = bool(_checkProviderAvailable(providerName))
    try:
        model = resolveDefaultModel(providerName, allowFetch=False) or "-"
    except (AttributeError, KeyError, OSError, TypeError, ValueError):
        model = "-"
    status: dict = {"available": available, "model": model}
    if providerName == "ollama":
        try:
            from dartlab.ai.providers.support.ollamaSetup import detectOllama

            status["ollama"] = detectOllama()
        except (ImportError, AttributeError, OSError, RuntimeError):
            pass
    return status


_SETUP_HINTS = {
    "oauth-codex": "dartlab setup oauth-codex",
    "codex": "dartlab setup codex",
    "ollama": "dartlab setup ollama",
    "openai": "dartlab setup openai",
    "custom": "dartlab setup custom",
}


def configureParser(subparsers) -> None:
    """status 서브커맨드 등록 — LLM 연결 상태 확인."""
    parser = subparsers.add_parser("status", help="LLM 연결 상태 확인")
    parser.add_argument("--provider", "-p", default=None, choices=PROVIDERS, help="확인할 provider")
    parser.add_argument("--cost", action="store_true", help="누적 토큰/비용 통계")
    parser.set_defaults(handler=run)


def run(args) -> int:
    """LLM provider 연결 상태 또는 누적 비용 통계를 출력한다."""
    dartlab = configureDartlab()

    if args.cost:
        return _showCost()

    providers = [args.provider] if args.provider else PROVIDERS
    single = len(providers) == 1

    if not single:
        # 요약 테이블
        print("\n  Provider          │ 상태   │ 모델             │ 설정 방법")
        print("  ──────────────────┼────────┼──────────────────┼─────────────────────")

    for providerName in providers:
        status = _providerStatus(providerName)
        available = status["available"]

        if single:
            _printDetail(providerName, status)
        else:
            marker = "✓" if available else "✗"
            model = status.get("model", "-") or "-"
            hint = "" if available else _SETUP_HINTS.get(providerName, "")
            print(f"  {providerName:<18s} │ {marker:<5s}  │ {model:<16s} │ {hint}")

    if not single:
        avail = sum(1 for p in providers if _providerStatus(p)["available"])
        print(f"\n  {avail}/{len(providers)} provider 사용 가능")
        if avail == 0:
            print("  시작하려면: dartlab setup\n")
        else:
            print()
    return 0


def _printDetail(providerName: str, status: dict) -> None:
    """단일 provider 상세 출력."""
    available = status["available"]
    marker = "●" if available else "○"
    print(f"\n{marker} {providerName}")
    print(f"  model:     {status['model']}")
    print(f"  available: {available}")

    if providerName == "ollama" and "ollama" in status:
        info = status["ollama"]
        print(f"  installed: {info['installed']}")
        print(f"  running:   {info['running']}")
        if info.get("models"):
            print(f"  models:    {', '.join(info['models'])}")
        if not info["installed"]:
            print("  setup:     dartlab setup ollama")
        elif not info["running"]:
            print("  setup:     ollama serve")

    elif providerName == "codex" and "codex" in status:
        info = status["codex"]
        print(f"  installed: {info['installed']}")
        if info.get("version"):
            print(f"  version:   {info['version']}")
        if not info["installed"]:
            print("  setup:     dartlab setup codex")

    elif providerName == "oauth-codex" and "oauth-codex" in status:
        info = status["oauth-codex"]
        print(f"  token:     {info['tokenStored']}")
        print(f"  auth:      {info['authenticated']}")
        print(f"  base url:  {info.get('baseUrlConfigured', False)}")
        if info.get("accountId"):
            print(f"  account:   {info['accountId']}")
        if not info["authenticated"]:
            print("  setup:     dartlab setup oauth-codex")

    elif providerName in ("openai", "custom") and not available:
        print(f"  setup:     dartlab setup {providerName}")

    print()


def _showCost() -> int:
    """누적 토큰/비용 통계 출력."""
    try:
        from dartlab.cli.services.history import getTotalUsage

        usage = getTotalUsage()
    except (ImportError, OSError):
        print("  비용 데이터가 없습니다.")
        return 0

    from dartlab.cli.services.output import getConsole

    console = getConsole()
    console.print("\n  [bold]토큰 사용량 통계[/]\n")
    console.print(f"  총 요청 수:    {usage['총_요청수']:,}")
    console.print(f"  입력 토큰:     {usage['입력_토큰']:,}")
    console.print(f"  출력 토큰:     {usage['출력_토큰']:,}")
    console.print(f"  총 비용 (USD): ${usage['총_비용_USD']:.4f}")
    console.print()
    return 0
