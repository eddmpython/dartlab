"""정기보고서 도시에 verdict-tone 금지 lint (터미널 surface + cardGuide).

도시에(periodic-report-dossier)는 "분포 사실, 판정 아님" 규율 위에 선다 — 우측 레일 자기이력
문장·카드 가이드 어디에도 *회사별 매수/매도·우량/부실 처방 톤*을 금지한다(PRD 03 §4.2·07 §7
NEVER-CLAIM). 본 guard가 그 grep 계약을 기계 강제한다.

★스캔 표면 한정 (leaf CI red 회피):
    터미널 surface 의 사용자-facing `*.svelte` + 카드 해석 SSOT `cardGuide.ts` 뿐이다.
    src `.py`(엔진 leaf 의 정당한 signal="underpriced" 등)·백테스터 `.ts`(매수/매도선=전략
    어휘)·밸류에이션 패널(동종 멀티플 '저평가/고평가' 서술)은 의도적으로 *대상 아님* —
    잡으면 CI red 이므로. 그래서 금지 토큰은 *회사별 verdict 로만 쓰이는 합성형*만 — bare
    우량/매수/저평가(교육·백테스터·밸류에이션 정당 중첩)는 ban 하지 않는다.

검사 (전부 현재 부재 = green no-op, 미래 verdict-creep 발화):
    우량주·부실주·주주친화·좋은 고용주 (회사 라벨) · 매수의견·매도의견·적극매수·강력매수·
    강력추천·비중확대·비중축소 (분석가 레이팅). 합성형이라 부정형 면책문("매수/매도 신호 금지")·
    backtester("매수선")·valuation("저평가 여력")을 오검출하지 않는다(allowlist 휴리스틱 불요).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# 스캔 대상 — 터미널 surface .svelte + cardGuide.ts (PRD 08 §2 G3 명세 범위)
_TERMINAL_DIR = REPO_ROOT / "ui" / "packages" / "surfaces" / "src" / "terminal"
_CARD_GUIDE = _TERMINAL_DIR / "lib" / "cardGuide.ts"

# 금지 토큰 → 사유. 전부 *회사별 verdict 합성형* — bare 토큰(우량/매수/저평가)은 교육·전략·밸류
# 정당 중첩이라 제외. 합성형이라 부정형 면책문·도메인 어휘를 오검출하지 않는다.
_BANNED: tuple[tuple[str, str], ...] = (
    ("우량주", "회사 등급 처방 — 분포 사실로 (도시에는 판정 아님)"),
    ("부실주", "회사 등급 처방 — 분포 사실로"),
    ("주주친화", "거버넌스 verdict — 자사주/배당은 서술(올라가면/내려가면)로"),
    ("좋은 고용주", "고용 verdict — 계약직/급여는 서술로 (고용안정 단정 금지)"),
    ("좋은고용주", "고용 verdict — 계약직/급여는 서술로"),
    ("매수의견", "분석가 레이팅 — 도시에 금지"),
    ("매도의견", "분석가 레이팅 — 도시에 금지"),
    ("적극매수", "분석가 레이팅 — 도시에 금지"),
    ("강력매수", "분석가 레이팅 — 도시에 금지"),
    ("강력추천", "투자권유 — 도시에 금지"),
    ("비중확대", "분석가 레이팅(overweight) — 도시에 금지"),
    ("비중축소", "분석가 레이팅(underweight) — 도시에 금지"),
)

# 라인 주석에서 *금지 토큰 목록 자체*를 기술하는 본 가드 호환 — 메타 라인은 면제
# (예: cardGuide convention 주석이 '매수/매도 금지'를 설명). 토큰 나열 메타는 합성형이 아니라 bare 라 자연 면제되나,
# 합성형을 면책문에 쓰는 미래 케이스 대비 per-line 면제 마커.
_EXEMPT_LINE = re.compile(r"(금지|아님|아닌|NEVER-CLAIM|dossierVerdictLint)")


def _scan_files() -> list[Path]:
    files: list[Path] = []
    if _TERMINAL_DIR.is_dir():
        files.extend(sorted(_TERMINAL_DIR.rglob("*.svelte")))
    if _CARD_GUIDE.is_file():
        files.append(_CARD_GUIDE)
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description="도시에 verdict-tone 금지 lint")
    ap.add_argument("--strict", action="store_true", help="위반 시 exit 1")
    args = ap.parse_args()

    violations: list[str] = []
    files = _scan_files()
    for fp in files:
        try:
            text = fp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if _EXEMPT_LINE.search(line):
                continue
            for token, reason in _BANNED:
                if token in line:
                    rel = fp.relative_to(REPO_ROOT).as_posix()
                    violations.append(f"  {rel}:{lineno}  '{token}' — {reason}")

    if violations:
        print(f"[dossierVerdictLint] FAIL — verdict-tone 토큰 {len(violations)}건 (도시에=분포 사실, 판정 아님):")
        print("\n".join(violations))
        print("  → 서술적 읽기(올라가면/내려가면)로 바꾸거나, 면책문이면 '금지/아님'을 같은 줄에 둔다.")
        return 1 if args.strict else 0

    print(f"[dossierVerdictLint] PASS — {len(files)}개 surface 파일, verdict-tone 토큰 0건.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
