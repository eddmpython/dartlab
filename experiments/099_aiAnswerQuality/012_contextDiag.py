"""실험 012: Context 진단 — skeleton tier에서 전달되는 실제 토큰 양 측정

목적:
- skeleton tier에서 LLM에 전달되는 user_content 크기 측정
- Gemini가 도구를 안 쓰는 이유가 context 풍부함 때문인지 확인

방법:
1. analyze() 이벤트에서 system_prompt + context 수집
2. 토큰 수 추정 (한국어 1자 ≈ 1.5 토큰)

결과: 아래 참조
결론: 아래 참조
실험일: 2026-03-26
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def main():
    import dartlab

    # API key
    apiKey = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not apiKey:
        try:
            from dartlab.engines.ai import get_config
            cfg = get_config("gemini")
            apiKey = cfg.api_key
        except Exception:
            pass
    if apiKey:
        os.environ.setdefault("GEMINI_API_KEY", apiKey)

    print("=" * 60)
    print("012: Context 진단")
    print("=" * 60)

    c = dartlab.Company("005930")

    from dartlab.engines.ai.runtime.core import analyze

    systemPrompt = ""
    userContent = ""
    contexts = []

    for event in analyze(
        c,
        "삼성전자 재무제표를 요약해줘",
        provider="gemini",
        use_tools=True,
        emit_system_prompt=True,
    ):
        if event.kind == "system_prompt":
            if event.data.get("userContent"):
                userContent = event.data["userContent"]
            systemPrompt = event.data.get("text", "")
        elif event.kind == "context":
            contexts.append(event.data)

    print(f"\n시스템 프롬프트 길이: {len(systemPrompt)}자 (~{len(systemPrompt)*1.5:.0f} 토큰)")
    print(f"유저 콘텐츠 길이: {len(userContent)}자 (~{len(userContent)*1.5:.0f} 토큰)")
    print(f"컨텍스트 모듈 수: {len(contexts)}")

    for ctx in contexts:
        module = ctx.get("module", "?")
        text = ctx.get("text", "")
        print(f"  [{module}] {len(text)}자")

    print(f"\n총 입력: {len(systemPrompt) + len(userContent)}자 (~{(len(systemPrompt) + len(userContent))*1.5:.0f} 토큰)")

    # 시스템 프롬프트 내용 미리보기
    print("\n── 시스템 프롬프트 (처음 500자) ──")
    print(systemPrompt[:500])
    print("\n── 유저 콘텐츠 (처음 1000자) ──")
    print(userContent[:1000])


if __name__ == "__main__":
    main()
