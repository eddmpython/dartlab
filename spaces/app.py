"""DartLab Streamlit Demo — AI 채팅 기반 기업 분석."""

from __future__ import annotations

import gc
import io
import os
import re

import pandas as pd
import streamlit as st

import dartlab

# ── 설정 ──────────────────────────────────────────────

_MAX_CACHE = 2
_LOGO_URL = "https://raw.githubusercontent.com/eddmpython/dartlab/master/.github/assets/logo.png"
_BLOG_URL = "https://eddmpython.github.io/dartlab/blog/dartlab-easy-start/"
_DOCS_URL = "https://eddmpython.github.io/dartlab/docs/getting-started/quickstart"
_COLAB_URL = "https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/01_quickstart.ipynb"
_REPO_URL = "https://github.com/eddmpython/dartlab"

_HAS_OPENAI = bool(os.environ.get("OPENAI_API_KEY"))

if _HAS_OPENAI:
    dartlab.llm.configure(provider="openai", api_key=os.environ["OPENAI_API_KEY"])

# ── 페이지 설정 ──────────────────────────────────────

st.set_page_config(
    page_title="DartLab — AI 기업 분석",
    page_icon=None,
    layout="centered",
)

# ── CSS ───────────────────────────────────────────────

st.markdown("""
<style>
/* 다크 테마 강제 */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stApp"], .main, .block-container {
    background-color: #050811 !important;
    color: #f1f5f9 !important;
}
[data-testid="stHeader"] { background: #050811 !important; }
[data-testid="stSidebar"] { background: #0f1219 !important; }

/* 입력 필드 */
input, textarea,
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea,
[data-baseweb="input"], [data-baseweb="base-input"] {
    background-color: #0f1219 !important;
    color: #f1f5f9 !important;
    border-color: #1e2433 !important;
}

/* 셀렉트/드롭다운 */
[data-baseweb="select"] > div {
    background-color: #0f1219 !important;
    border-color: #1e2433 !important;
    color: #f1f5f9 !important;
}
[data-baseweb="popover"], [data-baseweb="menu"] {
    background-color: #0f1219 !important;
}
[data-baseweb="menu"] li { color: #f1f5f9 !important; }
[data-baseweb="menu"] li:hover { background-color: #1a1f2b !important; }

/* 라디오 */
[data-testid="stRadio"] label { color: #f1f5f9 !important; }

/* 버튼 — dartlab primary 통일 */
button, [data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-secondary"],
[data-testid="stFormSubmitButton"] button,
[data-testid="stChatInputSubmitButton"] {
    background-color: #ea4647 !important;
    color: #fff !important;
    border: none !important;
    font-weight: 600 !important;
}
button:hover, [data-testid="stBaseButton-primary"]:hover,
[data-testid="stChatInputSubmitButton"]:hover {
    background-color: #c83232 !important;
}
[data-testid="stDownloadButton"] button {
    background-color: #0f1219 !important;
    color: #f1f5f9 !important;
    border: 1px solid #1e2433 !important;
}
[data-testid="stDownloadButton"] button:hover {
    border-color: #ea4647 !important;
    color: #ea4647 !important;
    background-color: #0f1219 !important;
}
/* expander 토글은 배경색 제거 */
[data-testid="stExpander"] button {
    background-color: transparent !important;
    color: #f1f5f9 !important;
}

/* Expander */
[data-testid="stExpander"] {
    background-color: #0f1219 !important;
    border-color: #1e2433 !important;
}

/* Chat */
[data-testid="stChatMessage"] {
    background-color: #0a0e17 !important;
    border-color: #1e2433 !important;
}
[data-testid="stChatInput"], [data-testid="stChatInput"] textarea {
    background-color: #0f1219 !important;
    border-color: #1e2433 !important;
    color: #f1f5f9 !important;
}

/* 텍스트 */
p, span, label, h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p {
    color: #f1f5f9 !important;
}
[data-testid="stCaption"] { color: #64748b !important; }

/* DataFrame */
[data-testid="stDataFrame"] { font-variant-numeric: tabular-nums; }

/* 커스텀 */
.dl-header {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
}
.dl-header img {
    border-radius: 50%;
    box-shadow: 0 0 48px rgba(234,70,71,0.25);
}
.dl-header h1 {
    background: linear-gradient(135deg, #ea4647, #f87171, #ea4647);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.4rem !important;
    font-weight: 800 !important;
    margin: 0.5rem 0 0.1rem !important;
    letter-spacing: -0.03em;
}
.dl-header .tagline { color: #94a3b8 !important; font-size: 1rem; margin: 0; }
.dl-header .sub { color: #64748b !important; font-size: 0.82rem; margin: 0.15rem 0 0; }

.dl-card {
    background: linear-gradient(135deg, #0f1219 0%, #0a0d16 100%);
    border: 1px solid #1e2433;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin: 0.8rem 0;
    position: relative;
    overflow: hidden;
}
.dl-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #ea4647, #f87171, #fb923c);
}
.dl-card h3 { color: #f1f5f9 !important; font-size: 1.3rem !important; margin: 0 0 0.8rem !important; }
.dl-card .meta { display: flex; gap: 2.5rem; flex-wrap: wrap; }
.dl-card .meta-item { display: flex; flex-direction: column; gap: 0.1rem; }
.dl-card .meta-label {
    color: #64748b !important; font-size: 0.72rem;
    text-transform: uppercase; letter-spacing: 0.08em;
}
.dl-card .meta-value {
    color: #e2e8f0 !important; font-size: 1.1rem; font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}

.dl-section {
    color: #ea4647 !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    border-bottom: 2px solid #ea4647;
    padding-bottom: 0.3rem;
    margin: 1rem 0 0.6rem;
}

.dl-footer {
    text-align: center;
    padding: 1.5rem 0 0.8rem;
    border-top: 1px solid #1e2433;
    margin-top: 2rem;
    color: #475569 !important;
    font-size: 0.82rem;
}
.dl-footer a { color: #94a3b8 !important; text-decoration: none; margin: 0 0.5rem; }
.dl-footer a:hover { color: #ea4647 !important; }

.dl-hero-glow {
    position: fixed;
    top: 0; left: 50%;
    transform: translateX(-50%);
    width: 600px; height: 400px;
    background: radial-gradient(ellipse at top, rgba(234,70,71,0.05) 0%, transparent 60%);
    pointer-events: none; z-index: 0;
}
</style>
""", unsafe_allow_html=True)


# ── 유틸 ──────────────────────────────────────────────


def _toPandas(df):
    """Polars/pandas DataFrame -> pandas."""
    if df is None:
        return None
    if hasattr(df, "to_pandas"):
        return df.to_pandas()
    return df


def _formatDf(df: pd.DataFrame) -> pd.DataFrame:
    """숫자를 천단위 콤마 문자열로 변환 (소수점 제거)."""
    if df is None or df.empty:
        return df
    result = df.copy()
    for col in result.columns:
        if pd.api.types.is_numeric_dtype(result[col]):
            result[col] = result[col].apply(
                lambda x: f"{int(x):,}" if pd.notna(x) and x == x else ""
            )
    return result


def _toExcel(df: pd.DataFrame) -> bytes:
    """DataFrame -> Excel bytes."""
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


def _showDf(df: pd.DataFrame, key: str = "", downloadName: str = ""):
    """DataFrame 표시 + Excel 다운로드."""
    if df is None or df.empty:
        st.caption("데이터 없음")
        return
    st.dataframe(_formatDf(df), use_container_width=True, hide_index=True, key=key or None)
    if downloadName:
        st.download_button(
            label="Excel 다운로드",
            data=_toExcel(df),
            file_name=f"{downloadName}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_{key}" if key else None,
        )


@st.cache_resource(max_entries=_MAX_CACHE)
def _getCompany(code: str):
    """캐시된 Company."""
    gc.collect()
    return dartlab.Company(code)


# ── 종목코드 추출 ────────────────────────────────────


def _extractCode(message: str) -> str | None:
    """메시지에서 종목코드/회사명 추출."""
    msg = message.strip()

    # 6자리 숫자
    m = re.search(r"\b(\d{6})\b", msg)
    if m:
        return m.group(1)

    # 영문 티커 (단독 대문자 1~5자)
    m = re.search(r"\b([A-Z]{1,5})\b", msg)
    if m:
        return m.group(1)

    # 한글 회사명 → dartlab.search
    cleaned = re.sub(
        r"(에\s*대해|에\s*대한|에대해|좀|의|를|을|은|는|이|가|도|만|부터|까지|하고|이랑|랑|로|으로|와|과|한테|에서|에게)\b",
        " ",
        msg,
    )
    # 불필요한 동사/조동사 제거
    cleaned = re.sub(
        r"\b(알려줘|보여줘|분석|해줘|해봐|어때|보자|볼래|줘|해|좀|요)\b",
        " ",
        cleaned,
    )
    tokens = re.findall(r"[가-힣A-Za-z0-9]+", cleaned)
    # 긴 토큰 우선 (회사명일 가능성 높음)
    tokens.sort(key=len, reverse=True)
    for token in tokens:
        if len(token) >= 2:
            try:
                results = dartlab.search(token)
                if results is not None and len(results) > 0:
                    return str(results[0, "stockCode"])
            except Exception:
                continue
    return None


def _detectTopic(message: str) -> str | None:
    """메시지에서 특정 topic 키워드 감지."""
    topicMap = {
        "배당": "dividend",
        "주주": "majorHolder",
        "대주주": "majorHolder",
        "직원": "employee",
        "임원": "executive",
        "임원보수": "executivePay",
        "보수": "executivePay",
        "세그먼트": "segments",
        "부문": "segments",
        "사업부": "segments",
        "유형자산": "tangibleAsset",
        "무형자산": "intangibleAsset",
        "원재료": "rawMaterial",
        "수주": "salesOrder",
        "제품": "productService",
        "자회사": "subsidiary",
        "종속": "subsidiary",
        "부채": "contingentLiability",
        "우발": "contingentLiability",
        "파생": "riskDerivative",
        "사채": "bond",
        "이사회": "boardOfDirectors",
        "감사": "audit",
        "자본변동": "capitalChange",
        "자기주식": "treasuryStock",
        "사업개요": "business",
        "사업보고": "business",
        "연혁": "companyHistory",
    }
    msg = message.lower()
    for keyword, topic in topicMap.items():
        if keyword in msg:
            return topic
    return None


# ── AI ────────────────────────────────────────────────


def _askAi(stockCode: str, question: str) -> str:
    """AI 질문. OpenAI 우선, HF 무료 fallback."""
    if _HAS_OPENAI:
        try:
            q = f"{stockCode} {question}" if stockCode else question
            answer = dartlab.ask(q, stream=False, raw=False)
            return answer or "응답 없음"
        except Exception as e:
            return f"분석 실패: {e}"

    try:
        from huggingface_hub import InferenceClient
        token = os.environ.get("HF_TOKEN")
        client = InferenceClient(
            model="meta-llama/Llama-3.1-8B-Instruct",
            token=token if token else None,
        )
        context = _buildAiContext(stockCode)
        systemMsg = (
            "당신은 한국 기업 재무 분석 전문가입니다. "
            "아래 재무 데이터를 바탕으로 사용자의 질문에 한국어로 답변하세요. "
            "숫자는 천단위 콤마를 사용하고, 근거를 명확히 제시하세요.\n\n"
            f"{context}"
        )
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": systemMsg},
                {"role": "user", "content": question},
            ],
            max_tokens=1024,
        )
        return response.choices[0].message.content or "응답 없음"
    except Exception as e:
        return f"AI 분석 실패: {e}"


def _buildAiContext(stockCode: str) -> str:
    """AI 컨텍스트 구성."""
    try:
        c = _getCompany(stockCode)
    except Exception:
        return f"종목코드: {stockCode}"

    parts = [f"기업: {c.corpName} ({c.stockCode}), 시장: {c.market}"]
    for name, attr in [("손익계산서", "IS"), ("재무상태표", "BS"), ("재무비율", "ratios")]:
        try:
            df = _toPandas(getattr(c, attr, None))
            if df is not None and not df.empty:
                parts.append(f"\n[{name}]\n{df.head(15).to_string()}")
        except Exception:
            pass
    return "\n".join(parts)


# ── 대시보드 렌더링 ──────────────────────────────────


def _renderCompanyCard(c):
    """기업 카드."""
    currency = ""
    if hasattr(c, "currency") and c.currency:
        currency = c.currency
    currencyHtml = (
        f"<div class='meta-item'><span class='meta-label'>통화</span>"
        f"<span class='meta-value'>{currency}</span></div>"
        if currency else ""
    )
    st.markdown(f"""
    <div class="dl-card">
        <h3>{c.corpName}</h3>
        <div class="meta">
            <div class="meta-item">
                <span class="meta-label">종목코드</span>
                <span class="meta-value">{c.stockCode}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">시장</span>
                <span class="meta-value">{c.market}</span>
            </div>
            {currencyHtml}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _renderFullDashboard(c, code: str):
    """전체 재무 대시보드."""
    _renderCompanyCard(c)

    # 재무제표
    st.markdown('<div class="dl-section">재무제표</div>', unsafe_allow_html=True)
    for label, attr in [("IS (손익계산서)", "IS"), ("BS (재무상태표)", "BS"),
                         ("CF (현금흐름표)", "CF"), ("ratios (재무비율)", "ratios")]:
        with st.expander(label, expanded=(attr == "IS")):
            try:
                df = _toPandas(getattr(c, attr, None))
                _showDf(df, key=f"dash_{attr}", downloadName=f"{code}_{attr}")
            except Exception:
                st.caption("로드 실패")

    # Sections
    topics = []
    try:
        topics = list(c.topics) if c.topics else []
    except Exception:
        pass

    if topics:
        st.markdown('<div class="dl-section">공시 데이터</div>', unsafe_allow_html=True)
        selectedTopic = st.selectbox("topic", topics, label_visibility="collapsed", key="dash_topic")
        if selectedTopic:
            try:
                result = c.show(selectedTopic)
                if result is not None:
                    if hasattr(result, "to_pandas"):
                        _showDf(_toPandas(result), key="dash_sec", downloadName=f"{code}_{selectedTopic}")
                    else:
                        st.markdown(str(result))
            except Exception as e:
                st.caption(f"조회 실패: {e}")


def _renderTopicData(c, code: str, topic: str):
    """특정 topic 데이터만 렌더링."""
    try:
        result = c.show(topic)
        if result is not None:
            if hasattr(result, "to_pandas"):
                _showDf(_toPandas(result), key=f"topic_{topic}", downloadName=f"{code}_{topic}")
            else:
                st.markdown(str(result))
        else:
            st.caption(f"'{topic}' 데이터 없음")
    except Exception as e:
        st.caption(f"조회 실패: {e}")


# ── 프리로드 ──────────────────────────────────────────

@st.cache_resource
def _warmup():
    """listing 캐시."""
    try:
        dartlab.search("삼성전자")
    except Exception:
        pass
    return True

_warmup()


# ── 헤더 ──────────────────────────────────────────────

st.markdown(f"""
<div class="dl-hero-glow"></div>
<div class="dl-header">
    <img src="{_LOGO_URL}" width="80" height="80" alt="DartLab">
    <h1>DartLab</h1>
    <p class="tagline">종목코드 하나. 기업의 전체 이야기.</p>
    <p class="sub">DART / EDGAR 공시 데이터를 구조화하여 제공합니다</p>
</div>
""", unsafe_allow_html=True)


# ── 세션 초기화 ──────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "code" not in st.session_state:
    st.session_state.code = ""


# ── 대시보드 영역 (종목이 있으면 표시) ────────────────

if st.session_state.code:
    try:
        _dashCompany = _getCompany(st.session_state.code)
        _renderFullDashboard(_dashCompany, st.session_state.code)
    except Exception as e:
        st.error(f"기업 로드 실패: {e}")

    st.markdown("---")


# ── 채팅 영역 ────────────────────────────────────────

# 히스토리 표시
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 입력
if prompt := st.chat_input("삼성전자에 대해 알려줘, 배당 현황은? ..."):
    # 사용자 메시지 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 종목코드 추출 시도
    newCode = _extractCode(prompt)
    if newCode and newCode != st.session_state.code:
        st.session_state.code = newCode

    code = st.session_state.code

    if not code:
        # 종목 못 찾음
        reply = "종목을 찾지 못했습니다. 회사명이나 종목코드를 포함해서 다시 질문해주세요.\n\n예: 삼성전자에 대해 알려줘, 005930 분석, AAPL 재무"
        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)
    else:
        # 응답 생성
        with st.chat_message("assistant"):
            # 특정 topic 감지
            topic = _detectTopic(prompt)

            if topic:
                # 특정 topic만 보여주기
                try:
                    c = _getCompany(code)
                    _renderTopicData(c, code, topic)
                except Exception:
                    pass

            # AI 요약
            with st.spinner("분석 중..."):
                aiAnswer = _askAi(code, prompt)
            st.markdown(aiAnswer)

            st.session_state.messages.append({"role": "assistant", "content": aiAnswer})

    # 대시보드 갱신을 위해 rerun
    if newCode and newCode != "":
        st.rerun()


# ── 초기 안내 (대화 없을 때) ─────────────────────────

if not st.session_state.messages and not st.session_state.code:
    st.markdown("""
    <div style="text-align: center; color: #64748b; padding: 2rem 1rem;">
        <p style="font-size: 1.1rem; color: #94a3b8;">
            아래 입력창에 자연어로 질문하세요
        </p>
        <p style="margin-top: 0.5rem;">
            <code>삼성전자에 대해 알려줘</code> &middot;
            <code>005930 분석</code> &middot;
            <code>AAPL 재무 보여줘</code>
        </p>
        <p style="margin-top: 0.3rem; font-size: 0.85rem;">
            종목을 말하면 재무제표/공시 데이터가 바로 표시되고, AI가 분석을 덧붙입니다
        </p>
    </div>
    """, unsafe_allow_html=True)


# ── 푸터 ──────────────────────────────────────────────

st.markdown(f"""
<div class="dl-footer">
    <a href="{_BLOG_URL}">초보자 가이드</a> /
    <a href="{_DOCS_URL}">공식 문서</a> /
    <a href="{_COLAB_URL}">Colab</a> /
    <a href="{_REPO_URL}">GitHub</a>
    <br><span style="color:#334155; font-size:0.78rem; margin-top:0.4rem; display:inline-block;">
        pip install dartlab
    </span>
</div>
""", unsafe_allow_html=True)
