"""DartLab CLI — 터미널에서 바로 기업 분석.

사용법::

    dartlab ask 005930 "재무 건전성을 분석해줘"
    dartlab ask 삼성전자 "배당 추세" --provider codex
    dartlab ask 005930 "부채 리스크" --provider claude-code --stream
    dartlab status
    dartlab setup codex
    dartlab ai                  # AI 분석 웹 인터페이스 (http://localhost:8400)
"""

from __future__ import annotations

import argparse
import io
import sys


def _ensure_utf8():
	"""Windows cp949 환경에서 UTF-8 출력 강제."""
	if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
		sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
		sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


_PROVIDERS = ["codex", "claude-code", "ollama", "openai", "claude", "custom"]
_CLI_PROVIDERS = ["codex", "claude-code", "ollama"]


def main():
	_ensure_utf8()
	parser = argparse.ArgumentParser(
		prog="dartlab",
		description="DartLab — DART 공시 데이터 + LLM 분석",
	)
	sub = parser.add_subparsers(dest="command")

	# ── dartlab ask ──
	ask_parser = sub.add_parser("ask", help="LLM에게 기업 분석 질문")
	ask_parser.add_argument("company", help="종목코드 (005930) 또는 회사명 (삼성전자)")
	ask_parser.add_argument("question", help="질문 텍스트")
	ask_parser.add_argument("--provider", "-p", default=None, choices=_PROVIDERS, help="LLM provider")
	ask_parser.add_argument("--model", "-m", default=None, help="모델명")
	ask_parser.add_argument("--base-url", default=None, help="커스텀 API URL")
	ask_parser.add_argument("--api-key", default=None, help="API 키")
	ask_parser.add_argument("--include", "-i", nargs="+", default=None, help="포함할 데이터 (BS IS dividend ...)")
	ask_parser.add_argument("--exclude", "-e", nargs="+", default=None, help="제외할 데이터")
	ask_parser.add_argument("--stream", "-s", action="store_true", help="스트리밍 출력")

	# ── dartlab status ──
	status_parser = sub.add_parser("status", help="LLM 연결 상태 확인")
	status_parser.add_argument("--provider", "-p", default=None, choices=_PROVIDERS, help="확인할 provider")

	# ── dartlab setup ──
	setup_parser = sub.add_parser("setup", help="LLM provider 설치 및 인증 안내")
	setup_parser.add_argument("provider", nargs="?", default=None, choices=_CLI_PROVIDERS, help="설정할 provider")

	# ── dartlab ai ──
	ai_parser = sub.add_parser("ai", help="AI 분석 웹 인터페이스 실행")
	ai_parser.add_argument("--port", type=int, default=8400, help="포트 번호 (기본: 8400)")
	ai_parser.add_argument("--host", default="0.0.0.0", help="호스트 (기본: 0.0.0.0)")
	ai_parser.add_argument("--dev", action="store_true", help="개발 모드 (Svelte dev 서버 동시 실행)")

	# ── dartlab ui (별칭, 하위 호환) ──
	ui_parser = sub.add_parser("ui")
	ui_parser.add_argument("--port", type=int, default=8400)
	ui_parser.add_argument("--host", default="0.0.0.0")
	ui_parser.add_argument("--dev", action="store_true")

	args = parser.parse_args()

	if args.command is None:
		parser.print_help()
		return

	if args.command == "status":
		_cmd_status(args)
	elif args.command == "ask":
		_cmd_ask(args)
	elif args.command == "setup":
		_cmd_setup(args)
	elif args.command in ("ai", "ui"):
		if args.command == "ui":
			print("  ℹ  dartlab ui → dartlab ai 로 변경되었습니다. dartlab ai를 사용하세요.\n")
		_cmd_ui(args)


def _cmd_status(args):
	import dartlab

	dartlab.verbose = False

	if args.provider:
		providers = [args.provider]
	else:
		providers = _PROVIDERS

	for prov in providers:
		dartlab.llm.configure(provider=prov)
		s = dartlab.llm.status()

		avail = s["available"]
		mark = "●" if avail else "○"
		print(f"\n{mark} {prov}")
		print(f"  model:     {s['model']}")
		print(f"  available: {avail}")

		if prov == "ollama" and "ollama" in s:
			info = s["ollama"]
			print(f"  installed: {info['installed']}")
			print(f"  running:   {info['running']}")
			if info.get("models"):
				print(f"  models:    {', '.join(info['models'])}")
			if not info["installed"]:
				print(f"  setup:     dartlab setup ollama")
			elif not info["running"]:
				print(f"  setup:     ollama serve")

		elif prov == "claude-code" and "claude-code" in s:
			info = s["claude-code"]
			print(f"  installed: {info['installed']}")
			print(f"  authenticated: {info['authenticated']}")
			if info.get("version"):
				print(f"  version:   {info['version']}")
			if not info["installed"] or not info["authenticated"]:
				print(f"  setup:     dartlab setup claude-code")

		elif prov == "codex" and "codex" in s:
			info = s["codex"]
			print(f"  installed: {info['installed']}")
			if info.get("version"):
				print(f"  version:   {info['version']}")
			if not info["installed"]:
				print(f"  setup:     dartlab setup codex")

		elif prov in ("openai", "claude", "custom") and not avail:
			print(f"  setup:     dartlab ask ... -p {prov} --api-key YOUR_KEY")

	print()


def _cmd_setup(args):
	from dartlab.engines.llmAnalyzer.cli_setup import (
		detect_claude_code, detect_codex,
	)

	if args.provider is None:
		# 전체 안내
		print("\n사용 가능한 provider:\n")
		print("  dartlab setup codex        ChatGPT Plus/Pro 구독 (API 키 불필요)")
		print("  dartlab setup claude-code  Claude Pro/Max 구독 (API 키 불필요)")
		print("  dartlab setup ollama       로컬 LLM (무료)\n")
		return

	if args.provider == "codex":
		_setup_codex(detect_codex())
	elif args.provider == "claude-code":
		_setup_claude_code(detect_claude_code())
	elif args.provider == "ollama":
		_setup_ollama()


def _setup_codex(info: dict):
	print("\n[ Codex CLI 설정 — ChatGPT Plus/Pro 구독 ]\n")

	# Step 1: 설치
	if info["installed"]:
		print(f"  1. 설치  ✓  ({info.get('version', 'installed')})")
	else:
		print("  1. 설치")
		print("     npm install -g @openai/codex\n")
		print("     Node.js가 필요합니다: https://nodejs.org/\n")

	# Step 2: 인증
	print("  2. 인증")
	if info["installed"]:
		print("     터미널에서 codex 를 실행하면 브라우저가 열립니다.")
		print("     ChatGPT 계정으로 로그인하세요.\n")
	else:
		print("     설치 후 codex 를 실행하면 브라우저에서 로그인됩니다.\n")

	# Step 3: 확인
	print("  3. 확인")
	print("     dartlab status -p codex\n")

	# Step 4: 사용
	print("  4. 사용")
	print('     dartlab ask 005930 "재무 건전성 분석" -p codex')
	print()


def _setup_claude_code(info: dict):
	print("\n[ Claude Code CLI 설정 — Claude Pro/Max 구독 ]\n")

	# Step 1: 설치
	if info["installed"]:
		print(f"  1. 설치  ✓  ({info.get('version', 'installed')})")
	else:
		print("  1. 설치")
		print("     npm install -g @anthropic-ai/claude-code\n")
		print("     Node.js가 필요합니다: https://nodejs.org/\n")

	# Step 2: 인증
	if info.get("authenticated"):
		print("  2. 인증  ✓")
	else:
		print("  2. 인증")
		print("     claude auth login\n")
		print("     브라우저가 열리면 Claude 계정으로 로그인하세요.\n")

	# Step 3: 확인
	print("  3. 확인")
	print("     dartlab status -p claude-code\n")

	# Step 4: 사용
	print("  4. 사용")
	print('     dartlab ask 005930 "재무 건전성 분석" -p claude-code')
	print('     dartlab ask 삼성전자 "배당 분석" -p claude-code -m opus')
	print()


def _setup_ollama():
	print("\n[ Ollama 설정 — 로컬 LLM (무료) ]\n")

	print("  1. 설치")
	print("     https://ollama.com/download\n")

	print("  2. 모델 다운로드")
	print("     ollama pull llama3.2\n")

	print("  3. 서버 시작")
	print("     ollama serve\n")

	print("  4. 확인")
	print("     dartlab status -p ollama\n")

	print("  5. 사용")
	print('     dartlab ask 005930 "재무 건전성 분석" -p ollama')
	print()


def _detect_provider() -> str:
	"""사용 가능한 provider 자동 감지."""
	from dartlab.engines.llmAnalyzer.providers import create_provider
	from dartlab.engines.llmAnalyzer.types import LLMConfig

	for prov in ["codex", "claude-code", "ollama"]:
		config = LLMConfig(provider=prov)
		try:
			provider = create_provider(config)
			if provider.check_available():
				return prov
		except Exception:
			continue
	return "ollama"


def _cmd_ask(args):
	import dartlab

	dartlab.verbose = False

	provider = args.provider or _detect_provider()
	kwargs = {"provider": provider}
	if args.model:
		kwargs["model"] = args.model
	if args.base_url:
		kwargs["base_url"] = args.base_url
	if args.api_key:
		kwargs["api_key"] = args.api_key

	dartlab.llm.configure(**kwargs)

	try:
		c = dartlab.Company(args.company)
	except Exception as e:
		print(f"오류: {e}", file=sys.stderr)
		sys.exit(1)

	print(f"\n  {c.corpName} ({c.stockCode})")
	print(f"  provider: {provider}")
	print()

	answer = c.ask(
		args.question,
		include=args.include,
		exclude=args.exclude,
		stream=args.stream,
	)

	if not args.stream:
		print(answer)


def _cmd_ui(args):
	import webbrowser
	from pathlib import Path

	port = args.port
	host = args.host
	url = f"http://localhost:{port}"

	if args.dev:
		# 개발 모드: Svelte dev 서버 + FastAPI 동시 실행
		import subprocess
		import threading

		ui_dir = Path(__file__).parent / "ui"
		if not (ui_dir / "node_modules").exists():
			print("npm install 실행 중...")
			subprocess.run(["npm", "install"], cwd=str(ui_dir), shell=True)

		def run_vite():
			subprocess.run(
				["npm", "run", "dev"],
				cwd=str(ui_dir),
				shell=True,
			)

		print(f"\n  DartLab AI (개발 모드)")
		print(f"  API:     {url}")
		print(f"  Svelte:  http://localhost:5400")
		print()

		vite_thread = threading.Thread(target=run_vite, daemon=True)
		vite_thread.start()
	else:
		ui_dir = Path(__file__).parent / "ui" / "build"
		if not ui_dir.exists():
			print("\n  UI가 빌드되지 않았습니다.")
			print("  개발 모드로 실행하세요:\n")
			print(f"    dartlab ai --dev\n")
			print("  또는 빌드 후 실행:")
			print(f"    cd src/dartlab/ui && npm install && npm run build")
			print(f"    dartlab ai\n")
			return

		print(f"\n  DartLab AI")
		print(f"  {url}")
		print()

	# 브라우저 자동 열기
	def open_browser():
		import time
		time.sleep(1.5)
		target = "http://localhost:5400" if args.dev else url
		webbrowser.open(target)

	import threading
	threading.Thread(target=open_browser, daemon=True).start()

	from dartlab.server import run_server
	run_server(host=host, port=port)


if __name__ == "__main__":
	main()
