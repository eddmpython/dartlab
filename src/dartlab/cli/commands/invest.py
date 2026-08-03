"""`dartlab invest` 투자 의사결정 브리프 진입점."""

from __future__ import annotations

import argparse


def configureParser(subparsers) -> None:
    """종목 하나와 선택적 초점을 받는 투자 브리프 명령을 등록한다."""
    parser = subparsers.add_parser("invest", help="논지·하방·밸류·촉매를 한 번에 분석")
    parser.add_argument("company", help="종목코드 또는 회사명")
    parser.add_argument("focus", nargs="*", help="추가로 확인할 투자 초점")
    parser.add_argument("--runtime", "-r", choices=["codex", "claude"], default=None)
    parser.add_argument("--expert", action="store_true", help="모형 가정과 근거 계보까지 상세히 표시")
    parser.set_defaults(handler=run)


def run(args) -> int:
    """일반 투자자용 핵심 5개를 먼저 요청하고 기존 ask 스트림을 재사용한다."""
    from dartlab.cli.commands.ask import run as runAsk

    focus = " ".join(getattr(args, "focus", [])).strip()
    question = (
        "투자 의사결정 브리프를 작성해줘. 중심논지와 가장 강한 반대논지, 실적 변곡과 원인, "
        "산업·거시 전파, 현재가에 반영된 기대와 밸류에이션, bear/base/bull, 촉매와 시점, "
        "리스크와 논지 훼손 경로, monitoring tripwire와 다음 확인 시점을 분석해줘."
    )
    if focus:
        question += f" 추가 초점: {focus}."
    if getattr(args, "expert", False):
        question += " 전문가 세부 정보로 WACC, reverse DCF, 시나리오 driver, 근거 계보와 결손도 펼쳐줘."
    askArgs = argparse.Namespace(
        query=[question],
        company=args.company,
        runtime=getattr(args, "runtime", None),
        session=None,
        include=None,
        exclude=None,
        stream=True,
        cont=False,
        pattern=None,
        report=True,
        investment=True,
    )
    return runAsk(askArgs)


__all__ = ["configureParser", "run"]
