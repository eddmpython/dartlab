"""DartLab Streamlit Demo — DART/EDGAR 공시 분석."""

from __future__ import annotations

import gc
import io
import os
import re
from collections import OrderedDict

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

# ── 페이지 설정 ──────────────────────────────────────

st.set_page_config(
    page_title="DartLab — 종목코드 하나로 기업 분석",
    page_icon="📊",
    layout="centered",
)

# ── 커스텀 CSS ────────────────────────────────────────

st.markdown("""
<style>
/* 다크 브랜딩 */
[data-testid="stAppViewContainer"] {
    background: #0a0d16;
}
[data-testid="stHeader"] {
    background: #0a0d16;
}
[data-testid="stSidebar"] {
    background: #0f1219;
}

/* 헤더 */
.dl-header {
    text-align: center;
    padding: 1.5rem 0 1rem;
}
.dl-header img {
    border-radius: 50%;
    box-shadow: 0 0 40px rgba(234,70,71,0.3);
}
.dl-header h1 {
    color: #ea4647;
    font-size: 2.4rem;
    font-weight: 800;
    margin: 0.5rem 0 0.15rem;
    letter-spacing: -0.02em;
}
.dl-header .tagline {
    color: #94a3b8;
    font-size: 1.05rem;
    margin: 0;
}
.dl-header .sub {
    color: #64748b;
    font-size: 0.85rem;
    margin: 0.2rem 0 0;
}

/* 섹션 제목 */
.dl-section {
    color: #ea4647;
    font-weight: 700;
    font-size: 1.15rem;
    border-bottom: 2px solid #ea4647;
    padding-bottom: 0.35rem;
    margin: 1.5rem 0 0.8rem;
}

/* 기업카드 */
.dl-card {
    background: #0f1219;
    border: 1px solid #1e2433;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin: 1rem 0;
}
.dl-card h2 {
    color: #f1f5f9;
    font-size: 1.4rem;
    margin: 0 0 0.8rem;
}
.dl-card .meta {
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
}
.dl-card .meta-item {
    display: flex;
    flex-direction: column;
}
.dl-card .meta-label {
    color: #64748b;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.dl-card .meta-value {
    color: #e2e8f0;
    font-size: 1.1rem;
    font-weight: 600;
}

/* 안내 텍스트 */
.dl-guide {
    color: #64748b;
    font-size: 0.88rem;
    text-align: center;
    margin: 0.2rem 0 0.8rem;
}

/* 데이터 테이블 — column_config로 처리하므로 최소한만 */
[data-testid="stDataFrame"] {
    font-variant-numeric: tabular-nums;
}

/* 푸터 */
.dl-footer {
    text-align: center;
    padding: 2rem 0 1rem;
    border-top: 1px solid #1e2433;
    margin-top: 2rem;
    color: #475569;
    font-size: 0.85rem;
}
.dl-footer a {
    color: #94a3b8;
    text-decoration: none;
    margin: 0 0.5rem;
}
.dl-footer a:hover {
    color: #ea4647;
}

/* 빈 상태 안내 */
.dl-empty {
    text-align: center;
    color: #475569;
    padding: 2rem;
    font-size: 1rem;
}
</style>
""", unsafe_allow_html=True)


# ── 유틸 ──────────────────────────────────────────────


def _toPandas(df):
    """Polars/pandas DataFrame → pandas 변환."""
    if df is None:
        return None
    if hasattr(df, "to_pandas"):
        return df.to_pandas()
    return df


@st.cache_resource(max_entries=_MAX_CACHE)
def _getCompany(code: str):
    """캐시된 Company 반환."""
    gc.collect()
    return dartlab.Company(code)


def _resolveCode(query: str) -> tuple[str | None, str | None]:
    """쿼리 → (종목코드, 에러메시지)."""
    query = query.strip()
    if not query:
        return None, None

    if re.match(r"^\d{6}$", query) or re.match(r"^[A-Z]{1,5}$", query):
        return query, None

    try:
        results = dartlab.search(query)
        if results is None or len(results) == 0:
            return None, f"'{query}' 검색 결과가 없습니다. 종목코드(예: 005930)를 직접 입력해보세요."
        return str(results[0, "stockCode"]), None
    except Exception as e:
        return None, f"검색 실패: {e}"


def _formatDf(df: pd.DataFrame) -> pd.DataFrame:
    """숫자 컬럼을 천단위 콤마 문자열로 변환 (소수점 제거)."""
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
    """DataFrame → Excel bytes."""
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


def _showDataFrame(df: pd.DataFrame, key: str = "", downloadName: str = ""):
    """DataFrame 표시 + 엑셀 다운로드 버튼."""
    if df is None or df.empty:
        st.markdown('<p class="dl-empty">데이터 없음</p>', unsafe_allow_html=True)
        return
    # 포맷팅된 버전으로 표시
    st.dataframe(
        _formatDf(df),
        use_container_width=True,
        hide_index=True,
        key=key or None,
    )
    # 엑셀 다운로드 (원본 숫자 유지)
    if downloadName:
        st.download_button(
            label="📥 Excel 다운로드",
            data=_toExcel(df),
            file_name=f"{downloadName}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_{key}" if key else None,
        )


# ── 프리로드 ──────────────────────────────────────────

@st.cache_resource
def _warmup():
    """listing 캐시 워밍업."""
    try:
        dartlab.search("삼성전자")
    except Exception:
        pass
    return True

_warmup()


# ── 헤더 ──────────────────────────────────────────────

st.markdown(f"""
<div class="dl-header">
    <img src="{_LOGO_URL}" width="88" height="88" alt="DartLab">
    <h1>DartLab</h1>
    <p class="tagline">종목코드 하나. 기업의 전체 이야기.</p>
    <p class="sub">DART · EDGAR 공시 데이터를 구조화하여 제공합니다</p>
</div>
""", unsafe_allow_html=True)


# ── 종목 입력 ─────────────────────────────────────────

col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input(
        "종목코드 또는 회사명",
        placeholder="005930, 삼성전자, AAPL ...",
        label_visibility="collapsed",
    )
with col2:
    analyzeClicked = st.button("분석하기", type="primary", use_container_width=True)

st.markdown('<p class="dl-guide">종목코드(005930) 또는 회사명(삼성전자)을 입력하고 분석하기를 클릭하세요</p>', unsafe_allow_html=True)


# ── 메인 로직 ─────────────────────────────────────────

# 세션 상태 초기화
if "code" not in st.session_state:
    st.session_state.code = ""

if analyzeClicked and query:
    code, err = _resolveCode(query)
    if err:
        st.error(err)
    elif code:
        st.session_state.code = code

code = st.session_state.code

if code:
    try:
        c = _getCompany(code)
    except Exception as e:
        st.error(f"기업 로드 실패: {e}")
        st.stop()

    # ── 기업 카드 ──
    currency = ""
    if hasattr(c, "currency") and c.currency:
        currency = c.currency

    st.markdown(f"""
    <div class="dl-card">
        <h2>🏢 {c.corpName}</h2>
        <div class="meta">
            <div class="meta-item">
                <span class="meta-label">종목코드</span>
                <span class="meta-value">{c.stockCode}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">시장</span>
                <span class="meta-value">{c.market}</span>
            </div>
            {"<div class='meta-item'><span class='meta-label'>통화</span><span class='meta-value'>" + currency + "</span></div>" if currency else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 재무제표 ──
    st.markdown('<div class="dl-section">📊 재무제표</div>', unsafe_allow_html=True)
    st.markdown('<p class="dl-guide">IS(손익계산서) · BS(재무상태표) · CF(현금흐름표) · ratios(재무비율)</p>', unsafe_allow_html=True)

    sheetTab = st.radio(
        "시트 선택",
        ["IS", "BS", "CF", "ratios"],
        horizontal=True,
        label_visibility="collapsed",
    )

    finDf = None
    try:
        raw = getattr(c, sheetTab, None)
        finDf = _toPandas(raw)
    except Exception:
        pass

    _showDataFrame(finDf, key="finance", downloadName=f"{code}_{sheetTab}")

    # ── Sections ──
    topics = []
    try:
        topics = list(c.topics) if c.topics else []
    except Exception:
        pass

    if topics:
        st.markdown('<div class="dl-section">📋 공시 데이터 (Sections)</div>', unsafe_allow_html=True)
        st.markdown('<p class="dl-guide">topic을 선택하면 해당 공시 항목의 기간별 데이터를 표시합니다</p>', unsafe_allow_html=True)

        selectedTopic = st.selectbox(
            "Topic 선택",
            topics,
            label_visibility="collapsed",
        )

        if selectedTopic:
            secDf = None
            secText = ""
            try:
                result = c.show(selectedTopic)
                if result is not None:
                    if hasattr(result, "to_pandas"):
                        secDf = _toPandas(result)
                    else:
                        secText = str(result)
            except Exception as e:
                secText = f"조회 실패: {e}"

            if secDf is not None:
                _showDataFrame(secDf, key="section", downloadName=f"{code}_{selectedTopic}")
            elif secText:
                st.markdown(secText)

    # ── AI Chat ──
    with st.expander("🤖 AI 분석 (OpenAI API 필요)", expanded=False):
        hasAi = bool(os.environ.get("OPENAI_API_KEY"))

        if not hasAi:
            st.info("AI 분석을 사용하려면 HuggingFace Spaces Settings → Variables and secrets에서 `OPENAI_API_KEY`를 설정하세요.")
        else:
            if "messages" not in st.session_state:
                st.session_state.messages = []

            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            if prompt := st.chat_input("재무건전성 분석해줘, 배당 이상 징후 찾아줘 ..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    try:
                        q = f"{code} {prompt}"
                        answer = dartlab.ask(q, stream=False, raw=False)
                        st.markdown(answer or "응답 없음")
                        st.session_state.messages.append({"role": "assistant", "content": answer or "응답 없음"})
                    except Exception as e:
                        errMsg = f"분석 실패: {e}"
                        st.markdown(errMsg)
                        st.session_state.messages.append({"role": "assistant", "content": errMsg})

else:
    # 미입력 상태
    st.markdown("""
    <div class="dl-empty">
        <p style="font-size: 1.2rem; color: #94a3b8;">종목코드를 입력하고 <strong>분석하기</strong>를 클릭하세요</p>
        <p style="color: #475569; margin-top: 0.5rem;">
            예시: <code>005930</code> (삼성전자) · <code>000660</code> (SK하이닉스) · <code>AAPL</code> (Apple)
        </p>
    </div>
    """, unsafe_allow_html=True)


# ── 푸터 ──────────────────────────────────────────────

st.markdown(f"""
<div class="dl-footer">
    <a href="{_BLOG_URL}">📖 초보자 가이드</a> ·
    <a href="{_DOCS_URL}">📘 공식 문서</a> ·
    <a href="{_COLAB_URL}">🔬 Colab</a> ·
    <a href="{_REPO_URL}">⭐ GitHub</a>
    <br><span style="color:#334155; font-size:0.8rem; margin-top:0.5rem; display:inline-block;">
        pip install dartlab · Python 3.12+
    </span>
</div>
""", unsafe_allow_html=True)
