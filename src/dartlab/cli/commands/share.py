"""`dartlab share` command — 로컬 서버를 외부에 안전하게 공개.

사용 예:
    dartlab share                        # 저장된 설정 또는 인터랙티브
    dartlab share --ttl 2h              # 2시간 TTL
    dartlab share --tunnel ngrok         # ngrok 터널
    dartlab share --readonly            # 읽기 전용
    dartlab share --save                # 현재 옵션을 기본값으로 저장
    dartlab share --reset               # 저장된 설정 초기화
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

_SHARE_CONFIG_PATH = Path.home() / ".dartlab" / "share.json"

_TTL_CHOICES = [
    ("30m", 1800, "30분"),
    ("1h", 3600, "1시간"),
    ("3h", 10800, "3시간"),
    ("12h", 43200, "12시간"),
    ("24h", 86400, "24시간"),
]

# dartlab 컬러 팔레트 (display.py 동일)
_PR = "#ea4647"
_AC = "#fb923c"
_TM = "#94a3b8"
_TX = "#f1f5f9"


def configure_parser(subparsers) -> None:
    """share 서브커맨드 등록 — 터널 기반 외부 공유."""
    parser = subparsers.add_parser(
        "share",
        help="로컬 서버를 외부에 안전하게 공개",
    )
    parser.add_argument(
        "--tunnel",
        choices=["cloudflare", "ngrok", "ssh"],
        default=None,
        help="터널 백엔드 (기본: cloudflare)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="포트 번호 (기본: 8400)",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="호스트 (기본: 127.0.0.1)",
    )
    parser.add_argument(
        "--ttl",
        default=None,
        help="터널 자동 만료 시간 (예: 30m, 2h, 24h)",
    )
    parser.add_argument(
        "--token",
        help="커스텀 인증 토큰 (미지정 시 자동 생성)",
    )
    parser.add_argument(
        "--readonly",
        action="store_true",
        default=None,
        help="읽기 전용 모드 (POST /api/ask 등 차단)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="브라우저 자동 열기 비활성화",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="현재 옵션을 기본 설정으로 저장",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="저장된 기본 설정 초기화",
    )
    # 메시징 채널
    parser.add_argument(
        "--telegram",
        metavar="TOKEN",
        help="Telegram 봇 토큰 (BotFather에서 발급)",
    )
    parser.add_argument(
        "--slack",
        metavar="BOT_TOKEN",
        help="Slack 봇 토큰 (xoxb-...)",
    )
    parser.add_argument(
        "--slack-app-token",
        metavar="APP_TOKEN",
        help="Slack 앱 토큰 (xapp-..., Socket Mode용)",
    )
    parser.add_argument(
        "--discord",
        metavar="TOKEN",
        help="Discord 봇 토큰",
    )
    parser.set_defaults(handler=run)


# ---------------------------------------------------------------------------
# 설정 저장/로드
# ---------------------------------------------------------------------------


def _load_config() -> dict:
    """~/.dartlab/share.json 에서 저장된 설정을 로드한다."""
    if _SHARE_CONFIG_PATH.exists():
        try:
            return json.loads(_SHARE_CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_config(config: dict) -> None:
    """설정을 ~/.dartlab/share.json 에 저장한다."""
    _SHARE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SHARE_CONFIG_PATH.write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _resolve_option(args_val, config_key: str, config: dict, default):
    """CLI 인자 > 저장된 설정 > 기본값 순으로 결정."""
    if args_val is not None:
        return args_val
    if config_key in config:
        return config[config_key]
    return default


# ---------------------------------------------------------------------------
# TTL
# ---------------------------------------------------------------------------


def _parse_ttl(ttl_str: str) -> int:
    """TTL 문자열을 초 단위로 변환. 예: '30m' -> 1800, '2h' -> 7200."""
    match = re.match(r"^(\d+)(m|h|s)?$", ttl_str.strip())
    if not match:
        print(f"  오류: 잘못된 TTL 형식: {ttl_str!r} (예: 30m, 2h, 3600s)", file=sys.stderr)
        raise SystemExit(1)

    value = int(match.group(1))
    unit = match.group(2) or "s"
    multipliers = {"s": 1, "m": 60, "h": 3600}
    return value * multipliers[unit]


def _ttl_to_str(seconds: int) -> str:
    """초를 사람이 읽기 좋은 문자열로."""
    if seconds >= 3600 and seconds % 3600 == 0:
        return f"{seconds // 3600}시간"
    if seconds >= 60 and seconds % 60 == 0:
        return f"{seconds // 60}분"
    return f"{seconds}초"


def _ask_ttl() -> int:
    """사용자에게 TTL을 인터랙티브하게 선택하게 한다."""
    print()
    print("  공유 시간을 선택하세요:")
    print()
    for i, (_, _, label) in enumerate(_TTL_CHOICES, 1):
        marker = " *" if i == 2 else ""
        print(f"    {i}) {label}{marker}")
    print("    6) 직접 입력")
    print()

    try:
        choice = input("  선택 [1-6, 기본=2]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit(0)

    if choice == "" or choice == "2":
        return 3600

    idx = None
    try:
        idx = int(choice) - 1
    except ValueError:
        pass

    if idx is not None and 0 <= idx < len(_TTL_CHOICES):
        return _TTL_CHOICES[idx][1]
    if choice == "6" or idx == 5:
        try:
            custom = input("  시간 입력 (예: 30m, 2h, 6h): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise SystemExit(0)
        return _parse_ttl(custom)

    try:
        return _parse_ttl(choice)
    except SystemExit:
        print("  잘못된 입력. 기본값 1시간을 사용합니다.", file=sys.stderr)
        return 3600


# ---------------------------------------------------------------------------
# QR 코드 — qrcode 내장 print_ascii 사용
# ---------------------------------------------------------------------------


def _ensure_qrcode() -> bool:
    """qrcode 패키지가 없으면 설치 여부를 묻는다."""
    try:
        import qrcode  # noqa: F401

        return True
    except ImportError:
        pass

    print()
    print("  QR 코드 출력에 qrcode 패키지가 필요합니다.")
    try:
        answer = input("  설치하시겠습니까? [Y/n] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False

    if answer not in ("", "y", "yes"):
        return False

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "qrcode"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("  qrcode 설치 실패. QR 코드 없이 계속합니다.", file=sys.stderr)
        return False

    print("  설치 완료!")
    return True


def _render_qr(url: str) -> str:
    """URL을 QR 코드 문자열로 렌더링한다. 다크 터미널 호환."""
    import qrcode  # type: ignore[import-untyped]

    qr = qrcode.QRCode(border=2, error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr.add_data(url)
    qr.make(fit=True)
    buf = io.StringIO()
    qr.print_ascii(out=buf, invert=True)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Rich 출력
# ---------------------------------------------------------------------------


def _print_share_info(
    *,
    full_url: str,
    readonly_url: str,
    ttl_display: str,
    tunnel_backend: str,
    readonly: bool,
    has_qr: bool,
    show_save_tip: bool,
) -> None:
    """Rich Panel로 공유 정보를 출력한다."""
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    from dartlab.cli.services.output import get_console

    console = get_console()

    # 내부 콘텐츠 조립
    parts: list[str | Text] = []

    # QR 코드
    if has_qr:
        qr_text = _render_qr(full_url)
        parts.append(qr_text)

    # URL 정보 테이블
    info = Table.grid(padding=(0, 2))
    info.add_column(style=f"bold {_TM}", justify="right")
    info.add_column(style=f"bold {_TX}")

    info.add_row("URL", full_url)
    if not readonly:
        info.add_row("Read-only", readonly_url)
    info.add_row("TTL", ttl_display)
    info.add_row("Tunnel", tunnel_backend)
    info.add_row("Room", "협업 모드 활성 (최대 10명)")
    if readonly:
        info.add_row("Mode", "readonly")

    # Panel 출력
    from rich.console import Group

    group_items = []
    if has_qr:
        group_items.append(Text.from_ansi(qr_text))
    group_items.append(info)

    # 임베드 스니펫
    embed_tip = Text()
    embed_tip.append("\n")
    embed_tip.append("Embed: ", style=f"bold {_AC}")
    # public_url 추출 (full_url에서 ?token= 앞부분)
    base = full_url.split("/?")[0] if "/?" in full_url else full_url
    ro_token = readonly_url.split("token=")[-1] if "token=" in readonly_url else ""
    embed_tip.append(
        f'<script src="{base}/embed.js" data-code="종목코드" data-token="{ro_token}"></script>',
        style=_TX,
    )
    group_items.append(embed_tip)

    if show_save_tip:
        tip = Text()
        tip.append("\n")
        tip.append("Tip: ", style=f"bold {_AC}")
        tip.append("dartlab share --save", style=f"bold {_TX}")
        tip.append(" 로 이 설정을 저장하세요", style=_TM)
        group_items.append(tip)

    footer = Text()
    footer.append("\nCtrl+C", style=f"bold {_TX}")
    footer.append(" 로 종료", style=_TM)
    group_items.append(footer)

    panel = Panel(
        Group(*group_items),
        title="[bold]DartLab Share[/]",
        border_style=_PR,
        padding=(1, 2),
    )
    console.print()
    console.print(panel)
    console.print()


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------


def run(args) -> int:
    """터널을 통해 로컬 서버를 외부에 공유한다."""
    config = _load_config()

    # --reset: 설정 초기화
    if args.reset:
        if _SHARE_CONFIG_PATH.exists():
            _SHARE_CONFIG_PATH.unlink()
            print("  저장된 설정이 초기화되었습니다.")
        else:
            print("  저장된 설정이 없습니다.")
        return 0

    # 옵션 결정: CLI > 저장된 설정 > 기본값
    tunnel_backend = _resolve_option(args.tunnel, "tunnel", config, "cloudflare")
    port = _resolve_option(args.port, "port", config, 8400)
    host = _resolve_option(args.host, "host", config, "127.0.0.1")
    readonly = _resolve_option(args.readonly, "readonly", config, False)

    # TTL: CLI > 저장된 설정 > 인터랙티브 선택
    if args.ttl is not None:
        ttl = _parse_ttl(args.ttl)
    elif "ttl" in config:
        ttl = config["ttl"]
        print(f"\n  저장된 설정 사용: TTL={_ttl_to_str(ttl)}, 터널={tunnel_backend}")
    else:
        ttl = _ask_ttl()

    # --save: 현재 옵션을 기본값으로 저장
    if args.save:
        save_data = {"tunnel": tunnel_backend, "port": port, "host": host, "ttl": ttl, "readonly": readonly}
        _save_config(save_data)
        print(f"\n  설정 저장됨: {_SHARE_CONFIG_PATH}")
        print(f"    터널={tunnel_backend}, TTL={_ttl_to_str(ttl)}, 포트={port}")
        print()

    # --- 보안 환경변수 설정 ---
    os.environ["DARTLAB_TUNNEL"] = "1"

    if args.token:
        os.environ["DARTLAB_TUNNEL_TOKEN"] = args.token

    os.environ["DARTLAB_TUNNEL_TTL"] = str(ttl)

    if readonly:
        os.environ["DARTLAB_TUNNEL_READONLY"] = "1"

    # --- 보안 컴포넌트 초기화 ---
    from dartlab.server.security import TokenManager, TunnelKillSwitch

    token_manager = TokenManager(args.token)
    kill_switch = TunnelKillSwitch(ttl)

    os.environ["DARTLAB_TUNNEL_TOKEN"] = token_manager.full_token

    # --- 포트 확보 ---
    from dartlab.server import ensure_port

    status = ensure_port(port)
    if status == "failed":
        return 1

    # --- 터널 시작 ---
    print(f"\n  터널 시작 중... ({tunnel_backend})")

    from dartlab.channel.tunnel import create_tunnel

    try:
        tunnel = create_tunnel(tunnel_backend)
        public_url = tunnel.start(port)
    except RuntimeError as exc:
        print(f"\n  터널 시작 실패: {exc}", file=sys.stderr)
        return 1

    # CORS에 터널 도메인 추가 (절대 *가 아님)
    os.environ["DARTLAB_CORS_ORIGINS"] = f"http://127.0.0.1:{port},http://localhost:{port},{public_url}"

    # --- 접속 정보 출력 ---
    full_url = f"{public_url}/?token={token_manager.full_token}"
    readonly_url = f"{public_url}/?token={token_manager.readonly_token}"
    has_qr = _ensure_qrcode()

    _print_share_info(
        full_url=full_url,
        readonly_url=readonly_url,
        ttl_display=_ttl_to_str(ttl),
        tunnel_backend=tunnel_backend,
        readonly=readonly,
        has_qr=has_qr,
        show_save_tip=not config and not args.save,
    )

    # --- 메시징 채널 시작 (백그라운드) ---
    adapters = _start_messaging_adapters(args)

    # --- 서버 시작 (blocking) ---
    from dartlab.server import run_server

    try:
        run_server(host=host, port=port)
    except KeyboardInterrupt:
        pass
    finally:
        for adapter in adapters:
            print(f"\n  {adapter.name} 어댑터 종료 중...")
        print("\n  터널 종료 중...")
        tunnel.stop()
        print("  종료 완료.")

    return 0


def _start_messaging_adapters(args) -> list:
    """CLI 인자에 따라 메시징 어댑터를 백그라운드로 시작한다."""
    import threading

    adapters = []

    if getattr(args, "telegram", None):
        from dartlab.channel.adapters import create_adapter

        adapter = create_adapter("telegram", token=args.telegram)
        adapters.append(adapter)
        t = threading.Thread(target=_run_adapter, args=(adapter,), daemon=True)
        t.start()
        print("  Telegram 봇 시작됨")

    if getattr(args, "slack", None):
        app_token = getattr(args, "slack_app_token", None)
        if not app_token:
            print("  Slack은 --slack-app-token 이 필요합니다 (Socket Mode)", file=sys.stderr)
        else:
            from dartlab.channel.adapters import create_adapter

            adapter = create_adapter("slack", bot_token=args.slack, app_token=app_token)
            adapters.append(adapter)
            t = threading.Thread(target=_run_adapter, args=(adapter,), daemon=True)
            t.start()
            print("  Slack 봇 시작됨")

    if getattr(args, "discord", None):
        from dartlab.channel.adapters import create_adapter

        adapter = create_adapter("discord", token=args.discord)
        adapters.append(adapter)
        t = threading.Thread(target=_run_adapter, args=(adapter,), daemon=True)
        t.start()
        print("  Discord 봇 시작됨")

    return adapters


def _run_adapter(adapter) -> None:
    """어댑터를 별도 이벤트 루프에서 실행한다."""
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(adapter.start())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
