"""실험 ID: 001
실험명: SCE(자본변동표) 원본 데이터 구조 탐색

목적:
- SCE 데이터의 실제 구조 파악 (매트릭스? 플랫?)
- account_detail 필드의 역할 확인 (자본항목 구분자인지)
- 전종목 SCE 존재 비율 확인
- BS/IS/CF 피벗과 다른 점 정리
- 매핑 가능한 계정 목록 확인

가설:
1. SCE는 행(변동사유) × 열(자본항목) 매트릭스 구조일 것
2. account_detail이 자본항목(자본금, 자본잉여금, 이익잉여금 등) 구분자일 것
3. 대부분 종목이 SCE 데이터를 가지고 있을 것 (90%+)

방법:
1. 삼성전자 SCE 원본 데이터 전체 구조 출력
2. account_detail 값 분포 확인
3. account_id 분포 확인 (매핑 가능성)
4. 연도별/분기별 행 수 확인
5. 전종목 SCE 존재 여부 스캔

결과:
1. 전종목 SCE 존재율: 2,564/2,743 = 93.5%
   - 행 수: min=12, max=10,811, median=2,223, avg=2,308

2. SCE 구조 = 행(변동사유) × 열(자본항목) 매트릭스
   - account_nm = 변동사유 (기초자본, 배당, 당기순이익, 자기주식취득 등)
   - account_detail = 자본항목 계층 (파이프'|'로 구분)
     예: '자본 [구성요소]|지배기업의 소유주에게 귀속되는 지분 [구성요소]|이익잉여금 [구성요소]'
   - ord = 행 순서 (변동사유 순서)
   - thstrm_amount = 해당 변동사유 × 자본항목의 금액

3. account_detail 자본항목 계층:
   - 최상위: '연결재무제표 [member]' / '별도재무제표 [member]' (= fs_div)
   - 1단계: '자본 [구성요소]|지배기업 소유주지분', '자본 [구성요소]|비지배지분'
   - 2단계: '자본금', '주식발행초과금', '이익잉여금', '기타자본구성요소'
   - 연도에 따라 '[member]' vs '[구성요소]' 표기 불일치

4. account_id:
   - 27.4%가 '-표준계정코드 미사용-' (매핑 불가능, account_nm으로만 식별)
   - 나머지는 ifrs-full_ 또는 dart_ 프리픽스 (BS/IS/CF와 동일 매핑 파이프라인 가능)

5. 삼성전자 2024 4분기 CFS 기준 91행 (13개 변동사유 × 7개 자본항목)
   변동사유: 연결실체의변동, 기초자본, 연결실체내자본거래, 배당, 자본총계,
            현금흐름위험회피, 해외사업장환산, 기타, 기타포괄손익-공정가치금융자산,
            순확정급여부채재측정, 당기순이익, 자기주식의취득, 관계기업OCI지분
   자본항목: 자본금, 주식발행초과금, 이익잉여금, 기타자본구성요소,
            지배기업소유주지분(소계), 비지배지분, 연결재무제표전체(총계)

6. 회사별 계정명 변동 심함:
   - 삼성전자: 34개 account_nm
   - 동화약품: 43개
   - KB금융: 48개
   - 포스코퓨처엠: 73개
   - 에코프로비엠: 82개 (기초자본 vs 기초자본 잔액 등 표기 불일치)

결론:
1. 가설 1 채택 — 행(변동사유) × 열(자본항목) 매트릭스 구조 확인
2. 가설 2 채택 — account_detail이 자본항목 구분자 (파이프 구분 계층)
3. 가설 3 채택 — 93.5% 보유
4. BS/IS/CF 피벗과 완전히 다른 구조 — 별도 피벗 로직 필요
5. 핵심 과제:
   a) account_detail 정규화 (member vs 구성요소, 표기 불일치)
   b) account_nm 동의어 정리 (34~82개로 회사마다 다름)
   c) CFS/OFS 선택 (BS/IS/CF와 동일 정책)
   d) 연도별 구조 변경 대응 (2015~2025 동안 표기법 변경)
6. 가치 판단: SCE 고유 데이터 = 자기주식 거래, OCI 세부, 연결실체 변동, 배당 금액
   → 이미 CF에 배당금지급, BS에 자기주식 잔액이 있으므로 SCE의 추가 가치는
   "자본 변동의 원인 분해"와 "자본항목별 금액 변동" 정도
7. 다음 실험: 핵심 변동사유(기초/기말/배당/순이익/자기주식) account_detail 통합 피벗 가능성

실험일: 2026-03-10
"""

from __future__ import annotations

import polars as pl


def exploreSamsung():
    from dartlab.core.dataLoader import loadData

    df = loadData("005930", category="finance")
    if df is None:
        print("데이터 없음")
        return

    sce = df.filter(pl.col("sj_div") == "SCE")
    print(f"=== 삼성전자 SCE ===")
    print(f"총 행 수: {sce.height}")
    print(f"컬럼: {sce.columns}")
    print()

    print("--- account_detail 값 분포 ---")
    if "account_detail" in sce.columns:
        detail_counts = (
            sce.group_by("account_detail")
            .len()
            .sort("len", descending=True)
        )
        for row in detail_counts.iter_rows(named=True):
            print(f"  {row['account_detail']!r}: {row['len']}행")
    print()

    print("--- account_nm 값 분포 ---")
    nm_counts = (
        sce.group_by("account_nm")
        .len()
        .sort("len", descending=True)
    )
    for row in nm_counts.iter_rows(named=True):
        print(f"  {row['account_nm']}: {row['len']}행")
    print()

    print("--- account_id 값 분포 (상위 20) ---")
    id_counts = (
        sce.group_by("account_id")
        .len()
        .sort("len", descending=True)
        .head(20)
    )
    for row in id_counts.iter_rows(named=True):
        print(f"  {row['account_id']}: {row['len']}행")
    print()

    print("--- 연도별 행 수 ---")
    year_counts = (
        sce.group_by("bsns_year")
        .len()
        .sort("bsns_year")
    )
    for row in year_counts.iter_rows(named=True):
        print(f"  {row['bsns_year']}: {row['len']}행")
    print()

    print("--- 보고서별 행 수 ---")
    if "reprt_nm" in sce.columns:
        reprt_counts = (
            sce.group_by("reprt_nm")
            .len()
            .sort("len", descending=True)
        )
        for row in reprt_counts.iter_rows(named=True):
            print(f"  {row['reprt_nm']}: {row['len']}행")
    print()

    print("--- 2024 사업보고서 SCE 샘플 (전체) ---")
    sample = sce.filter(
        (pl.col("bsns_year") == "2024")
        & (pl.col("reprt_nm").str.contains("사업"))
    )
    if sample.is_empty():
        sample = sce.filter(pl.col("bsns_year") == "2023")
        sample = sample.filter(pl.col("reprt_nm").str.contains("사업"))

    cols = ["account_id", "account_nm", "account_detail",
            "thstrm_amount", "frmtrm_amount", "bfefrmtrm_amount", "ord"]
    cols = [c for c in cols if c in sample.columns]
    sample = sample.select(cols).sort("ord")

    print(f"행 수: {sample.height}")
    for row in sample.iter_rows(named=True):
        detail = row.get("account_detail", "")
        amt = row.get("thstrm_amount", "")
        print(f"  [{row.get('ord', '')}] {row['account_nm']}"
              f" | detail={detail!r} | amt={amt}")


def scanAllStocks():
    from dartlab.core.dataLoader import loadData
    from dartlab.core.dataConfig import listStockCodes

    codes = listStockCodes("finance")
    total = len(codes)
    hasSce = 0
    sceRows = []

    for code in codes:
        df = loadData(code, category="finance")
        if df is None:
            continue
        sce = df.filter(pl.col("sj_div") == "SCE")
        if sce.height > 0:
            hasSce += 1
            sceRows.append(sce.height)

    print(f"\n=== 전종목 SCE 스캔 ===")
    print(f"총 종목: {total}")
    print(f"SCE 보유: {hasSce} ({hasSce/total*100:.1f}%)")
    if sceRows:
        print(f"SCE 행 수: min={min(sceRows)}, max={max(sceRows)}, "
              f"median={sorted(sceRows)[len(sceRows)//2]}, "
              f"avg={sum(sceRows)/len(sceRows):.0f}")


if __name__ == "__main__":
    exploreSamsung()
    print("\n" + "=" * 60 + "\n")
    scanAllStocks()
