"""알림 sink 정화 — authoritative(발송 전). landing sanitize.ts 는 SW 렌더 방어심층 미러.

알림 body 는 LLM 프롬프트가 아니라 OS 알림센터 + 화면에 렌더되는 별개 sink → wrap_external_in_result
부적용. 제어/zero-width/양방향(RTL) 제어문자 strip + 공백 정규화 + 길이 cap + (외부 본문은) 출처 라벨.
설계: mainPlan/watcher-notify-platform/02-hub-d1-receiving.md §6.
"""

from __future__ import annotations

import re

# C0/C1 제어(단 0x09~0x0D = tab·LF·VT·FF·CR 보존) + zero-width + RTL/LTR override·isolate + BOM.
# 코드포인트 범위를 chr() 로 빌드 → 소스 순수 ASCII(보이지 않는 문자 리터럴·escape 0).
_STRIP_CODEPOINTS = (
    list(range(0x00, 0x09))
    + list(range(0x0E, 0x20))
    + list(range(0x7F, 0xA0))
    + list(range(0x200B, 0x2010))  # zero-width + LRM/RLM
    + list(range(0x202A, 0x202F))  # LRE..RLO + PDF
    + list(range(0x2060, 0x2065))  # word-joiner + invisible ops
    + list(range(0x2066, 0x206A))  # LRI..PDI
    + [0xFEFF]  # BOM
)
_STRIP_RE = re.compile("[" + "".join(re.escape(chr(c)) for c in _STRIP_CODEPOINTS) + "]")


def sanitize(text: object, max_len: int = 120) -> str:
    """제어·zero-width·양방향 제어문자 strip + 공백 정규화 + 길이 cap."""
    s = _STRIP_RE.sub("", str(text or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return (s[: max_len - 1] + "…") if len(s) > max_len else s


def with_source_label(text: object, label: str, max_len: int = 120) -> str:
    """외부 본문(공시 제목·뉴스 헤드라인)에 출처 라벨 prepend — P2 왓처 토픽용. 라벨 길이 확보 후 cap."""
    body = sanitize(text, max_len=max(8, max_len - len(label) - 3))
    return f"[{label}] {body}" if body else f"[{label}]"
