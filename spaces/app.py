"""DartLab Gradio Demo — DART/EDGAR 공시 분석."""

from __future__ import annotations

import gc
import os
import threading
from collections import OrderedDict

import gradio as gr

import dartlab

# ── 설정 ──────────────────────────────────────────────

_MAX_CACHE = 2
_companyCache: OrderedDict = OrderedDict()
_HAS_AI = bool(os.environ.get("OPENAI_API_KEY"))

if _HAS_AI:
    dartlab.llm.configure(provider="openai", api_key=os.environ["OPENAI_API_KEY"])


# ── 유틸 ──────────────────────────────────────────────


def _toPandas(df):
    """Polars/pandas DataFrame → pandas 변환."""
    if df is None:
        return None
    if hasattr(df, "to_pandas"):
        return df.to_pandas()
    return df


def _getCompany(code: str):
    """캐시된 Company 반환, 최대 2개 유지."""
    code = code.strip()
    if code in _companyCache:
        _companyCache.move_to_end(code)
        return _companyCache[code]
    while len(_companyCache) >= _MAX_CACHE:
        _companyCache.popitem(last=False)
        gc.collect()
    c = dartlab.Company(code)
    _companyCache[code] = c
    return c


# ── 프리로드 ──────────────────────────────────────────


def _warmup():
    """백그라운드 listing 캐시 워밍업."""
    try:
        dartlab.search("삼성전자")
    except Exception:
        pass


threading.Thread(target=_warmup, daemon=True).start()


# ── 핸들러: 검색 ─────────────────────────────────────


def handleSearch(keyword: str):
    """종목 검색."""
    if not keyword or not keyword.strip():
        return None
    df = dartlab.search(keyword.strip())
    return _toPandas(df)


# ── 핸들러: 기업 개요 + 재무 ─────────────────────────


def handleLoadCompany(code: str):
    """기업 개요 로드 → (기본정보 markdown, topics 리스트, 재무 DataFrame)."""
    if not code or not code.strip():
        return "종목코드를 입력하세요.", gr.update(choices=[]), None
    try:
        c = _getCompany(code)
    except Exception as e:
        return f"로드 실패: {e}", gr.update(choices=[]), None

    # 기본정보
    info = f"## {c.corpName} ({c.stockCode})\n"
    info += f"- 시장: {c.market}\n"
    if hasattr(c, "currency") and c.currency:
        info += f"- 통화: {c.currency}\n"

    # topics
    topics = []
    try:
        topics = list(c.topics) if c.topics else []
    except Exception:
        pass

    # IS 기본 로드
    finance = None
    try:
        finance = _toPandas(c.IS)
    except Exception:
        pass

    return info, gr.update(choices=topics, value=topics[0] if topics else None), finance


def handleFinance(code: str, sheet: str):
    """재무제표 시트 전환."""
    if not code or not code.strip():
        return None
    try:
        c = _getCompany(code)
    except Exception:
        return None

    lookup = {"BS": "BS", "IS": "IS", "CF": "CF", "ratios": "ratios"}
    attr = lookup.get(sheet, "IS")
    try:
        result = getattr(c, attr, None)
        return _toPandas(result)
    except Exception:
        return None


# ── 핸들러: Sections ──────────────────────────────────


def handleShow(code: str, topic: str):
    """sections show → DataFrame 또는 Markdown."""
    if not code or not topic:
        return None, ""
    try:
        c = _getCompany(code)
        result = c.show(topic)
    except Exception as e:
        return None, f"조회 실패: {e}"

    if result is None:
        return None, "데이터 없음"
    if hasattr(result, "to_pandas"):
        return _toPandas(result), ""
    return None, str(result)


# ── 핸들러: AI Chat ───────────────────────────────────


def handleChat(message: str, history: list, code: str):
    """AI 분석 대화."""
    if not _HAS_AI:
        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": "OPENAI_API_KEY가 설정되지 않았습니다.\n\nHuggingFace Spaces Settings → Variables and secrets에서 설정하세요."},
        ]
        return history, ""

    stockCode = code.strip() if code else None
    if not stockCode:
        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": "먼저 Company 탭에서 종목을 로드하세요."},
        ]
        return history, ""

    # ask() 호출 — raw=True로 Generator 받아서 스트리밍
    try:
        if stockCode:
            query = f"{stockCode} {message}"
        else:
            query = message
        answer = dartlab.ask(query, stream=False, raw=False)
    except Exception as e:
        answer = f"분석 실패: {e}"

    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": answer if answer else "응답 없음"},
    ]
    return history, ""


# ── UI ────────────────────────────────────────────────

_CSS = """
.main-title { text-align: center; margin-bottom: 0.5em; }
.subtitle { text-align: center; color: #666; margin-top: 0; }
"""

with gr.Blocks(
    title="DartLab — DART/EDGAR 공시 분석",
    theme=gr.themes.Soft(),
    css=_CSS,
) as demo:
    gr.Markdown("# DartLab", elem_classes="main-title")
    gr.Markdown(
        "DART 전자공시 + EDGAR — 종목코드 하나로 기업 분석",
        elem_classes="subtitle",
    )

    # 공유 state
    codeState = gr.State("")

    with gr.Tabs():
        # ── Tab 1: 검색 ──
        with gr.Tab("Search"):
            with gr.Row():
                searchInput = gr.Textbox(
                    label="종목 검색",
                    placeholder="삼성전자, AAPL, 005930 ...",
                    scale=4,
                )
                searchBtn = gr.Button("검색", scale=1, variant="primary")
            searchResult = gr.DataFrame(label="검색 결과", interactive=False)

            with gr.Row():
                selectedCode = gr.Textbox(
                    label="종목코드 입력 후 분석",
                    placeholder="005930",
                    scale=4,
                )
                loadBtn = gr.Button("분석하기", scale=1, variant="primary")

            searchBtn.click(handleSearch, inputs=searchInput, outputs=searchResult)
            searchInput.submit(handleSearch, inputs=searchInput, outputs=searchResult)

        # ── Tab 2: 기업 + 재무 ──
        with gr.Tab("Company"):
            companyInfo = gr.Markdown("종목코드를 입력하고 '분석하기'를 클릭하세요.")

            with gr.Row():
                sheetSelect = gr.Dropdown(
                    choices=["IS", "BS", "CF", "ratios"],
                    value="IS",
                    label="재무제표",
                    scale=1,
                )
            financeTable = gr.DataFrame(label="재무제표", interactive=False)

            sheetSelect.change(
                handleFinance,
                inputs=[codeState, sheetSelect],
                outputs=financeTable,
            )

        # ── Tab 3: Sections ──
        with gr.Tab("Sections"):
            gr.Markdown("topic × period 수평화 — 기업의 전체 지도")
            topicSelect = gr.Dropdown(
                choices=[],
                label="Topic",
                interactive=True,
            )
            sectionTable = gr.DataFrame(label="Section 데이터", interactive=False)
            sectionText = gr.Markdown("")

            topicSelect.change(
                handleShow,
                inputs=[codeState, topicSelect],
                outputs=[sectionTable, sectionText],
            )

        # ── Tab 4: AI Chat ──
        with gr.Tab("AI Chat"):
            if not _HAS_AI:
                gr.Markdown(
                    "**AI 분석을 사용하려면** HuggingFace Spaces Settings → "
                    "Variables and secrets에서 `OPENAI_API_KEY`를 설정하세요."
                )
            chatbot = gr.Chatbot(label="AI 분석", type="messages", height=500)
            with gr.Row():
                chatInput = gr.Textbox(
                    label="질문",
                    placeholder="재무건전성 분석해줘, 배당 이상 징후 찾아줘 ...",
                    scale=5,
                )
                chatBtn = gr.Button("전송", scale=1, variant="primary")

            chatBtn.click(
                handleChat,
                inputs=[chatInput, chatbot, codeState],
                outputs=[chatbot, chatInput],
            )
            chatInput.submit(
                handleChat,
                inputs=[chatInput, chatbot, codeState],
                outputs=[chatbot, chatInput],
            )

    # ── 분석하기 버튼 → Company 탭 로드 ──
    loadBtn.click(
        lambda code: code.strip(),
        inputs=selectedCode,
        outputs=codeState,
    ).then(
        handleLoadCompany,
        inputs=selectedCode,
        outputs=[companyInfo, topicSelect, financeTable],
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
