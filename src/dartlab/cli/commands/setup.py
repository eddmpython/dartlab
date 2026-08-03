"""`dartlab setup` 데이터 키와 agent runtime 안내."""

from __future__ import annotations


def configureParser(subparsers) -> None:
    """setup 서브커맨드에 runtime 또는 DART 데이터 키 대상을 등록한다."""
    parser = subparsers.add_parser(
        "setup",
        help="투자 분석 agent를 한 번에 준비하거나 DART 데이터 키 설정",
        description=(
            "투자 분석용 설치형 agent의 설치, 공식 로그인, DartLab 연결을 한 흐름으로 완료합니다. "
            "OpenDART 데이터 키는 dartlab setup dart-key로 별도 설정합니다."
        ),
    )
    parser.add_argument("target", nargs="?", choices=["codex", "claude", "cline", "dart-key"], default=None)
    parser.add_argument("--yes", "-y", action="store_true", help="설치와 DartLab 연결 변경을 한 번에 승인")
    parser.set_defaults(handler=run)


def run(args) -> int:
    """선택 대상의 안전한 다음 명령을 출력하거나 DART 키를 입력받는다."""
    if args.target == "dart-key":
        return _setupDartKey()
    from dartlab.cli.commands.agent import runSetup

    return runSetup(args.target, yes=getattr(args, "yes", False))


def _setupDartKey() -> int:
    """OpenDART 데이터 API 키를 대화형으로 프로젝트 환경에 저장한다."""
    from dartlab.core.dartClient import hasDartApiKey

    if hasDartApiKey():
        print("\n  DART API 키가 이미 설정되어 있습니다.\n")
        return 0
    print("\n  OpenDART 키 발급: https://opendart.fss.or.kr")
    apiKey = input("  DART API KEY: ").strip()
    if not apiKey:
        print("\n  취소됨.\n")
        return 1
    from dartlab.gather.dart.keys import saveDartKeyToDotenv

    saveDartKeyToDotenv(apiKey)
    print("\n  DART_API_KEY 저장 완료. 이 키는 모델 인증과 무관합니다.\n")
    return 0
