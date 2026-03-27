"""DartLab Gradio Demo — DART/EDGAR 공시 분석."""

from __future__ import annotations

import gc
import os
import re
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

_LOGO_URL = "https://raw.githubusercontent.com/eddmpython/dartlab/master/.github/assets/logo.png"
_BLOG_URL = "https://eddmpython.github.io/dartlab/blog/dartlab-easy-start/"
_DOCS_URL = "https://eddmpython.github.io/dartlab/docs/getting-started/quickstart"
_COLAB_URL = "https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/01_quickstart.ipynb"
_REPO_URL = "https://github.com/eddmpython/dartlab"


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


# ── 핸들러: 통합 분석 ────────────────────────────────


def handleAnalyze(query: str):
    """종목코드 또는 회사명 → 기업정보 + 재무제표 + topics."""
    if not query or not query.strip():
        return (
            "종목코드 또는 회사명을 입력하세요.",
            "",
            None,
            gr.update(choices=[], value=None),
            None,
            "",
        )

    query = query.strip()

    # 종목코드 판별: 6자리 숫자 또는 영문 티커
    if re.match(r"^\d{6}$", query) or re.match(r"^[A-Z]{1,5}$", query):
        code = query
    else:
        # 검색 먼저
        try:
            results = dartlab.search(query)
            if results is None or len(results) == 0:
                return (
                    f"'{query}' 검색 결과가 없습니다. 종목코드(예: 005930)나 티커(예: AAPL)를 직접 입력해보세요.",
                    "",
                    None,
                    gr.update(choices=[], value=None),
                    None,
                    "",
                )
            code = str(results[0, "stockCode"])
        except Exception as e:
            return (
                f"검색 실패: {e}",
                "",
                None,
                gr.update(choices=[], value=None),
                None,
                "",
            )

    # Company 로드
    try:
        c = _getCompany(code)
    except Exception as e:
        return (
            f"기업 로드 실패: {e}",
            "",
            None,
            gr.update(choices=[], value=None),
            None,
            "",
        )

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

    topicUpdate = gr.update(
        choices=topics,
        value=topics[0] if topics else None,
    )

    return info, code, finance, topicUpdate, None, ""


def handleFinance(code: str, sheet: str):
    """재무제표 시트 전환."""
    if not code or not code.strip():
        return None
    try:
        c = _getCompany(code)
    except Exception:
        return None

    lookup = {"IS": "IS", "BS": "BS", "CF": "CF", "ratios": "ratios"}
    attr = lookup.get(sheet, "IS")
    try:
        result = getattr(c, attr, None)
        return _toPandas(result)
    except Exception:
        return None


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
            {
                "role": "assistant",
                "content": "OPENAI_API_KEY가 설정되지 않았습니다.\n\nHuggingFace Spaces Settings → Variables and secrets에서 설정하세요.",
            },
        ]
        return history, ""

    stockCode = code.strip() if code else None
    if not stockCode:
        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": "먼저 상단에서 종목을 분석하세요."},
        ]
        return history, ""

    try:
        query = f"{stockCode} {message}" if stockCode else message
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
/* ── dartlab 브랜딩 ── */
.gradio-container {
    background: #0a0d16 !important;
    max-width: 960px !important;
}
.main-header {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
}
.main-header img {
    display: inline-block;
    border-radius: 50%;
    box-shadow: 0 0 32px rgba(234,70,71,0.25);
}
.main-header h1 {
    color: #ea4647 !important;
    font-size: 2.2rem !important;
    margin: 0.5rem 0 0.2rem !important;
    font-weight: 800 !important;
}
.main-header .tagline {
    color: #94a3b8;
    font-size: 1.05rem;
    margin: 0;
}
.section-label {
    color: #ea4647 !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    margin: 1rem 0 0.3rem !important;
    border-bottom: 1px solid #1e2433;
    padding-bottom: 0.3rem;
}
.footer-links {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
    color: #64748b;
    font-size: 0.9rem;
}
.footer-links a {
    color: #94a3b8 !important;
    text-decoration: none;
    margin: 0 0.5rem;
}
.footer-links a:hover {
    color: #ea4647 !important;
}
"""

_THEME = gr.themes.Base(
    primary_hue=gr.themes.Color(
        c50="#fef2f2", c100="#fee2e2", c200="#fecaca", c300="#fca5a5",
        c400="#f87171", c500="#ea4647", c600="#dc2626", c700="#c83232",
        c800="#991b1b", c900="#7f1d1d", c950="#450a0a",
    ),
    neutral_hue=gr.themes.Color(
        c50="#f8fafc", c100="#f1f5f9", c200="#e2e8f0", c300="#cbd5e1",
        c400="#94a3b8", c500="#64748b", c600="#475569", c700="#334155",
        c800="#1e293b", c900="#0f172a", c950="#0a0d16",
    ),
    font=("system-ui", "-apple-system", "sans-serif"),
).set(
    body_background_fill="#0a0d16",
    body_text_color="#f1f5f9",
    block_background_fill="#0f1219",
    block_border_color="#1e2433",
    input_background_fill="#1a1f2b",
    button_primary_background_fill="#ea4647",
    button_primary_text_color="#ffffff",
    button_secondary_background_fill="#1a1f2b",
    button_secondary_text_color="#f1f5f9",
    button_secondary_border_color="#1e2433",
)


with gr.Blocks(
    title="DartLab — 종목코드 하나로 기업 분석",
    theme=_THEME,
    css=_CSS,
) as demo:

    # ── 헤더 ──
    gr.HTML(f"""
    <div class="main-header">
        <img src="{_LOGO_URL}" width="100" height="100" alt="DartLab">
        <h1>DartLab</h1>
        <p class="tagline">종목코드 하나. 기업의 전체 이야기.</p>
    </div>
    """)

    # ── 공유 state ──
    codeState = gr.State("")

    # ── 통합 입력 ──
    with gr.Row():
        queryInput = gr.Textbox(
            label="종목코드 또는 회사명",
            placeholder="삼성전자, 005930, AAPL ...",
            scale=4,
        )
        analyzeBtn = gr.Button("분석하기", scale=1, variant="primary", size="lg")

    # ── 기업 정보 ──
    companyInfo = gr.Markdown("종목코드를 입력하고 **분석하기**를 클릭하세요.")

    # ── 재무제표 ──
    gr.Markdown("### 재무제표", elem_classes="section-label")
    with gr.Row():
        sheetSelect = gr.Dropdown(
            choices=["IS", "BS", "CF", "ratios"],
            value="IS",
            label="시트",
            scale=1,
        )
    financeTable = gr.DataFrame(label="재무제표", interactive=False)

    # ── Sections ──
    gr.Markdown("### Sections — topic × period 수평화", elem_classes="section-label")
    topicSelect = gr.Dropdown(
        choices=[],
        label="Topic",
        interactive=True,
    )
    sectionTable = gr.DataFrame(label="Section 데이터", interactive=False)
    sectionText = gr.Markdown("")

    # ── AI Chat (접힘) ──
    with gr.Accordion("AI 분석 (OpenAI API 필요)", open=False):
        if not _HAS_AI:
            gr.Markdown(
                "**AI 분석을 사용하려면** HuggingFace Spaces Settings → "
                "Variables and secrets에서 `OPENAI_API_KEY`를 설정하세요."
            )
        chatbot = gr.Chatbot(label="AI 분석", type="messages", height=400)
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

    # ── 푸터 ──
    gr.HTML(f"""
    <div class="footer-links">
        <a href="{_BLOG_URL}">📖 설치 가이드</a> ·
        <a href="{_DOCS_URL}">📘 공식 문서</a> ·
        <a href="{_COLAB_URL}">🔬 Colab</a> ·
        <a href="{_REPO_URL}">⭐ GitHub</a>
    </div>
    """)

    # ── 이벤트 바인딩 ──
    analyzeBtn.click(
        handleAnalyze,
        inputs=queryInput,
        outputs=[companyInfo, codeState, financeTable, topicSelect, sectionTable, sectionText],
    )
    queryInput.submit(
        handleAnalyze,
        inputs=queryInput,
        outputs=[companyInfo, codeState, financeTable, topicSelect, sectionTable, sectionText],
    )

    sheetSelect.change(
        handleFinance,
        inputs=[codeState, sheetSelect],
        outputs=financeTable,
    )

    topicSelect.change(
        handleShow,
        inputs=[codeState, topicSelect],
        outputs=[sectionTable, sectionText],
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
