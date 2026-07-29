"""Silent-fail 패턴 lint — 2026-04-19 사고 class 재유입 차단.

번들 리소스 로더가 파일 부재 시 조용히 빈 값(`{}`, `[]`)을 리턴하면 상위
파이프라인이 "데이터 없음" 과 "파일 누락" 을 구분 못 해 사용자 crash 로
이어질 수 있다. 해당 패턴을 lint 해서 새 코드에서 재유입을 차단한다.

탐지 패턴 (AST 기반, 보수적):
    1. `if not X.exists(): return {}` / `return []`  — 파일 부재 silent fallback
    2. `except FileNotFoundError: return {}` / `return []`
    3. `try: ... open(...) ... except (...): return {}/[]`  — 동일 패턴

허용 (화이트리스트):
    - 사용자 입력 파싱 (tests, scripts/dev)
    - ai/settings/secrets.py 같은 옵셔널 설정 로더
    - 이미 명시적으로 허용된 경로

사용법::

    python tests/audit/checkSilentFail.py  # src/dartlab/ 전체 스캔
    python tests/audit/checkSilentFail.py --warn-only  # 경고만, exit 0

종료 코드: 0 깨끗 / 1 위반 발견 / 2 입력 오류
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "dartlab"

# 옵셔널 리소스 로더 — 누락이 정상 동작 (사용자 설정/선택 데이터 등)
_ALLOWLIST_FILES: frozenset[str] = frozenset(
    {
        # 사용자 설정/인증 파일 (옵셔널)
        "ai/settings/secrets.py",
        "ai/settings/profile.py",
        "ai/providers/support/codexCli.py",
        "ai/tools/__init__.py",
        "ai/tools/listEngineGaps.py",
        "channel/devtunnel.py",
        "server/api/ai.py",
        # blog/05-company-reports/ 디렉토리는 옵셔널 — 분석 회사 블로그 글이 없으면
        # 빈 리스트가 정상. 회사 헤더 블로그 태그용 노출 헬퍼.
        "server/api/company.py",
        # 런타임 데이터 캐시 (HF/API 응답 파일) — 없으면 빈 결과가 정상
        "synth/bottomUpBeta.py",  # peer 추출 헬퍼 — finance.parquet 없으면 peer 0 정상
        "gather/domains/naver.py",
        "gather/domains/yahooChart.py",
        "providers/dart/openapi/allFilingsCollector.py",
        "providers/dart/openapi/batch.py",
        "gather/dart/keys.py",
        "providers/dart/accessor/financeDocAccessor.py",
        "providers/dart/ops/insiderTrades.py",
        "providers/mappers/scanner.py",
        "providers/edgar/openapi/batch.py",
        "providers/edgar/docs/notesParsers.py",
        # tickers.parquet 옵셔널 universe 로더 — 없으면 빈 universe(빌드 대상 0)가 정상(loud-fail 부적합).
        "providers/edgar/panel/build/builder.py",
        "providers/edgar/report/employee.py",
        "scan/watch/scanner.py",
        # gather 도메인 — 외부 API 응답 (네트워크 실패 시 빈 결과가 정상)
        "gather/domains/dartApi.py",
        "gather/domains/fdr.py",
        "gather/sources/insider.py",
        "gather/sources/news.py",
        "core/providers/secrets.py",
        # credit runtime history/audit — 사용자 생성 데이터
        "credit/monitoring/audit.py",
        "credit/monitoring/history.py",
        # scan builder — 프리빌드 runtime 상태 (데이터 없으면 스킵)
        "scan/builder/core.py",
        "scan/builders/edgar/builder.py",
        # corpProfile.parquet 는 선택 prebuild 데이터. 없으면 raw finance 추정으로 보강.
        "scan/builders/kr/fiscal.py",
        # _scanBuildState.json 증분 ledger 로더 — 부재 = 부트스트랩(전량 seed 회피) semantic, loud-fail 부적합.
        "scan/builders/kr/common.py",
        # note 횡단 프리빌드 빌더. panel 디렉토리·parquet 부재 = 빌드 대상 0 = 빈 결과 정상(scan 빌더 동형, batch-safe skip).
        "scan/builders/kr/notes.py",
        "scan/edgar/builder.py",
        "scan/io/parquet.py",
        # AI 런타임 상태 저장 (없으면 첫 실행)
        "ai/__init__.py",
        "skills/registry.py",
        # analysis/forecast/core 런타임 캐시 (HF seed/backtest output)
        "analysis/forecast/forwardTest.py",
        "core/mappers/scanner.py",
        # AI provider 옵셔널 (Ollama 등 로컬 LLM)
        "ai/providers/ollama.py",
        # analysis runtime 결과 (이전 스토리 캐시)
        "analysis/financial/storyValidation.py",
        # industry build pipeline — 단계별 중간 산출물 (없으면 이전 단계 재실행)
        "industry/build/delta.py",
        "industry/build/enrichCompany.py",
        "industry/build/pipeline.py",
        "industry/build/stage3_docs.py",
        "industry/build/stage4_review.py",
        # artifacts.loadProjectionRules — 알려진 chapter 만 loud-fail, 미등록은 빈 dict (의도적)
        # sections 사전빌드/다운로드 데이터 로더 — 번들 리소스가 아니라 HF 다운로드/
        # 로컬 빌드 산출물 (data/dart/panel/{code}.parquet · original zip). 부재 =
        # "아직 빌드/다운로드 안 됨" = 빈 결과가 정상 semantic. builder 계열은 warning 로그.
        "filings/dart/build/builder.py",
        # panel per-corp 빌더 — zip dir 부재 = 해당 종목 "아직 수집 안 됨" = 빈 결과 정상(warning 로그).
        # 번들 리소스 아니라 종목별 빌더라 batch-safe skip 이 정공 (loud-fail 시 전종목 batch 깨짐).
        "providers/dart/panel/build/builder.py",
        # panel 비교 unit hint — 종목별 panel cache 부재면 scale 추정 없음이 정상.
        "providers/dart/panel/compare.py",
        # frame/inventory.py. 회사별 report parquet(_dataDir("report")/{code}.parquet) 열거. report 없는
        # 종목은 빈 결과가 정상(종목별 옵셔널 데이터, 번들 리소스 아님). loud-fail 시 전종목 인벤토리 census
        # 가 깨짐(panel/build/builder 동형 batch-safe skip 이 정공).
        "frame/inventory.py",
        # search index builders — panel/content index 는 선택적 로컬/HF 산출물.
        # 부재 = 아직 빌드/동기화 대상 0건, 검색 caller 가 "인덱스 없음" 메시지를 반환.
        "providers/dart/search/fieldIndexRebuild.py",
        # search local activation pointer / previous manifest 는 선택 운영 산출물.
        # 첫 설치/첫 promote 에서는 부재가 정상이라 loud-fail 하면 bootstrap 이 깨진다.
        "providers/dart/search/localUpdate.py",
        "providers/dart/search/ngramIndex.py",
        "providers/dart/search/publishIndex.py",
        "providers/edgar/docs/sections/sectionsStorage.py",
        # quant bottom-up beta peer 추출 — scan finance parquet 없으면 섹터 기본 beta fallback
        "quant/risk/bottomUpBeta.py",
        # skill spec/validate 런타임 — spec 디렉토리 부재 시 빈 결과가 옵셔널 semantic
        "skills/validateSkills.py",
        # capability 라이브 빌더 — 축 registry introspection 이 install-robust 하게 try/except
        "reference/capability/builder.py",
        # lineage / credential lifecycle — 사용자 생성 데이터 (~/.dartlab/), 부재 = 첫 실행
        "core/dataAudit.py",
        "core/credentialLifecycle.py",
        # 메모리 dialectic / sessionIndex — 사용자 메모리 디렉토리 (~/.claude/memory/), 부재 = 빈
        "ai/memory/dialectic/feedbackSignals.py",
        "ai/memory/dialectic/userProfile.py",
        "ai/memory/sessionIndex/search.py",
        # gather 증분 수집 상태 — 기존 parquet 에서 "이미 수집된 period/accession" 세트 추출.
        # 첫 실행(파일 부재) = "아직 0건 수집" = 빈 세트 정상(loud-fail 시 전종목 batch 깨짐).
        "gather/dart/batch.py",
        "gather/edgar/batch.py",
        # DART API 키 .env 파서 — env var 가 1차 소스, .env 부재 = 멀티키 0 = 빈 list 정상.
        "gather/dart/keys.py",
        "gather/original/dart/keys.py",
        # pipeline changed 매니페스트 / hash 스냅샷 — 옵셔널 산출물. 부재 = "변경 없음"/"첫 실행" 정상.
        "pipeline/changed.py",
        "pipeline/hashing.py",
    }
)


class _SilentFailVisitor(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.offenders: list[tuple[int, str]] = []

    def _isEmptyCollection(self, node: ast.expr) -> bool:
        """`{}` / `[]` / `dict()` / `list()` / `set()` 판정."""
        if isinstance(node, ast.Dict) and not node.keys:
            return True
        if isinstance(node, ast.List) and not node.elts:
            return True
        if isinstance(node, ast.Set) and not node.elts:
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"dict", "list", "set"} and not node.args and not node.keywords:
                return True
        return False

    def _findEmptyReturn(self, stmts: list[ast.stmt]) -> ast.Return | None:
        for s in stmts:
            if isinstance(s, ast.Return) and s.value is not None and self._isEmptyCollection(s.value):
                return s
        return None

    def visit_If(self, node: ast.If):
        # Pattern 1: `if not X.exists(): return {}/[]`
        test = node.test
        isExistsCheck = False
        if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
            operand = test.operand
            if isinstance(operand, ast.Call) and isinstance(operand.func, ast.Attribute):
                if operand.func.attr in {"exists", "is_file", "is_dir"}:
                    isExistsCheck = True
        if isExistsCheck:
            ret = self._findEmptyReturn(node.body)
            if ret is not None:
                self.offenders.append(
                    (
                        ret.lineno,
                        f"`if not X.exists(): return {ast.unparse(ret.value)}` "
                        f"— 파일 부재 시 silent-fail. loud-fail (FileNotFoundError) 권장.",
                    )
                )
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        # Pattern 2/3: `except FileNotFoundError (or tuple with): return {}/[]`
        exType = node.type
        isFileRelated = False
        if isinstance(exType, ast.Name) and exType.id in {"FileNotFoundError", "OSError", "IOError"}:
            isFileRelated = True
        elif isinstance(exType, ast.Tuple):
            for elt in exType.elts:
                if isinstance(elt, ast.Name) and elt.id in {
                    "FileNotFoundError",
                    "OSError",
                    "IOError",
                }:
                    isFileRelated = True
                    break
        if isFileRelated:
            ret = self._findEmptyReturn(node.body)
            if ret is not None:
                self.offenders.append(
                    (
                        ret.lineno,
                        f"`except (FileNotFoundError, ...): return {ast.unparse(ret.value)}` "
                        f"— silent-fail. 번들 리소스라면 loud-fail 권장.",
                    )
                )
        self.generic_visit(node)


def scanFile(path: Path) -> list[tuple[int, str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return []
    visitor = _SilentFailVisitor(str(path))
    visitor.visit(tree)
    return visitor.offenders


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="silent-fail 패턴 lint")
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="위반 발견해도 exit 0 (경고만)",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="검사할 파일/디렉토리 (기본: src/dartlab)",
    )
    args = parser.parse_args()

    roots = args.paths or [_SRC_ROOT]
    targets: list[Path] = []
    for root in roots:
        if root.is_file() and root.suffix == ".py":
            targets.append(root)
        elif root.is_dir():
            targets.extend(root.rglob("*.py"))

    # 화이트리스트 필터
    filtered: list[Path] = []
    for p in targets:
        rel = p.resolve().relative_to(_SRC_ROOT).as_posix() if _SRC_ROOT in p.resolve().parents else None
        if rel and rel in _ALLOWLIST_FILES:
            continue
        if "__pycache__" in p.parts or "/_reference/" in p.as_posix():
            continue
        filtered.append(p)

    totalOffenders: list[tuple[Path, int, str]] = []
    for path in filtered:
        for line, msg in scanFile(path):
            totalOffenders.append((path, line, msg))

    if not totalOffenders:
        print(f"[check-silent-fail] OK — {len(filtered)}개 파일 스캔, 위반 없음")
        return 0

    print(f"[check-silent-fail] ⚠ {len(totalOffenders)}건 silent-fail 패턴 발견:")
    for path, line, msg in totalOffenders:
        rel = path.resolve().relative_to(_SRC_ROOT.parent).as_posix()
        print(f"  {rel}:{line}  {msg}")
    print()
    print("2026-04-19 사고 class 방어 — 번들 리소스 로더는 loud-fail 해야 합니다.")
    print("화이트리스트 가능한 옵셔널 로더라면 checkSilentFail.py 의 _ALLOWLIST_FILES 에 추가.")
    return 0 if args.warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
