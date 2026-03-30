"""AI Audit — 다양한 질문으로 ask() 품질을 체계적으로 검증.

analysis audit와 동일 원리: 질문 실행 → 결과 저장 → 차이 확인 → 프롬프트 개선.

사용법::

    uv run python scripts/auditAi.py                    # 전체 질문셋 실행
    uv run python scripts/auditAi.py --id single_review # 특정 질문만
    uv run python scripts/auditAi.py --id scan_growth   # 특정 질문만
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

# dartlab import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import dartlab


# ── 경로 ──

_ROOT = Path(__file__).resolve().parent.parent
_AUDIT_DIR = _ROOT / "data" / "dart" / "auditAi"
_QUESTIONS_PATH = _AUDIT_DIR / "questions.json"
_AUDIT_LOG = _AUDIT_DIR / "audit_log.jsonl"


def _todayDir() -> Path:
    d = _AUDIT_DIR / datetime.now().strftime("%Y-%m-%d")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _loadQuestions(filterId: str | None = None) -> list[dict]:
    with open(_QUESTIONS_PATH, encoding="utf-8") as f:
        qs = json.load(f)
    if filterId:
        qs = [q for q in qs if q["id"] == filterId]
    return qs


def _summarize(answer: str, durationSec: float) -> dict:
    """실행 결과 메타데이터 수집. 판정은 사람이 직접."""
    return {
        "answerLength": len(answer),
        "durationSec": round(durationSec, 1),
        "hasCode": "```python" in answer,
        "hasError": "[실행 오류]" in answer,
        "codeRounds": answer.count("[실행 결과]"),
    }


def _extractCodeBlocks(text: str) -> list[str]:
    return re.findall(r"```python\s*\n(.*?)```", text, re.DOTALL)


def _buildMd(qEntry: dict, answer: str, meta: dict) -> str:
    """사람이 읽을 수 있는 요약 markdown."""
    parts = []
    parts.append(f"# AI Audit: {qEntry['id']}")
    parts.append(f"\n**질문**: {qEntry['q']}")
    parts.append(f"**종목**: {qEntry.get('stock', '없음')}")
    parts.append(f"**기대**: {qEntry.get('expect', '')}")
    parts.append(f"**소요**: {meta.get('durationSec', '?')}초")
    parts.append(f"**코드 실행**: {meta.get('codeRounds', 0)}회")
    if meta.get("hasError"):
        parts.append("**에러**: 있음")

    # 생성된 코드 블록
    codeBlocks = _extractCodeBlocks(answer)
    if codeBlocks:
        parts.append("\n## 생성 코드")
        for i, code in enumerate(codeBlocks, 1):
            parts.append(f"\n### 코드 {i}")
            parts.append(f"```python\n{code.strip()}\n```")

    # 최종 답변 (코드 제외, 해석 부분만)
    interpretation = re.sub(r"```python\s*\n.*?```", "", answer, flags=re.DOTALL)
    interpretation = re.sub(r"```\n\[실행 결과\].*?```", "", interpretation, flags=re.DOTALL)
    interpretation = interpretation.strip()
    if interpretation:
        parts.append("\n## 해석")
        parts.append(interpretation[:3000])

    # 메타
    parts.append("\n## 메타")
    for k, v in meta.items():
        parts.append(f"- {k}: {v}")
    parts.append("\n## 판정 (사람이 직접 작성)")
    parts.append("- [ ] 결과 확인")
    parts.append("- 소견: ")

    return "\n".join(parts)


# ── 메인 실행 ──


def runAudit(filterId: str | None = None) -> None:
    """AI audit 실행."""
    questions = _loadQuestions(filterId)
    if not questions:
        print(f"질문을 찾을 수 없습니다: {filterId}")
        return

    todayDir = _todayDir()
    print(f"AI Audit 시작 — {len(questions)}개 질문, 저장: {todayDir}")

    results = []

    for i, q in enumerate(questions, 1):
        qId = q["id"]
        stock = q.get("stock")
        question = q["q"]

        print(f"\n[{i}/{len(questions)}] {qId}: {question}")

        # Company 생성
        company = None
        if stock:
            try:
                company = dartlab.Company(stock)
                print(f"  Company: {getattr(company, 'corpName', stock)}")
            except (ValueError, RuntimeError) as e:
                print(f"  Company 생성 실패: {e}")

        # ask 실행
        t0 = time.monotonic()
        try:
            answer = (
                dartlab.ask(
                    question,
                    company=company,
                    stream=False,
                )
                or ""
            )
        except Exception as e:
            answer = f"[ask 실행 실패] {e}"
        elapsed = time.monotonic() - t0

        # 메타 수집 (판정은 사람이 직접)
        meta = _summarize(answer, elapsed)
        errTag = " [에러있음]" if meta["hasError"] else ""
        print(f"  완료 ({elapsed:.1f}s, {len(answer)}자, 코드실행 {meta['codeRounds']}회{errTag})")

        # .md 저장
        stockLabel = stock or "none"
        mdPath = todayDir / f"{qId}_{stockLabel}.md"
        mdContent = _buildMd(q, answer, meta)
        mdPath.write_text(mdContent, encoding="utf-8")

        # askLog JSONL 복사 (있으면)
        askLogDir = Path(dartlab.config.dataDir) / "ask_logs"
        if askLogDir.exists():
            logFiles = sorted(askLogDir.glob(f"*_{stockLabel}.jsonl"), reverse=True)
            if logFiles:
                latestLog = logFiles[0]
                dest = todayDir / f"{qId}_{stockLabel}.jsonl"
                shutil.copy2(latestLog, dest)

        # audit_log에 누적
        logEntry = {
            "date": datetime.now().isoformat(),
            "id": qId,
            "question": question,
            "stock": stock,
            "duration": meta["durationSec"],
            "answerLength": meta["answerLength"],
            "codeRounds": meta["codeRounds"],
            "hasError": meta["hasError"],
        }
        with open(_AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(logEntry, ensure_ascii=False) + "\n")

        results.append(logEntry)

    # 요약
    print(f"\n{'=' * 50}")
    print(f"AI Audit 완료 — {len(results)}건 실행")
    for r in results:
        errTag = " [ERR]" if r["hasError"] else ""
        print(f"  {r['id']:20s} {r['duration']:5.1f}s  {r['answerLength']:6d}자  코드{r['codeRounds']}회{errTag}")
    print(f"\n결과 저장: {todayDir}")
    print("각 .md 파일을 읽고 직접 판정하세요.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI Audit")
    parser.add_argument("--id", help="특정 질문 ID만 실행")
    args = parser.parse_args()

    # askLog 활성화
    dartlab.config.askLog = True

    runAudit(filterId=args.id)
