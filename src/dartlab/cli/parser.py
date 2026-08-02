"""Argument parser builder for DartLab CLI."""

from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version

from dartlab.cli.context import DEPRECATED_ALIASES, CommandSpec
from dartlab.cli.services.runtime import loadCommandModule

COMMAND_SPECS = (
    # 데이터 조회
    CommandSpec("show", "dartlab.cli.commands.show", "topic 기반 데이터 조회"),
    CommandSpec("search", "dartlab.cli.commands.search", "종목코드/회사명 검색"),
    CommandSpec("statement", "dartlab.cli.commands.statement", "재무제표 출력 (BS/IS/CIS/CF/SCE)"),
    CommandSpec("sections", "dartlab.cli.commands.sections", "panel 공시 격자 출력"),
    CommandSpec("profile", "dartlab.cli.commands.profile", "Company index/facts 출력"),
    CommandSpec("modules", "dartlab.cli.commands.modules", "사용 가능한 데이터 모듈 목록"),
    # 에이전트 / 내보내기
    CommandSpec("ask", "dartlab.cli.commands.ask", "자연어 원스톱 분석"),
    CommandSpec("agent", "dartlab.cli.commands.agent", "설치형 agent runtime 관리"),
    CommandSpec("report", "dartlab.cli.commands.report", "Markdown 분석 보고서 생성"),
    CommandSpec("excel", "dartlab.cli.commands.excel", "기업 데이터 Excel 내보내기"),
    # 분석
    CommandSpec("story", "dartlab.cli.commands.story", "기업 분석 스토리 (사람이 읽는 보고서)"),
    # 수집/갱신
    CommandSpec("collect", "dartlab.cli.commands.collect", "DART/EDGAR 데이터 수집"),
    CommandSpec("sync", "dartlab.cli.commands.sync", "수집 파이프라인 실행 (로컬/CI 단일 SSOT)"),
    CommandSpec("update", "dartlab.cli.commands.update", "로컬 데이터를 HuggingFace 최신으로 갱신"),
    # 서버 / 설정
    CommandSpec("ai", "dartlab.cli.commands.ai", "분석 웹 인터페이스 실행"),
    CommandSpec("channel", "dartlab.cli.commands.channel", "외부 공유 채널 (DevTunnels 기본, 모바일 호환)"),
    CommandSpec("status", "dartlab.cli.commands.status", "agent runtime 연결 상태 확인"),
    CommandSpec("setup", "dartlab.cli.commands.setup", "agent runtime/DART 데이터 키 설정"),
    # MCP
    CommandSpec("mcp", "dartlab.cli.commands.mcp", "MCP 서버 실행 (stdio)"),
    # 플러그인
    CommandSpec("plugin", "dartlab.cli.commands.plugin", "플러그인 관리 (list/create)"),
)


HELP_DESCRIPTION = """\
DartLab — Korean DART + US SEC EDGAR 공시를 종목코드 하나로 분석한다.

`dartlab <종목코드>` 또는 `dartlab <한글 회사명>` 한 줄이면 story 로 자동 라우팅된다.
세부 서브커맨드는 아래 5 개 그룹으로 묶여 있고, `dartlab <서브커맨드> --help` 로 깊이 진입한다.
"""


HELP_EPILOG = """\
서브커맨드 그룹

  데이터 조회
    show         topic 기반 데이터 조회 (BS/IS/CF · panel · 정형 보고서)
    statement    재무제표 출력 (BS/IS/CIS/CF/SCE)
    sections     panel 공시 격자 출력
    profile      Company index/facts 출력
    search       종목코드/회사명 검색
    modules      사용 가능한 데이터 모듈 목록

  분석 / 보고서
    story        기업 분석 스토리 (사람이 읽는 보고서) — 자연어 라우팅의 기본 진입점
    ask          자연어 원스톱 분석 (에이전트가 도구 호출)
    report       Markdown 분석 보고서 생성
    excel        기업 데이터 Excel 내보내기

  수집 / 갱신
    collect      DART/EDGAR 원본 재수집 (API 키 필요)
    update       로컬 데이터를 HuggingFace 최신으로 갱신

  서버 / 외부 연동
    ai           분석 웹 인터페이스 실행
    channel      외부 공유 채널 (DevTunnels 기본, 모바일 호환)
    mcp          MCP 서버 (stdio) — 외부 도구에서 같은 표면 호출
    plugin       플러그인 관리 (list/create)

  설정
    setup        모델 provider/API 키 설정
    status       모델 연결 상태 확인

자동 라우팅
  종목코드(6 자리 숫자) 또는 한글 회사명을 첫 인자로 주면 `story` 로 자동 라우팅:
    dartlab 005930              == dartlab story 005930
    dartlab 삼성전자             == dartlab story 삼성전자
    dartlab 005930 자산구조      == dartlab story 005930 자산구조

30 초 quickstart (키 0, 환경변수 0)
  pip install dartlab
  dartlab 005930

문서 · Skill OS
  https://eddmpython.github.io/dartlab/         문서
  https://eddmpython.github.io/dartlab/skills   Skill OS (304 specs)
  README_EN.md                                  English readme

영문 사용자
  CLI 진행·에러 메시지는 한국어가 기본이지만 함수·심볼은 모두 영어다.
  설계 결정은 README_EN.md `Design Choices` 섹션 참조.
"""


class DartLabArgumentParser(argparse.ArgumentParser):
    """Parser that exits with stable CLI usage codes."""

    def error(self, message):
        """error — TODO 한국어 동작 설명."""
        self.print_usage()
        raise SystemExit(f"{self.prog}: error: {message}")


def buildParser() -> argparse.ArgumentParser:
    """CLI ArgumentParser 생성 및 서브커맨드 등록."""
    parser = DartLabArgumentParser(
        prog="dartlab",
        description=HELP_DESCRIPTION,
        epilog=HELP_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    try:
        version = pkg_version("dartlab")
    except PackageNotFoundError:
        version = "0.0.0"
    parser.add_argument("--version", action="version", version=f"%(prog)s {version}")
    visible_commands = ",".join(spec.name for spec in COMMAND_SPECS)
    subparsers = parser.add_subparsers(dest="command", metavar=f"{{{visible_commands}}}")

    for spec in COMMAND_SPECS:
        command_module = loadCommandModule(spec)
        command_module.configureParser(subparsers)

    for alias, target in DEPRECATED_ALIASES.items():
        if alias in subparsers.choices:
            subparsers.choices[alias].help = argparse.SUPPRESS

    return parser
