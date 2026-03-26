"""AI 보조 파싱 — 기존 파서 출력을 AI가 후처리하여 강화.

기존 파서를 교체하지 않는다. 파서가 생산한 DataFrame/텍스트를
LLM이 해석·요약·검증하는 후처리 레이어.

기존 LLM provider 시스템 재사용: dartlab.llm.configure() 설정을 그대로 활용.

사용법::

    import dartlab
    dartlab.llm.configure(provider="ollama", model="llama3.2")

    c = dartlab.Company("005930")

    # 요약
    dartlab.llm.ai.summarize(c.IS)

    # 계정 해석
    dartlab.llm.ai.interpret_accounts(c.BS)

    # 이상치 탐지
    dartlab.llm.ai.detect_anomalies(c.dividend)

    # 텍스트 분류
    dartlab.llm.ai.classify_text(c.mdna)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl

from dartlab.ai.metadata import get_meta

_AI_PARSER_ERRORS = (ImportError, OSError, RuntimeError, TypeError, ValueError)

# ══════════════════════════════════════
# 내부 LLM 호출
# ══════════════════════════════════════


def _llm_call(prompt: str, system: str = "") -> str:
    """내부 LLM 호출. 글로벌 설정된 provider 사용."""
    from dartlab.ai import get_config
    from dartlab.ai.providers import create_provider

    config = get_config()
    provider = create_provider(config)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = provider.complete(messages)
    return response.answer


# ══════════════════════════════════════
# 요약
# ══════════════════════════════════════


def summarize(
    data: pl.DataFrame | str | list,
    *,
    module_name: str | None = None,
    lang: str = "ko",
) -> str:
    """DataFrame, 텍스트, 또는 리스트를 2~5문장으로 요약.

    Args:
            data: DataFrame (마크다운 변환 후 요약), str (직접 요약), list (결합 후 요약)
            module_name: 메타데이터 활용을 위한 모듈명
            lang: "ko" 또는 "en"

    Returns:
            요약 텍스트 (2~5문장)
    """
    from dartlab.ai.context.builder import df_to_markdown

    # 데이터 → 텍스트
    if isinstance(data, pl.DataFrame):
        meta = get_meta(module_name) if module_name else None
        text = df_to_markdown(data, meta=meta)
    elif isinstance(data, list):
        parts = []
        for item in data[:10]:
            if hasattr(item, "title") and hasattr(item, "text"):
                parts.append(f"[{item.title}]\n{item.text[:500]}")
            else:
                parts.append(str(item)[:500])
        text = "\n\n".join(parts)
    else:
        text = str(data)[:3000]

    # 메타데이터 컨텍스트
    context = ""
    if module_name:
        meta = get_meta(module_name)
        if meta:
            context = f"이 데이터는 '{meta.label}'입니다. {meta.description}\n\n"

    system = "한국어로 답변하세요." if lang == "ko" else "Answer in English."

    prompt = (
        f"{context}"
        f"다음 데이터를 2~5문장으로 핵심만 요약하세요.\n"
        f"수치를 구체적으로 인용하고, 주요 추세와 특이사항을 포함하세요.\n\n"
        f"{text}"
    )

    return _llm_call(prompt, system=system)


# ══════════════════════════════════════
# 계정 해석
# ══════════════════════════════════════


def interpret_accounts(
    df: pl.DataFrame,
    *,
    account_col: str = "계정명",
    module_name: str | None = None,
) -> pl.DataFrame:
    """재무제표에 '설명' 컬럼 추가. 각 계정명의 의미를 LLM이 해석.

    LLM 1회 호출로 전체 계정 일괄 해석 (개별 호출 아님).

    Args:
            df: 계정명 컬럼이 있는 재무제표 DataFrame
            account_col: 계정명 컬럼명
            module_name: "BS", "IS", "CF" 등

    Returns:
            원본 + '설명' 컬럼이 추가된 DataFrame
    """
    if account_col not in df.columns:
        return df

    accounts = df[account_col].to_list()
    if not accounts:
        return df

    # 유일한 계정명만 추출
    unique_accounts = list(dict.fromkeys(accounts))

    module_hint = ""
    if module_name:
        meta = get_meta(module_name)
        if meta:
            module_hint = f"이 데이터는 '{meta.label}'({meta.description})입니다.\n"

    prompt = (
        f"{module_hint}"
        f"다음 K-IFRS 계정명 각각에 대해 한 줄(20자 이내)로 설명하세요.\n"
        f"형식: 계정명: 설명\n\n" + "\n".join(unique_accounts)
    )

    answer = _llm_call(prompt, system="한국어로 답변하세요. 각 계정에 대해 간결하게 설명만 하세요.")

    # 응답 파싱: "계정명: 설명" 형태
    desc_map: dict[str, str] = {}
    for line in answer.strip().split("\n"):
        line = line.strip().lstrip("- ").lstrip("· ")
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip()
            val = parts[1].strip()
            desc_map[key] = val

    # 매핑
    descriptions = []
    for acct in accounts:
        desc = desc_map.get(acct, "")
        if not desc:
            # 부분 매칭 시도
            for k, v in desc_map.items():
                if k in acct or acct in k:
                    desc = v
                    break
        descriptions.append(desc)

    return df.with_columns(pl.Series("설명", descriptions))


# ══════════════════════════════════════
# 이상치 탐지
# ══════════════════════════════════════


@dataclass
class Anomaly:
    """탐지된 이상치."""

    column: str
    year: str
    value: Any
    prev_value: Any
    change_pct: float | None
    anomaly_type: str  # "spike", "sign_reversal", "outlier", "missing"
    severity: str = "medium"  # "high", "medium", "low"
    description: str = ""


def _statistical_prescreen(
    df: pl.DataFrame,
    *,
    year_col: str = "year",
    threshold_pct: float = 50.0,
) -> list[Anomaly]:
    """순수 통계 기반 이상치 사전 탐지 (LLM 없이 동작).

    탐지 기준:
    - YoY 변동 threshold_pct% 초과
    - 부호 반전 (양→음, 음→양)
    - 2σ 이탈
    """
    if year_col not in df.columns:
        return []

    df_sorted = df.sort(year_col)
    numeric_cols = [
        c for c in df.columns if c != year_col and df[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32)
    ]

    anomalies = []
    years = df_sorted[year_col].to_list()

    for col in numeric_cols:
        values = df_sorted[col].to_list()
        non_null = [v for v in values if v is not None]

        if len(non_null) < 2:
            continue

        mean_val = sum(non_null) / len(non_null)
        if len(non_null) > 1:
            variance = sum((v - mean_val) ** 2 for v in non_null) / (len(non_null) - 1)
            std_val = variance**0.5
        else:
            std_val = 0

        for i in range(1, len(values)):
            cur = values[i]
            prev = values[i - 1]

            if cur is None or prev is None:
                continue

            # YoY 변동
            if prev != 0:
                change = (cur - prev) / abs(prev) * 100
                if abs(change) > threshold_pct:
                    severity = "high" if abs(change) > 100 else "medium"
                    anomalies.append(
                        Anomaly(
                            column=col,
                            year=str(years[i]),
                            value=cur,
                            prev_value=prev,
                            change_pct=round(change, 1),
                            anomaly_type="spike",
                            severity=severity,
                        )
                    )

            # 부호 반전
            if (prev > 0 and cur < 0) or (prev < 0 and cur > 0):
                anomalies.append(
                    Anomaly(
                        column=col,
                        year=str(years[i]),
                        value=cur,
                        prev_value=prev,
                        change_pct=None,
                        anomaly_type="sign_reversal",
                        severity="high",
                    )
                )

            # 2σ 이탈
            if std_val > 0 and abs(cur - mean_val) > 2 * std_val:
                anomalies.append(
                    Anomaly(
                        column=col,
                        year=str(years[i]),
                        value=cur,
                        prev_value=None,
                        change_pct=None,
                        anomaly_type="outlier",
                        severity="medium",
                    )
                )

    # 중복 제거 (같은 year+column)
    seen = set()
    unique = []
    for a in anomalies:
        key = (a.column, a.year, a.anomaly_type)
        if key not in seen:
            seen.add(key)
            unique.append(a)

    return unique


def detect_anomalies(
    df: pl.DataFrame,
    *,
    module_name: str | None = None,
    year_col: str = "year",
    threshold_pct: float = 50.0,
    use_llm: bool = True,
) -> list[Anomaly]:
    """2단계 이상치 탐지.

    Stage 1: 통계 사전스크리닝 (LLM 없이 항상 동작)
    Stage 2: LLM 해석 (use_llm=True이고 LLM 설정 시)

    Args:
            df: 시계열 DataFrame
            module_name: 모듈명 (메타데이터 활용)
            threshold_pct: YoY 변동 임계값 (%)
            use_llm: True면 LLM으로 해석 추가

    Returns:
            Anomaly 리스트 (severity 내림차순)
    """
    anomalies = _statistical_prescreen(df, year_col=year_col, threshold_pct=threshold_pct)

    if not anomalies:
        return []

    # Stage 2: LLM 해석
    if use_llm and anomalies:
        try:
            meta_ctx = ""
            if module_name:
                meta = get_meta(module_name)
                if meta:
                    meta_ctx = f"데이터: {meta.label} ({meta.description})\n"

            lines = []
            for a in anomalies[:10]:  # 최대 10개만
                if a.anomaly_type == "spike":
                    lines.append(
                        f"- {a.column} {a.year}년: {a.prev_value:,.0f} → {a.value:,.0f} (YoY {a.change_pct:+.1f}%)"
                    )
                elif a.anomaly_type == "sign_reversal":
                    lines.append(f"- {a.column} {a.year}년: 부호 반전 {a.prev_value:,.0f} → {a.value:,.0f}")
                elif a.anomaly_type == "outlier":
                    lines.append(f"- {a.column} {a.year}년: 이상치 {a.value:,.0f}")

            prompt = (
                f"{meta_ctx}"
                f"다음 재무 데이터 이상치들에 대해 각각 한 줄로 가능한 원인을 설명하세요.\n\n" + "\n".join(lines)
            )

            answer = _llm_call(prompt, system="한국어로 간결하게 답변하세요.")

            # 응답에서 설명 추출하여 anomalies에 매핑
            desc_lines = [l.strip().lstrip("- ").lstrip("· ") for l in answer.strip().split("\n") if l.strip()]
            for i, a in enumerate(anomalies[:10]):
                if i < len(desc_lines):
                    a.description = desc_lines[i]

        except _AI_PARSER_ERRORS:
            # LLM 실패 시 통계 결과만 반환
            pass

    # severity 정렬
    severity_order = {"high": 0, "medium": 1, "low": 2}
    anomalies.sort(key=lambda a: severity_order.get(a.severity, 1))

    return anomalies


# ══════════════════════════════════════
# 텍스트 분류
# ══════════════════════════════════════


def classify_text(text: str) -> dict:
    """공시 텍스트에서 감성, 핵심토픽, 리스크, 기회 추출.

    MD&A, 사업의 내용 등 서술형 텍스트를 구조화된 분석 결과로 변환.

    Returns:
            {
                    "sentiment": "긍정" | "부정" | "중립",
                    "key_topics": list[str],
                    "risks": list[str],
                    "opportunities": list[str],
                    "summary": str,
            }
    """
    if not text:
        return {
            "sentiment": "중립",
            "key_topics": [],
            "risks": [],
            "opportunities": [],
            "summary": "",
        }

    # 텍스트 길이 제한
    truncated = text[:3000] if len(text) > 3000 else text

    prompt = (
        "다음 공시 텍스트를 분석하여 아래 형식으로 답변하세요.\n\n"
        "감성: (긍정/부정/중립)\n"
        "핵심토픽: (쉼표로 구분, 3~5개)\n"
        "리스크: (쉼표로 구분)\n"
        "기회: (쉼표로 구분)\n"
        "요약: (2~3문장)\n\n"
        f"텍스트:\n{truncated}"
    )

    answer = _llm_call(prompt, system="한국어로 답변하세요. 주어진 형식을 정확히 따르세요.")

    # 응답 파싱
    result = {
        "sentiment": "중립",
        "key_topics": [],
        "risks": [],
        "opportunities": [],
        "summary": "",
    }

    for line in answer.strip().split("\n"):
        line = line.strip()
        if line.startswith("감성:"):
            val = line.split(":", 1)[1].strip()
            if "긍정" in val:
                result["sentiment"] = "긍정"
            elif "부정" in val:
                result["sentiment"] = "부정"
            else:
                result["sentiment"] = "중립"
        elif line.startswith("핵심토픽:"):
            val = line.split(":", 1)[1].strip()
            result["key_topics"] = [t.strip() for t in val.split(",") if t.strip()]
        elif line.startswith("리스크:"):
            val = line.split(":", 1)[1].strip()
            result["risks"] = [t.strip() for t in val.split(",") if t.strip()]
        elif line.startswith("기회:"):
            val = line.split(":", 1)[1].strip()
            result["opportunities"] = [t.strip() for t in val.split(",") if t.strip()]
        elif line.startswith("요약:"):
            result["summary"] = line.split(":", 1)[1].strip()

    return result


# ══════════════════════════════════════
# 통합 분석
# ══════════════════════════════════════


def analyze_module(
    company: Any,
    module_name: str,
) -> dict:
    """단일 모듈 전체 AI 분석.

    summarize + detect_anomalies + (interpret_accounts if applicable) 일괄 실행.

    Returns:
            {
                    "summary": str,
                    "anomalies": list[Anomaly],
                    "interpreted_df": pl.DataFrame | None,
            }
    """
    data = getattr(company, module_name, None)
    if data is None:
        return {"summary": "데이터 없음", "anomalies": [], "interpreted_df": None}

    result: dict[str, Any] = {}

    # 요약
    result["summary"] = summarize(data, module_name=module_name)

    # 이상치 탐지 (DataFrame인 경우만)
    if isinstance(data, pl.DataFrame):
        result["anomalies"] = detect_anomalies(data, module_name=module_name)
    else:
        result["anomalies"] = []

    # 계정 해석 (BS/IS/CF만)
    if module_name in ("BS", "IS", "CF") and isinstance(data, pl.DataFrame) and "계정명" in data.columns:
        result["interpreted_df"] = interpret_accounts(data, module_name=module_name)
    else:
        result["interpreted_df"] = None

    return result
