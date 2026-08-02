"""`dartlab setup` 데이터 키와 agent runtime 안내."""

from __future__ import annotations


def configureParser(subparsers) -> None:
    """setup 서브커맨드에 runtime 또는 DART 데이터 키 대상을 등록한다."""
    parser = subparsers.add_parser("setup", help="설치형 agent CLI 또는 DART 데이터 키 설정")
    parser.add_argument("target", nargs="?", choices=["codex", "claude", "cline", "dart-key"], default=None)
    parser.set_defaults(handler=run)


def run(args) -> int:
    """선택 대상의 안전한 다음 명령을 출력하거나 DART 키를 입력받는다."""
    if args.target == "dart-key":
        return _setupDartKey()
    if args.target:
        print(f"\n  {args.target} 설치·연결은 Runtime Center가 관리합니다.")
        print(f"  상태: dartlab agent status {args.target}")
        print(f"  설치 계획: dartlab agent install {args.target}")
        if args.target != "cline":
            print(f"  MCP 연결 계획: dartlab agent connect {args.target}")
        print("  로그인은 설치 후 해당 CLI를 직접 실행하세요. DartLab은 인증 정보를 저장하지 않습니다.\n")
        return 0
    print("\n[ 분석 런타임 ]\n")
    print("  dartlab agent status          설치된 CLI 자동 탐지")
    print("  dartlab agent install codex   설치 계획과 digest 출력")
    print("  dartlab agent connect codex   DartLab MCP 연결 계획 출력\n")
    print('  dartlab ask --runtime codex "삼성전자 분석"   선택한 로컬 CLI로 근거 분석\n')
    print("[ 데이터 수집 ]\n")
    print("  dartlab setup dart-key        OpenDART 데이터 API 키 설정\n")
    return 0


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
