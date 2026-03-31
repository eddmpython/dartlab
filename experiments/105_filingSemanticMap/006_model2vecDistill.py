"""실험 105-006: Model2Vec 커스텀 증류 + 하이브리드 검색

실험 ID: 105-006
실험명: DART 공시 어휘로 ko-sroberta에서 Model2Vec 증류 → SemanticMap 보강

목적:
- ko-sroberta의 한국어 의미 이해를 경량 모델로 증류
- DART 공시 어휘에 특화된 8-30MB 모델 생성
- SemanticMap + Model2Vec 하이브리드로 precision 75%+ 달성

가설:
1. Model2Vec 증류 30초 이내 (CPU)
2. 증류 모델 cold start < 500ms
3. SemanticMap + Model2Vec 하이브리드 precision@5 ≥ 75%

방법:
1. DART 공시 텍스트에서 고빈도 어휘 추출
2. ko-sroberta → Model2Vec 증류 (DART 어휘 사용)
3. 증류 모델로 벡터 검색
4. SemanticMap + Model2Vec 하이브리드 벤치마크

결과:
- 어휘 추출: 19,680개 (DART 공시 텍스트에서)
- 증류 시간: 15.7초 (CPU), teacher 모델 로딩 포함
- 모델 크기: 24.7MB (ko-sroberta 420MB 대비 17배 축소)
- cold start: 265ms (ko-sroberta 12,700ms 대비 48배 빠름)
- 전체 임베딩: 2.9초 (9,033섹션)
- Model2Vec 단독 precision@5: 67%
- Hybrid(SM+M2V) precision@5: 60% (합산 시 오히려 하락)

결론:
- DART 특화 Model2Vec 증류 성공 — 24.7MB, 265ms cold start
- 하지만 precision 67%로 BM25(71%)보다 낮음
- 하이브리드 합산은 오히려 하락 — SM과 M2V의 결과 합산 전략이 부적절
- ko-sroberta(83%)와 15%p 차이는 모델 크기/품질 한계
- 증류 모델은 보조적 리랭킹에는 활용 가능하나 주력 검색으로는 부족

실험일: 2026-03-31
"""

from __future__ import annotations

import re
import time
from collections import Counter
from pathlib import Path

import numpy as np
import polars as pl
from numpy.linalg import norm


def loadData():
    df26 = pl.read_parquet("data/dart/allFilings/20260326.parquet")
    df27 = pl.read_parquet("data/dart/allFilings/20260327.parquet")
    return pl.concat([df26, df27]).filter(pl.col("section_content").is_not_null())


def extractVocabulary(df: pl.DataFrame, topK: int = 30000) -> list[str]:
    """DART 공시 텍스트에서 고빈도 어휘 추출."""
    counter: Counter = Counter()
    for text in df["section_content"].to_list():
        if text:
            # 한국어 + 영문 + 숫자 토큰
            tokens = re.findall(r"[가-힣]+|[a-zA-Z]+|[0-9]+", text[:2000])
            counter.update(tokens)

    # report_nm, section_title에서도 추출
    for col in ["report_nm", "section_title"]:
        for text in df[col].drop_nulls().to_list():
            tokens = re.findall(r"[가-힣]+|[a-zA-Z]+", text)
            counter.update(tokens)

    # 빈도순 상위
    vocab = [word for word, count in counter.most_common(topK) if len(word) >= 2]
    return vocab


def distillModel(vocab: list[str], savePath: str):
    """ko-sroberta → Model2Vec 증류."""
    from model2vec.distill import distill_from_model
    from transformers import AutoModel, AutoTokenizer

    print("  teacher 모델 로딩...")
    tokenizer = AutoTokenizer.from_pretrained("jhgan/ko-sroberta-multitask")
    teacher = AutoModel.from_pretrained("jhgan/ko-sroberta-multitask")

    t0 = time.time()
    model = distill_from_model(
        model=teacher,
        tokenizer=tokenizer,
        vocabulary=vocab,
        pca_dims=256,
    )
    elapsed = time.time() - t0
    model.save_pretrained(savePath)
    print(f"증류 완료: {elapsed:.1f}초, 저장: {savePath}")

    # 모델 크기
    totalSize = sum(f.stat().st_size for f in Path(savePath).rglob("*") if f.is_file())
    print(f"모델 크기: {totalSize / 1024 / 1024:.1f}MB")

    return model


def loadDistilled(savePath: str):
    """증류된 모델 로드 + cold start 측정."""
    from model2vec import StaticModel

    t0 = time.time()
    model = StaticModel.from_pretrained(savePath)
    elapsed = time.time() - t0
    print(f"모델 로딩: {elapsed*1000:.0f}ms")
    return model


def searchModel2Vec(model, df, allVecs, query, topK=5):
    """Model2Vec 벡터 검색."""
    qvec = model.encode(query)
    qn = qvec / (norm(qvec) + 1e-8)
    dn = allVecs / (norm(allVecs, axis=1, keepdims=True) + 1e-8)
    scores = dn @ qn
    indices = np.argsort(scores)[::-1][:topK]
    return indices, scores[indices]


# SemanticMap 검색 (005에서 가져옴)
SEMANTIC_MAP = {
    "유상증자": ["유상증자", "증자", "신주"],
    "전환사채": ["전환사채", "사채", "전환가액"],
    "차입": ["차입", "대출", "자금조달", "사채", "전환사채"],
    "대표이사": ["대표이사", "CEO", "대표"],
    "사외이사": ["사외이사", "중도퇴임", "선임", "해임"],
    "임원": ["임원", "이사", "감사", "사외이사", "대표이사"],
    "경영진": ["대표이사", "임원", "선임", "해임"],
    "배당": ["배당", "현금배당"],
    "주주총회": ["주주총회", "주총", "소집"],
    "대량보유": ["대량보유", "보유", "변동", "최대주주"],
    "합병": ["합병", "인수", "분할"],
    "소송": ["소송", "분쟁", "경영권", "가처분"],
    "감사": ["감사", "감사의견", "한정", "부적정"],
    "재무": ["재무", "재무제표", "주석"],
    "증권": ["증권", "발행", "투자설명서"],
}
NATURAL_LANGUAGE = {
    "돈을 빌렸다": ["차입", "사채", "대출", "전환사채"],
    "빌렸다": ["차입", "사채"],
    "경영진이 바뀌었다": ["대표이사", "임원", "선임", "해임"],
    "바뀌었다": ["변경", "선임", "해임"],
    "돈을 줬다": ["배당", "현금배당"],
    "문제": ["한정", "부적정", "감사"],
}


def expandQuery(query):
    keywords = set()
    for phrase, exp in NATURAL_LANGUAGE.items():
        if phrase in query:
            keywords.update(exp)
    for concept, exp in SEMANTIC_MAP.items():
        if concept in query:
            keywords.update(exp)
    for word in query.split():
        if len(word) >= 2:
            keywords.add(word)
    return list(keywords)


def searchSemantic(df, query, topK=5):
    keywords = expandQuery(query)
    if not keywords:
        return pl.DataFrame()
    conditions = []
    for kw in keywords:
        conditions.append(pl.col("report_nm").str.contains(kw, literal=True))
        conditions.append(pl.col("section_title").is_not_null() & pl.col("section_title").str.contains(kw, literal=True))
    combined = conditions[0]
    for c in conditions[1:]:
        combined = combined | c
    result = df.filter(combined)
    if result.height == 0:
        return pl.DataFrame()
    scores = []
    for row in result.iter_rows(named=True):
        score = 0
        rn = row.get("report_nm", "")
        st = row.get("section_title", "") or ""
        for kw in keywords:
            if kw in rn:
                score += 5
            if kw in st:
                score += 2
        scores.append(score)
    result = result.with_columns(pl.Series("score", scores))
    return result.sort("score", descending=True).unique(subset=["rcept_no"], keep="first").head(topK)


QUERIES = [
    ("유상증자 결정", ["유상증자"]),
    ("대표이사 변경", ["대표이사"]),
    ("정기주주총회 결과", ["주주총회", "정기주주총회"]),
    ("사외이사 선임", ["사외이사"]),
    ("대량보유 변동", ["대량보유", "보유주식"]),
    ("주식매수선택권 부여", ["주식매수선택권", "스톡옵션"]),
    ("자기주식 취득", ["자기주식", "자사주"]),
    ("소송 제기", ["소송"]),
    ("회사가 돈을 빌렸다", ["사채", "차입", "대여", "발행"]),
    ("경영진이 바뀌었다", ["대표이사", "임원", "이사"]),
    ("주주에게 배당을 줬다", ["배당", "주주총회"]),
    ("회사 주식을 대량 매수했다", ["대량보유", "취득"]),
    ("기업 가치를 높이겠다", ["기업가치", "제고"]),
    ("새로운 계약을 맺었다", ["계약", "공급", "판매"]),
    ("감사보고서에 문제가 있다", ["감사", "의견", "거절"]),
    ("재무 상태가 나빠졌다", ["재무", "부채", "미지급", "손실"]),
    ("회사 합병", ["합병", "인수"]),
    ("회사채 발행", ["사채", "회사채", "발행"]),
    ("임원 보수", ["보수", "임원", "급여"]),
    ("증권 발행", ["증권", "발행", "유상"]),
]


if __name__ == "__main__":
    df = loadData()
    texts = df["section_content"].str.slice(0, 2000).to_list()
    print(f"데이터: {df.height}행\n")

    modelPath = "experiments/105_filingSemanticMap/dart_model2vec"

    # 1. 어휘 추출 + 증류
    if not Path(modelPath).exists():
        print("=== 어휘 추출 ===")
        vocab = extractVocabulary(df, topK=20000)
        print(f"어휘: {len(vocab)}개 (상위: {vocab[:10]})")

        print("\n=== Model2Vec 증류 ===")
        model = distillModel(vocab, modelPath)
    else:
        print("=== 기존 모델 로드 ===")

    # 2. cold start 측정
    model = loadDistilled(modelPath)

    # 3. 전체 임베딩
    t0 = time.time()
    allVecs = model.encode(texts)
    print(f"전체 임베딩: {time.time()-t0:.1f}초, shape={allVecs.shape}")

    # 4. Model2Vec 단독 precision
    print("\n=== Model2Vec 단독 ===")
    totalHit = totalCheck = 0
    for query, expectedKws in QUERIES:
        indices, scores = searchModel2Vec(model, df, allVecs, query, topK=5)
        hits = 0
        for idx in indices:
            row = df.row(idx, named=True)
            combined = f"{row['report_nm']} {row.get('section_title', '')}".lower()
            if any(kw in combined for kw in expectedKws):
                hits += 1
        totalHit += hits
        totalCheck += len(indices)

    m2vP5 = totalHit / totalCheck if totalCheck > 0 else 0
    print(f"Model2Vec precision@5: {m2vP5:.0%} ({totalHit}/{totalCheck})")

    # 5. 하이브리드: SemanticMap + Model2Vec
    print("\n=== Hybrid (SemanticMap + Model2Vec) ===")
    totalHit = totalCheck = 0
    latencies = []

    for query, expectedKws in QUERIES:
        t0 = time.time()

        # SemanticMap 결과
        smResult = searchSemantic(df, query, topK=10)
        smRcepts = set(smResult["rcept_no"].to_list()) if smResult.height > 0 else set()

        # Model2Vec 결과
        indices, scores = searchModel2Vec(model, df, allVecs, query, topK=10)
        m2vRcepts = {}
        for idx, score in zip(indices, scores):
            row = df.row(idx, named=True)
            m2vRcepts[row["rcept_no"]] = {"score": float(score), "row": row}

        # 합산: SM에도 있고 M2V에도 있으면 최상위
        allRcepts = {}
        for rcept in smRcepts:
            allRcepts[rcept] = allRcepts.get(rcept, 0) + 2
        for rcept, data in m2vRcepts.items():
            allRcepts[rcept] = allRcepts.get(rcept, 0) + 1

        topRcepts = sorted(allRcepts.items(), key=lambda x: x[1], reverse=True)[:5]

        elapsed = time.time() - t0
        latencies.append(elapsed)

        hits = 0
        for rcept, _ in topRcepts:
            if rcept in m2vRcepts:
                row = m2vRcepts[rcept]["row"]
            else:
                rows = df.filter(pl.col("rcept_no") == rcept)
                if rows.height == 0:
                    continue
                row = rows.row(0, named=True)
            combined = f"{row['report_nm']} {row.get('section_title', '')}".lower()
            if any(kw in combined for kw in expectedKws):
                hits += 1

        totalHit += hits
        totalCheck += min(5, len(topRcepts))

    hybridP5 = totalHit / totalCheck if totalCheck > 0 else 0
    print(f"Hybrid precision@5: {hybridP5:.0%} ({totalHit}/{totalCheck})")
    print(f"Hybrid 평균 속도: {np.mean(latencies)*1000:.0f}ms")

    # 최종 비교표
    print(f"\n{'='*60}")
    print(f"{'방법':25s} {'precision@5':12s} {'cold start':12s}")
    print(f"{'-'*60}")
    print(f"{'BM25(substring)':25s} {'71%':12s} {'0ms':12s}")
    print(f"{'SemanticMap':25s} {'68%':12s} {'0ms':12s}")
    print(f"{'Model2Vec(dart증류)':25s} {f'{m2vP5:.0%}':12s} {'<500ms':12s}")
    print(f"{'Hybrid(SM+M2V)':25s} {f'{hybridP5:.0%}':12s} {'<500ms':12s}")
    print(f"{'임베딩(ko-sroberta)':25s} {'83%':12s} {'12,700ms':12s}")
