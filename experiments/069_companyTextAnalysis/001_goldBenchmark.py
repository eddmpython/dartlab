"""
실험 ID: 069-001
실험명: Company 텍스트 분석 benchmark 구축

목적:
- Company에 실제로 도움이 되는 텍스트 분석을 검증할 수 있는 benchmark를 만든다.
- 검색/변화탐지/추출/요약을 한 번에 비교할 수 있는 고정 케이스 40개를 정의한다.
- 현재 `contextSlices`와 `retrievalBlocks`를 결합해 slice id가 안정적인 실험용 corpus를 만든다.

가설:
1. Company 흡수 후보 토픽 10개만 좁혀도 유의미한 benchmark corpus가 된다.
2. 최근 12개 기간 + placeholder 제거만으로도 검색/추출/요약 평가에 충분한 텍스트 풀을 만들 수 있다.
3. retrieval, change, extraction, summary를 섞은 40개 benchmark면 후속 실험의 기준점으로 충분하다.

방법:
1. 6개 기준 종목의 `retrievalBlocks`를 직접 읽어 blockIdx가 포함된 enriched context slice를 만든다.
2. 토픽 10개 + 최근 12개 기간 + placeholder 제거 + chars 40 이상으로 benchmark corpus를 만든다.
3. retrieval 16, change 8, extraction 8, summary 8의 총 40개 benchmark case를 구성한다.
4. case별 gold slice id, requiredFacts, forbiddenFacts를 코드에 고정하고 통계를 출력한다.

결과 (실험 후 작성):

결론:

실험일: 2026-03-18
"""

from __future__ import annotations

import json
import math
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import requests
from sentence_transformers import CrossEncoder, SentenceTransformer

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dartlab.core.dataLoader import _dataDir  # noqa: E402
from dartlab.providers.dart.docs.sections.views import (  # noqa: E402
    retrievalBlocks,
    splitContextText,
    splitMarkdownTable,
)

EXPERIMENT_DATE = "2026-03-18"
EXPERIMENT_DIR = Path(__file__).resolve().parent
STATUS_PATH = EXPERIMENT_DIR / "STATUS.md"
OLLAMA_URL = "http://localhost:11434/api/generate"
LOCAL_SUMMARY_MODEL = "qwen3:latest"
TARGET_STOCK_CODES = ["005930", "000660", "035420", "035720", "373220", "068270"]
TARGET_TOPICS = [
    "companyOverview",
    "businessOverview",
    "salesOrder",
    "rawMaterial",
    "riskDerivative",
    "audit",
    "employee",
    "boardOfDirectors",
    "majorHolder",
    "dividend",
]
TASK_DISTRIBUTION = {"retrieval": 16, "change": 8, "extraction": 8, "summary": 8}
TOPIC_QUERY_HINTS = {
    "salesOrder": "매출 및 판매 현황",
    "rawMaterial": "원재료 조달과 생산설비",
    "audit": "감사인과 감사계약 또는 비감사용역",
    "majorHolder": "최대주주와 지분 관련 현황",
    "dividend": "배당정책과 배당 이력",
    "riskDerivative": "위험관리와 파생상품 또는 환율위험",
    "companyOverview": "회사 개요와 주요 종속회사",
    "businessOverview": "사업 개요와 제품 또는 서비스",
    "employee": "임원 및 직원 현황",
    "boardOfDirectors": "이사회와 주주총회 제도",
}
PLACEHOLDER_PATTERNS = [
    "기재하지 아니하였습니다",
    "기재하지 않습니다",
    "해당사항 없음",
    "해당 사항 없음",
    "참고하시기 바랍니다",
]
TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9][가-힣A-Za-z0-9·&()/.-]{1,}")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?。])\\s+|(?<=다\\.)\\s+")


@dataclass(frozen=True)
class BenchmarkCase:
    caseId: str
    taskType: str
    stockCode: str
    topic: str
    period: str | None
    question: str
    goldSliceIds: list[str]
    requiredFacts: list[str]
    forbiddenFacts: list[str]
    note: str = ""


@dataclass
class RetrievalResult:
    method: str
    hit1: float
    hit3: float
    hit5: float
    mrr10: float
    ndcg10: float
    goldRecall10: float
    medianLatencyMs: float
    p95LatencyMs: float
    indexBuildSec: float
    caseCount: int


@dataclass
class ExtractionResult:
    method: str
    precision: float
    recall: float
    f1: float
    avgLatencyMs: float
    caseCount: int
    labelF1: dict[str, float]
    notes: str = ""


@dataclass
class SummaryResult:
    method: str
    requiredCoverage: float
    missingRate: float
    forbiddenHitRate: float
    citationCoverage: float
    avgLatencyMs: float
    caseCount: int
    notes: str = ""


def _is_placeholder(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return True
    return any(p in stripped for p in PLACEHOLDER_PATTERNS)


def _tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text or "")]


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\u00a0", " ")).strip()


def _slice_id(record: dict[str, Any]) -> str:
    return f"{record['cellKey']}:{record['blockIdx']}:{record['sliceIdx']}"


def _last_n_periods(df: pl.DataFrame, n: int = 12) -> pl.DataFrame:
    periods = sorted(df["period"].unique().to_list())
    if len(periods) <= n:
        return df
    return df.filter(pl.col("period").is_in(periods[-n:]))


def _safe_terms(text: str, *, max_terms: int = 3) -> list[str]:
    candidates = []
    seen: set[str] = set()
    for token in _tokenize(text):
        if len(token) < 3 or token in seen:
            continue
        seen.add(token)
        candidates.append(token)
        if len(candidates) >= max_terms:
            break
    return candidates


def _first_sentences(text: str, *, max_sentences: int = 2) -> list[str]:
    sentences = [_normalize_text(s) for s in SENTENCE_SPLIT_RE.split(text) if _normalize_text(s)]
    return sentences[:max_sentences]


def build_enriched_context_slices(stock_code: str, *, max_chars: int = 1800) -> pl.DataFrame:
    blocks = retrievalBlocks(stock_code)
    rows: list[dict[str, Any]] = []
    for record in blocks.to_dicts():
        is_semantic = record.get("semanticTopic") is not None or record.get("detailTopic") is not None
        if record.get("isBoilerplate") or (record.get("isPlaceholder") and not is_semantic):
            continue
        block_text = str(record.get("blockText") or "")
        if record.get("blockType") == "table":
            parts = splitMarkdownTable(block_text, max_chars)
        else:
            parts = splitContextText(block_text, max_chars)
        for idx, part in enumerate(parts):
            if not part.strip():
                continue
            rows.append(
                {
                    "stockCode": stock_code,
                    "period": str(record["period"]),
                    "periodOrder": int(record["periodOrder"]),
                    "topic": str(record["topic"]),
                    "sourceTopic": record.get("sourceTopic"),
                    "cellKey": str(record["cellKey"]),
                    "blockIdx": int(record["blockIdx"]),
                    "semanticTopic": record.get("semanticTopic"),
                    "detailTopic": record.get("detailTopic"),
                    "blockType": str(record["blockType"]),
                    "blockLabel": str(record.get("blockLabel") or ""),
                    "sliceIdx": idx,
                    "sliceText": part,
                    "chars": len(part),
                    "isSemantic": bool(is_semantic),
                    "isTable": bool(record.get("blockType") == "table"),
                    "isBoilerplate": bool(record.get("isBoilerplate")),
                    "isPlaceholder": bool(record.get("isPlaceholder")),
                    "blockPriority": int(record.get("blockPriority") or 0),
                    "sliceId": f"{record['cellKey']}:{record['blockIdx']}:{idx}",
                }
            )
    return pl.DataFrame(rows, strict=False, infer_schema_length=None)


def load_benchmark_corpus() -> pl.DataFrame:
    return build_corpus_for_codes(TARGET_STOCK_CODES, last_n=12)


def all_available_doc_codes() -> list[str]:
    docs_dir = _dataDir("docs")
    return sorted(path.stem for path in docs_dir.glob("*.parquet"))


def build_corpus_for_codes(codes: list[str], *, last_n: int | None = None) -> pl.DataFrame:
    frames = [build_enriched_context_slices(code) for code in codes]
    corpus = pl.concat(frames, how="vertical")
    corpus = corpus.filter(
        pl.col("topic").is_in(TARGET_TOPICS),
        ~pl.col("isPlaceholder"),
        ~pl.col("isBoilerplate"),
        pl.col("chars") >= 40,
    )
    grouped: list[pl.DataFrame] = []
    for code in codes:
        code_df = corpus.filter(pl.col("stockCode") == code)
        grouped.append(_last_n_periods(code_df, last_n) if last_n is not None else code_df)
    return pl.concat(grouped, how="vertical").sort(
        ["stockCode", "periodOrder", "blockPriority", "chars"],
        descending=[False, True, True, True],
    )


def _pick_case_rows(
    corpus: pl.DataFrame,
    *,
    topic: str,
    count: int,
    prefer_table: bool | None = None,
    min_chars: int = 80,
    keyword: str | None = None,
    unique_stock: bool = True,
) -> list[dict[str, Any]]:
    subset = corpus.filter(pl.col("topic") == topic, pl.col("chars") >= min_chars)
    if prefer_table is True:
        subset = subset.filter(pl.col("isTable"))
    elif prefer_table is False:
        subset = subset.filter(~pl.col("isTable"))
    if keyword:
        subset = subset.filter(pl.col("sliceText").str.contains(keyword, literal=False))
    rows = subset.to_dicts()
    picked: list[dict[str, Any]] = []
    seen_stocks: set[str] = set()
    seen_cells: set[str] = set()
    for row in rows:
        if _is_placeholder(str(row["sliceText"])):
            continue
        if unique_stock and row["stockCode"] in seen_stocks:
            continue
        cell_key = f"{row['cellKey']}:{row['blockIdx']}"
        if cell_key in seen_cells:
            continue
        picked.append(row)
        seen_stocks.add(row["stockCode"])
        seen_cells.add(cell_key)
        if len(picked) >= count:
            break
    return picked


def _change_pairs(corpus: pl.DataFrame, topic: str, count: int) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for code in TARGET_STOCK_CODES:
        subset = corpus.filter(pl.col("stockCode") == code, pl.col("topic") == topic, pl.col("chars") >= 80)
        if subset.is_empty():
            continue
        rows = subset.to_dicts()
        latest = rows[0]
        previous = None
        for row in rows[1:]:
            if row["period"] != latest["period"]:
                previous = row
                break
        if previous is None:
            continue
        if _normalize_text(latest["sliceText"]) == _normalize_text(previous["sliceText"]):
            continue
        pairs.append((latest, previous))
        if len(pairs) >= count:
            break
    return pairs


MANUAL_EXTRACTION_SPECS: list[dict[str, Any]] = [
    {
        "stockCode": "000660",
        "topic": "businessOverview",
        "contains": "경기도 이천시에 위치한 본사",
        "question": "SK하이닉스의 사업 개요에서 지역 정보를 추출하라.",
        "expected": [
            {"text": "경기도 이천시", "label": "region"},
            {"text": "미국", "label": "region"},
            {"text": "중국", "label": "region"},
            {"text": "싱가포르", "label": "region"},
        ],
    },
    {
        "stockCode": "000660",
        "topic": "businessOverview",
        "contains": "DRAM 및 NAND",
        "question": "SK하이닉스 사업 개요에서 핵심 제품을 추출하라.",
        "expected": [
            {"text": "DRAM", "label": "product"},
            {"text": "NAND", "label": "product"},
        ],
    },
    {
        "stockCode": "035420",
        "topic": "salesOrder",
        "contains": "검색, 광고, 커머스, 클라우드",
        "question": "네이버 판매전략 설명에서 서비스/제품명을 추출하라.",
        "expected": [
            {"text": "검색", "label": "product"},
            {"text": "광고", "label": "product"},
            {"text": "커머스", "label": "product"},
            {"text": "클라우드", "label": "product"},
        ],
    },
    {
        "stockCode": "373220",
        "topic": "salesOrder",
        "contains": "리튬전지 시장",
        "question": "LG에너지솔루션 판매전략에서 핵심 제품을 추출하라.",
        "expected": [{"text": "리튬전지", "label": "product"}],
    },
    {
        "stockCode": "068270",
        "topic": "salesOrder",
        "contains": "주식회사 셀트리온헬스케어",
        "question": "셀트리온 판매경로 설명에서 거래상대방/회사명을 추출하라.",
        "expected": [{"text": "주식회사 셀트리온헬스케어", "label": "counterparty"}],
    },
    {
        "stockCode": "005930",
        "topic": "riskDerivative",
        "contains": "레인보우로보틱스㈜",
        "question": "삼성전자 위험관리 설명에서 거래상대방/회사명을 추출하라.",
        "expected": [{"text": "레인보우로보틱스㈜", "label": "counterparty"}],
    },
    {
        "stockCode": "005930",
        "topic": "majorHolder",
        "contains": "삼성생명보험㈜",
        "question": "삼성전자 최대주주 설명에서 관련 회사를 추출하라.",
        "expected": [
            {"text": "삼성생명보험㈜", "label": "company"},
            {"text": "삼성카드㈜", "label": "company"},
        ],
    },
    {
        "stockCode": "000660",
        "topic": "majorHolder",
        "contains": "대표이사(대표조합원)",
        "question": "SK하이닉스 최대주주 정보 표에서 지배구조 역할명을 추출하라.",
        "expected": [
            {"text": "대표이사", "label": "governanceRole"},
            {"text": "업무집행자", "label": "governanceRole"},
            {"text": "최대주주", "label": "governanceRole"},
        ],
    },
]

MANUAL_SUMMARY_SPECS: list[dict[str, Any]] = [
    {
        "stockCode": "005930",
        "topic": "dividend",
        "contains": "2021~2023년의 주주환원 정책",
        "question": "삼성전자의 배당정책 핵심을 근거와 함께 요약하라.",
        "requiredFacts": ["2021~2023년", "잉여현금흐름", "정규 배당"],
        "forbiddenFacts": ["무배당", "배당 중단"],
    },
    {
        "stockCode": "000660",
        "topic": "dividend",
        "contains": "2025년부터 2027년까지 적용될 신규 주주환원정책",
        "question": "SK하이닉스의 신규 주주환원정책 핵심을 요약하라.",
        "requiredFacts": ["2025~2027년", "주주환원정책", "재무 건전성 강화"],
        "forbiddenFacts": ["2021~2023년", "무배당"],
    },
    {
        "stockCode": "373220",
        "topic": "dividend",
        "contains": "대규모 투자 집행",
        "question": "LG에너지솔루션의 배당정책 배경을 요약하라.",
        "requiredFacts": ["대규모 투자", "당분간", "배당정책"],
        "forbiddenFacts": ["연속 배당", "즉시 배당 확대"],
    },
    {
        "stockCode": "068270",
        "topic": "dividend",
        "contains": "2012년 12월 31일부터 2024년 12월 31일",
        "question": "셀트리온의 배당 이력 핵심을 요약하라.",
        "requiredFacts": ["2012년", "2024년 12월 31일", "과거 배당 이력"],
        "forbiddenFacts": ["무배당", "배당 미지급"],
    },
    {
        "stockCode": "000660",
        "topic": "rawMaterial",
        "contains": "300mm 웨이퍼",
        "question": "SK하이닉스의 원재료 조달 구조를 요약하라.",
        "requiredFacts": ["300mm 웨이퍼", "일본", "미국"],
        "forbiddenFacts": ["단일 국내 공급처", "원재료 자체 생산"],
    },
    {
        "stockCode": "035420",
        "topic": "businessOverview",
        "contains": "네이버쇼핑",
        "question": "네이버 사업 개요에서 커머스 축의 핵심을 요약하라.",
        "requiredFacts": ["네이버쇼핑", "이커머스", "검색형 쇼핑 서비스"],
        "forbiddenFacts": ["오프라인 유통 중심", "제조업 주력"],
    },
    {
        "stockCode": "373220",
        "topic": "riskDerivative",
        "contains": "시장위험, 신용위험 및 유동성위험",
        "question": "LG에너지솔루션의 위험관리 요지를 요약하라.",
        "requiredFacts": ["시장위험", "신용위험", "유동성위험"],
        "forbiddenFacts": ["위험 없음", "파생상품 미사용"],
    },
    {
        "stockCode": "068270",
        "topic": "businessOverview",
        "contains": "제약 산업은 인간의 생명과 보건",
        "question": "셀트리온 사업 개요의 산업 특성을 요약하라.",
        "requiredFacts": ["제약 산업", "임상시험", "인ㆍ허가"],
        "forbiddenFacts": ["전자상거래", "반도체 제조"],
    },
]


def _find_manual_row(corpus: pl.DataFrame, spec: dict[str, Any]) -> dict[str, Any]:
    rows = corpus.filter(
        pl.col("stockCode") == spec["stockCode"],
        pl.col("topic") == spec["topic"],
        pl.col("sliceText").str.contains(spec["contains"], literal=True),
    ).sort(["periodOrder", "chars"], descending=[True, True]).to_dicts()
    if not rows:
        raise ValueError(f"manual spec not found: {spec['stockCode']} {spec['topic']} {spec['contains']}")
    return rows[0]


def build_benchmark_cases(corpus: pl.DataFrame) -> list[BenchmarkCase]:
    cases: list[BenchmarkCase] = []

    retrieval_plan = [
        ("salesOrder", False),
        ("rawMaterial", False),
        ("audit", True),
        ("majorHolder", None),
    ]
    case_no = 1
    for topic, prefer_table in retrieval_plan:
        rows = _pick_case_rows(corpus, topic=topic, count=4, prefer_table=prefer_table, min_chars=100)
        for idx, row in enumerate(rows, 1):
            question = (
                f"{row['stockCode']}의 {TOPIC_QUERY_HINTS[topic]} 관련 최신 근거를 찾아라. "
                f"질문 힌트: {_safe_terms(str(row['sliceText']), max_terms=2)}"
            )
            cases.append(
                BenchmarkCase(
                    caseId=f"R{case_no:02d}",
                    taskType="retrieval",
                    stockCode=str(row["stockCode"]),
                    topic=topic,
                    period=str(row["period"]),
                    question=question,
                    goldSliceIds=[_slice_id(row)],
                    requiredFacts=[],
                    forbiddenFacts=[],
                    note=f"{topic}-{idx}",
                )
            )
            case_no += 1

    change_case_no = 1
    for topic in ["dividend", "riskDerivative"]:
        for latest, previous in _change_pairs(corpus, topic, 4):
            question = (
                f"{latest['stockCode']}의 {TOPIC_QUERY_HINTS[topic]}에서 "
                f"{previous['period']} 대비 {latest['period']} 변화 근거를 찾아라."
            )
            required = _safe_terms(str(latest["sliceText"]), max_terms=2) + _safe_terms(str(previous["sliceText"]), max_terms=1)
            cases.append(
                BenchmarkCase(
                    caseId=f"C{change_case_no:02d}",
                    taskType="change",
                    stockCode=str(latest["stockCode"]),
                    topic=topic,
                    period=f"{previous['period']}->{latest['period']}",
                    question=question,
                    goldSliceIds=[_slice_id(latest), _slice_id(previous)],
                    requiredFacts=required[:3],
                    forbiddenFacts=[],
                    note=f"{previous['period']}->{latest['period']}",
                )
            )
            change_case_no += 1

    for idx, spec in enumerate(MANUAL_EXTRACTION_SPECS, 1):
        row = _find_manual_row(corpus, spec)
        cases.append(
            BenchmarkCase(
                caseId=f"E{idx:02d}",
                taskType="extraction",
                stockCode=spec["stockCode"],
                topic=spec["topic"],
                period=str(row["period"]),
                question=spec["question"],
                goldSliceIds=[_slice_id(row)],
                requiredFacts=[item["text"] for item in spec["expected"]],
                forbiddenFacts=[],
                note=json.dumps(spec["expected"], ensure_ascii=False),
            )
        )

    for idx, spec in enumerate(MANUAL_SUMMARY_SPECS, 1):
        row = _find_manual_row(corpus, spec)
        cases.append(
            BenchmarkCase(
                caseId=f"S{idx:02d}",
                taskType="summary",
                stockCode=spec["stockCode"],
                topic=spec["topic"],
                period=str(row["period"]),
                question=spec["question"],
                goldSliceIds=[_slice_id(row)],
                requiredFacts=list(spec["requiredFacts"]),
                forbiddenFacts=list(spec["forbiddenFacts"]),
                note=spec["contains"],
            )
        )

    counts = Counter(case.taskType for case in cases)
    assert counts == TASK_DISTRIBUTION, counts
    assert len(cases) == 40, len(cases)
    return cases


class SimpleBM25:
    def __init__(self, docs: list[str]):
        self.doc_tokens = [_tokenize(doc) for doc in docs]
        self.doc_freq: Counter[str] = Counter()
        for tokens in self.doc_tokens:
            self.doc_freq.update(set(tokens))
        self.doc_len = [len(tokens) for tokens in self.doc_tokens]
        self.avgdl = (sum(self.doc_len) / len(self.doc_len)) if self.doc_len else 0
        self.k1 = 1.5
        self.b = 0.75
        self.N = len(self.doc_tokens)

    def score(self, query: str) -> np.ndarray:
        q_tokens = _tokenize(query)
        scores = np.zeros(self.N, dtype=np.float32)
        if not q_tokens:
            return scores
        q_counter = Counter(q_tokens)
        for idx, tokens in enumerate(self.doc_tokens):
            tf = Counter(tokens)
            dl = self.doc_len[idx]
            for token, qf in q_counter.items():
                df = self.doc_freq.get(token, 0)
                if df == 0:
                    continue
                idf = math.log(1 + (self.N - df + 0.5) / (df + 0.5))
                freq = tf.get(token, 0)
                denom = freq + self.k1 * (1 - self.b + self.b * dl / max(self.avgdl, 1))
                if denom == 0:
                    continue
                scores[idx] += idf * freq * (self.k1 + 1) / denom * qf
        return scores


def contextual_text(row: dict[str, Any]) -> str:
    meta = [
        row["stockCode"],
        row["period"],
        row["topic"],
        row.get("semanticTopic") or "",
        row.get("detailTopic") or "",
        row["blockType"],
        row["blockLabel"],
    ]
    return " | ".join(str(m) for m in meta if m) + "\n" + str(row["sliceText"])


def _query_for_e5(query: str) -> str:
    return f"Instruct: 한국 기업 공시 질문과 관련된 근거 문서를 찾으세요.\nQuery: {query}"


def build_retrieval_corpora(corpus: pl.DataFrame) -> dict[str, list[str]]:
    rows = corpus.to_dicts()
    return {
        "raw": [str(row["sliceText"]) for row in rows],
        "contextual": [contextual_text(row) for row in rows],
    }


def _rrf(rank_lists: list[list[int]], k: int = 60) -> list[int]:
    scores: dict[int, float] = defaultdict(float)
    for rank_list in rank_lists:
        for rank, doc_idx in enumerate(rank_list, 1):
            scores[doc_idx] += 1.0 / (k + rank)
    return [doc for doc, _score in sorted(scores.items(), key=lambda item: item[1], reverse=True)]


def _binary_ndcg(relevant: set[str], ranked_ids: list[str], k: int = 10) -> float:
    dcg = 0.0
    for idx, slice_id in enumerate(ranked_ids[:k], 1):
        if slice_id in relevant:
            dcg += 1.0 / math.log2(idx + 1)
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(relevant), k) + 1))
    return (dcg / ideal) if ideal else 0.0


def evaluate_ranked_lists(
    cases: list[BenchmarkCase],
    ranked_lists: dict[str, list[str]],
    latencies_ms: list[float],
    index_sec: float,
) -> RetrievalResult:
    hits = {1: 0, 3: 0, 5: 0}
    mrr_total = 0.0
    ndcg_total = 0.0
    gold_recall_total = 0.0
    for case in cases:
        ranked = ranked_lists[case.caseId]
        relevant = set(case.goldSliceIds)
        for k in hits:
            if any(slice_id in relevant for slice_id in ranked[:k]):
                hits[k] += 1
        reciprocal = 0.0
        for idx, slice_id in enumerate(ranked[:10], 1):
            if slice_id in relevant:
                reciprocal = 1.0 / idx
                break
        mrr_total += reciprocal
        ndcg_total += _binary_ndcg(relevant, ranked, 10)
        found = sum(1 for slice_id in ranked[:10] if slice_id in relevant)
        gold_recall_total += found / max(len(relevant), 1)
    return RetrievalResult(
        method="",
        hit1=hits[1] / len(cases),
        hit3=hits[3] / len(cases),
        hit5=hits[5] / len(cases),
        mrr10=mrr_total / len(cases),
        ndcg10=ndcg_total / len(cases),
        goldRecall10=gold_recall_total / len(cases),
        medianLatencyMs=statistics.median(latencies_ms) if latencies_ms else 0.0,
        p95LatencyMs=float(np.percentile(latencies_ms, 95)) if latencies_ms else 0.0,
        indexBuildSec=index_sec,
        caseCount=len(cases),
    )


def load_dense_model(name: str) -> SentenceTransformer:
    if name == "e5":
        return SentenceTransformer("intfloat/multilingual-e5-large-instruct")
    if name == "bge":
        return SentenceTransformer("BAAI/bge-m3", trust_remote_code=True)
    raise ValueError(name)


def load_reranker() -> CrossEncoder:
    return CrossEncoder("BAAI/bge-reranker-v2-m3", trust_remote_code=True)


def dense_rank(
    model: SentenceTransformer,
    *,
    corpus_texts: list[str],
    queries: list[str],
    model_name: str,
) -> tuple[np.ndarray, float]:
    start = time.perf_counter()
    query_texts = [_query_for_e5(q) for q in queries] if model_name == "e5" else queries
    doc_emb = model.encode(corpus_texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
    query_emb = model.encode(query_texts, batch_size=16, normalize_embeddings=True, show_progress_bar=False)
    return np.matmul(query_emb, doc_emb.T), (time.perf_counter() - start)


def run_retrieval_methods(corpus: pl.DataFrame, cases: list[BenchmarkCase]) -> dict[str, RetrievalResult]:
    rows = corpus.to_dicts()
    slice_ids = [str(row["sliceId"]) for row in rows]
    corpora = build_retrieval_corpora(corpus)
    queries = [case.question for case in cases]
    results: dict[str, RetrievalResult] = {}

    for name, texts in [("B1_raw_bm25", corpora["raw"]), ("B2_contextual_bm25", corpora["contextual"])]:
        start = time.perf_counter()
        bm25 = SimpleBM25(texts)
        build_sec = time.perf_counter() - start
        ranked_lists: dict[str, list[str]] = {}
        latencies: list[float] = []
        for case in cases:
            t0 = time.perf_counter()
            scores = bm25.score(case.question)
            order = np.argsort(scores)[::-1][:10]
            latencies.append((time.perf_counter() - t0) * 1000)
            ranked_lists[case.caseId] = [slice_ids[i] for i in order]
        metric = evaluate_ranked_lists(cases, ranked_lists, latencies, build_sec)
        metric.method = name
        results[name] = metric

    dense_models = {
        "D1_e5_dense": ("e5", corpora["contextual"]),
        "D2_bge_dense": ("bge", corpora["contextual"]),
    }
    dense_scores: dict[str, np.ndarray] = {}
    dense_build_sec: dict[str, float] = {}
    for out_name, (model_key, texts) in dense_models.items():
        model = load_dense_model(model_key)
        scores, build_sec = dense_rank(model, corpus_texts=texts, queries=queries, model_name=model_key)
        dense_scores[out_name] = scores
        dense_build_sec[out_name] = build_sec
        ranked_lists = {}
        latencies = []
        for idx, case in enumerate(cases):
            t0 = time.perf_counter()
            order = np.argsort(scores[idx])[::-1][:10]
            latencies.append((time.perf_counter() - t0) * 1000)
            ranked_lists[case.caseId] = [slice_ids[i] for i in order]
        metric = evaluate_ranked_lists(cases, ranked_lists, latencies, build_sec)
        metric.method = out_name
        results[out_name] = metric

    hybrids = [
        ("H1_raw_plus_e5", "B1_raw_bm25", "D1_e5_dense"),
        ("H2_contextual_plus_bge", "B2_contextual_bm25", "D2_bge_dense"),
    ]
    for out_name, sparse_name, dense_name in hybrids:
        ranked_lists = {}
        latencies = []
        sparse_texts = corpora["raw"] if "raw" in sparse_name else corpora["contextual"]
        bm25 = SimpleBM25(sparse_texts)
        for idx, case in enumerate(cases):
            t0 = time.perf_counter()
            sparse_order = np.argsort(bm25.score(case.question))[::-1][:50].tolist()
            dense_order = np.argsort(dense_scores[dense_name][idx])[::-1][:50].tolist()
            fused = _rrf([sparse_order, dense_order])[:10]
            latencies.append((time.perf_counter() - t0) * 1000)
            ranked_lists[case.caseId] = [slice_ids[i] for i in fused]
        metric = evaluate_ranked_lists(cases, ranked_lists, latencies, dense_build_sec[dense_name])
        metric.method = out_name
        results[out_name] = metric

    reranker = load_reranker()
    bm25 = SimpleBM25(corpora["contextual"])
    ranked_lists = {}
    latencies = []
    for idx, case in enumerate(cases):
        t0 = time.perf_counter()
        sparse_order = np.argsort(bm25.score(case.question))[::-1][:30].tolist()
        dense_order = np.argsort(dense_scores["D2_bge_dense"][idx])[::-1][:30].tolist()
        fused = _rrf([sparse_order, dense_order])[:20]
        pairs = [(case.question, corpora["contextual"][i]) for i in fused]
        scores = reranker.predict(pairs)
        reranked = [doc_idx for doc_idx, _score in sorted(zip(fused, scores), key=lambda item: float(item[1]), reverse=True)][:10]
        latencies.append((time.perf_counter() - t0) * 1000)
        ranked_lists[case.caseId] = [slice_ids[i] for i in reranked]
    metric = evaluate_ranked_lists(cases, ranked_lists, latencies, dense_build_sec["D2_bge_dense"])
    metric.method = "R1_h2_plus_reranker"
    results[metric.method] = metric
    return results


def _paragraph_split(text: str, max_chars: int = 1800) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paras:
        paras = [t.strip() for t in text.split("\n") if t.strip()]
    parts: list[str] = []
    buf: list[str] = []
    total = 0
    for para in paras:
        extra = len(para) + (2 if buf else 0)
        if buf and total + extra > max_chars:
            parts.append("\n\n".join(buf))
            buf = [para]
            total = len(para)
        else:
            buf.append(para)
            total += extra
    if buf:
        parts.append("\n\n".join(buf))
    return parts if parts else [text]


def build_long_text_corpus(strategy: str) -> pl.DataFrame:
    corpus = load_benchmark_corpus()
    rows: list[dict[str, Any]] = []
    for record in corpus.to_dicts():
        text = str(record["sliceText"])
        parts = [text] if (record["isTable"] or strategy == "current") else _paragraph_split(text)
        for idx, part in enumerate(parts):
            row = dict(record)
            row["sliceIdx"] = idx
            row["sliceText"] = part
            row["chars"] = len(part)
            row["sliceId"] = f"{record['cellKey']}:{record['blockIdx']}:{idx}:{strategy}"
            row["embedText"] = (
                contextual_text(record) + "\n\n[focus]\n" + part
                if strategy == "late" and not record["isTable"]
                else contextual_text({**record, "sliceText": part})
            )
            rows.append(row)
    return pl.DataFrame(rows, strict=False, infer_schema_length=None)


def run_late_chunking_bench(cases: list[BenchmarkCase]) -> dict[str, RetrievalResult]:
    long_cases = [case for case in cases if case.taskType in {"retrieval", "change", "summary"}]
    results: dict[str, RetrievalResult] = {}
    for strategy in ["current", "paragraph", "late"]:
        corpus = build_long_text_corpus(strategy)
        slice_ids = corpus["sliceId"].to_list()
        texts = corpus["embedText"].to_list()
        model = load_dense_model("bge")
        scores, build_sec = dense_rank(model, corpus_texts=texts, queries=[case.question for case in long_cases], model_name="bge")
        ranked_lists = {}
        latencies = []
        for idx, case in enumerate(long_cases):
            t0 = time.perf_counter()
            order = np.argsort(scores[idx])[::-1][:10]
            latencies.append((time.perf_counter() - t0) * 1000)
            ranked_lists[case.caseId] = [slice_ids[i] for i in order]
        metric = evaluate_ranked_lists(long_cases, ranked_lists, latencies, build_sec)
        metric.method = strategy
        results[strategy] = metric
    return results


def _extract_regex_baseline(text: str, expected_labels: list[dict[str, str]]) -> list[dict[str, str]]:
    return [item for item in expected_labels if item["text"] in text]


def _extract_gliner(text: str, expected_labels: list[dict[str, str]]) -> list[dict[str, str]]:
    try:
        from gliner import GLiNER
    except ImportError:
        return []
    label_map = {
        "company": "회사명",
        "product": "제품",
        "region": "지역",
        "counterparty": "거래상대방",
        "riskEvent": "위험사건",
        "governanceRole": "지배구조 역할",
    }
    labels = sorted({label_map[item["label"]] for item in expected_labels})
    model = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
    preds = model.predict_entities(text, labels, threshold=0.2)
    rev_map = {v: k for k, v in label_map.items()}
    return [{"text": pred.get("text", ""), "label": rev_map[pred.get("label")]} for pred in preds if pred.get("label") in rev_map]


def _extract_llm_local(text: str, expected_labels: list[dict[str, str]]) -> list[dict[str, str]]:
    prompt = (
        "한국어 공시 문장에서 엔티티를 추출하라.\n"
        f"라벨 집합: {sorted({item['label'] for item in expected_labels})}\n"
        "반드시 JSON 배열만 반환하고 각 원소는 {\"text\":...,\"label\":...} 형식으로 작성하라.\n"
        f"문장:\n{text[:3000]}"
    )
    payload = {"model": LOCAL_SUMMARY_MODEL, "prompt": prompt, "stream": False}
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        raw = resp.json()["response"].strip()
        start = raw.find("[")
        end = raw.rfind("]")
        if start >= 0 and end > start:
            return json.loads(raw[start : end + 1])
    except (requests.RequestException, KeyError, json.JSONDecodeError, ValueError):
        return []
    return []


def _prf(preds: list[dict[str, str]], gold: list[dict[str, str]]) -> tuple[float, float, float]:
    gold_set = {(item["text"], item["label"]) for item in gold}
    pred_set = {(item.get("text", ""), item.get("label", "")) for item in preds}
    tp = len(gold_set & pred_set)
    fp = len(pred_set - gold_set)
    fn = len(gold_set - pred_set)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


def run_extraction_bench(corpus: pl.DataFrame) -> dict[str, ExtractionResult]:
    methods = {"regex_baseline": _extract_regex_baseline, "gliner": _extract_gliner, "ollama_qwen3": _extract_llm_local}
    cases = [(_find_manual_row(corpus, spec), spec) for spec in MANUAL_EXTRACTION_SPECS]
    results: dict[str, ExtractionResult] = {}
    for method_name, fn in methods.items():
        precisions = []
        recalls = []
        f1s = []
        latencies = []
        per_label: dict[str, list[float]] = defaultdict(list)
        for row, spec in cases:
            t0 = time.perf_counter()
            preds = fn(str(row["sliceText"]), spec["expected"])
            latencies.append((time.perf_counter() - t0) * 1000)
            precision, recall, f1 = _prf(preds, spec["expected"])
            precisions.append(precision)
            recalls.append(recall)
            f1s.append(f1)
            for label in {item["label"] for item in spec["expected"]}:
                label_gold = [g for g in spec["expected"] if g["label"] == label]
                label_preds = [p for p in preds if p.get("label") == label]
                _p, _r, _f1 = _prf(label_preds, label_gold)
                per_label[label].append(_f1)
        results[method_name] = ExtractionResult(
            method=method_name,
            precision=float(np.mean(precisions)),
            recall=float(np.mean(recalls)),
            f1=float(np.mean(f1s)),
            avgLatencyMs=float(np.mean(latencies)),
            caseCount=len(cases),
            labelF1={label: float(np.mean(values)) for label, values in per_label.items()},
        )
    return results


def _summary_with_ollama(question: str, text: str) -> str:
    prompt = (
        "한국어 공시 문서 요약기다.\n"
        "질문에 맞게 2~4문장으로 간결히 요약하고, 각 문장 끝에 [S1] 태그를 붙여라.\n"
        f"질문: {question}\n근거:\n{text[:4000]}"
    )
    resp = requests.post(OLLAMA_URL, json={"model": LOCAL_SUMMARY_MODEL, "prompt": prompt, "stream": False}, timeout=180)
    resp.raise_for_status()
    return resp.json()["response"].strip()


def _hierarchical_summary(_question: str, text: str) -> str:
    sentences = _first_sentences(text, max_sentences=3)
    return "\n".join(f"- {s} [S1]" for s in sentences if s)


def _score_summary(case: BenchmarkCase, summary: str) -> tuple[float, float, float]:
    normalized = _normalize_text(summary)
    required_hits = sum(1 for fact in case.requiredFacts if fact in normalized)
    forbidden_hits = sum(1 for fact in case.forbiddenFacts if fact in normalized)
    coverage = required_hits / max(len(case.requiredFacts), 1)
    missing_rate = 1 - coverage
    forbidden_rate = forbidden_hits / max(len(case.forbiddenFacts), 1) if case.forbiddenFacts else 0.0
    return coverage, missing_rate, forbidden_rate


def run_summary_bench(corpus: pl.DataFrame, cases: list[BenchmarkCase]) -> dict[str, SummaryResult]:
    summary_cases = [case for case in cases if case.taskType == "summary"]
    methods = {
        "S0_raw_concat": lambda q, t: " ".join(_first_sentences(t, max_sentences=2)) + " [S1]",
        "S1_grounded_ollama": _summary_with_ollama,
        "S2_hierarchical_local": _hierarchical_summary,
    }
    results: dict[str, SummaryResult] = {}
    for method_name, fn in methods.items():
        coverages = []
        missings = []
        forbiddens = []
        citation_covs = []
        latencies = []
        for case in summary_cases:
            row = corpus.filter(pl.col("sliceId") == case.goldSliceIds[0]).to_dicts()[0]
            t0 = time.perf_counter()
            summary = fn(case.question, str(row["sliceText"]))
            latencies.append((time.perf_counter() - t0) * 1000)
            coverage, missing, forbidden = _score_summary(case, summary)
            coverages.append(coverage)
            missings.append(missing)
            forbiddens.append(forbidden)
            citation_covs.append(1.0 if "[S1]" in summary else 0.0)
        results[method_name] = SummaryResult(
            method=method_name,
            requiredCoverage=float(np.mean(coverages)),
            missingRate=float(np.mean(missings)),
            forbiddenHitRate=float(np.mean(forbiddens)),
            citationCoverage=float(np.mean(citation_covs)),
            avgLatencyMs=float(np.mean(latencies)),
            caseCount=len(summary_cases),
        )
    return results


def print_section(title: str) -> None:
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)


def benchmark_overview(corpus: pl.DataFrame, cases: list[BenchmarkCase]) -> dict[str, Any]:
    return {
        "stocks": TARGET_STOCK_CODES,
        "topics": TARGET_TOPICS,
        "corpusRows": corpus.height,
        "periods": corpus["period"].n_unique(),
        "taskCounts": dict(Counter(case.taskType for case in cases)),
        "topicCounts": dict(Counter(case.topic for case in cases)),
        "meanChars": round(float(corpus["chars"].mean()), 2),
        "medianChars": round(float(corpus["chars"].median()), 2),
    }


def write_status(summary: dict[str, Any]) -> None:
    STATUS_PATH.write_text(
        "\n".join(
            [
                "# 069 Company Text Analysis",
                "",
                f"- 실험일: {EXPERIMENT_DATE}",
                f"- benchmark rows: {summary['corpusRows']}",
                f"- periods: {summary['periods']}",
                f"- task counts: {summary['taskCounts']}",
                f"- topic counts: {summary['topicCounts']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    corpus = load_benchmark_corpus()
    cases = build_benchmark_cases(corpus)
    summary = benchmark_overview(corpus, cases)
    print_section("069-001 benchmark overview")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print_section("sample cases")
    for case in cases[:8]:
        print(asdict(case))
    write_status(summary)


if __name__ == "__main__":
    main()
