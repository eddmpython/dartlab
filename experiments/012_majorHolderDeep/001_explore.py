"""
실험 ID: 012-001
실험명: 주주에 관한 사항 — 전체 데이터 탐색

목적:
- 사업보고서 "주주에 관한 사항" 섹션에 어떤 테이블들이 존재하는지 전수 조사
- 기존 majorHolder 모듈이 최대주주 테이블만 추출 — 나머지 테이블 파악
- 소액주주, 기관/외국인, 지분 변동 사유 등 추가 데이터 확인

가설:
1. "주주에 관한 사항" 섹션에는 최대주주 외에 2~3개 이상의 추가 테이블이 존재
2. 소액주주 현황, 주식 소유 분포 등 추출 가능한 데이터가 더 있을 것

방법:
1. 삼성전자(005930) 최신 사업보고서에서 "주주" 관련 섹션 전체 내용 출력
2. 섹션별 서브타이틀, 테이블 헤더 패턴 분류
3. 추가 추출 가능 항목 목록 작성

결과:
=== 삼성전자 (005930) "VII. 주주에 관한 사항" 서브섹션 ===

섹션 구조:
1. 최대주주 및 그 특수관계인의 주식소유 현황 (기존 추출 완료)
2. 최대주주 관련 정보
   가. 최대주주의 개요
   (1) 최대주주(삼성생명보험)의 기본정보
   (2) 최대주주의 최근 3개년 사업현황
   (3) 최대주주의 재무현황 등
   (4) 최대주주와의 거래내용
   나. 최대주주 변동내역 → ★ 추가 추출 가능
3. 주식의 분포
   가. 5% 이상 주주현황 → ★ 추가 추출 가능
   나. 소유주식수별 분포 → ★ 추가 추출 가능
4. 주식사무 (명의개서, 결산일 등 — 텍스트)
5. 의결권 현황 → ★ 추가 추출 가능 (발행주식수, 의결권제한, 자기주식)
6. 배당에 관한 사항 (dividend에서 처리)

결론:
추가 추출 가능 항목 4개 발견:
1. 최대주주 변동내역 — 변동일자, 변동사유
2. 5% 이상 주주현황 — 기관/외국인 대주주
3. 소유주식수별 분포 — 소액주주 비율
4. 의결권 현황 — 의결권 행사 가능 주식수

실험일: 2026-03-07
"""

import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport


def explore(stockCode: str):
    df = loadData(stockCode)
    if df is None:
        print(f"[{stockCode}] 데이터 없음")
        return

    corpName = df["corp_name"][0] if "corp_name" in df.columns else stockCode

    years = sorted(df["year"].unique().to_list(), reverse=True)
    year = years[0]

    report = selectReport(df, year, reportKind="annual")
    if report is None:
        print(f"[{corpName}] {year} 사업보고서 없음")
        return

    print(f"=== {corpName} ({stockCode}) {year} 사업보고서 ===")

    holderRows = report.filter(pl.col("section_title").str.contains("주주"))
    print(f"'주주' 포함 섹션: {holderRows.height}개\n")

    for i in range(holderRows.height):
        title = holderRows["section_title"][i]
        content = holderRows["section_content"][i]
        lines = content.split("\n")

        print(f"--- 섹션 {i+1}: {title} ({len(lines)}줄) ---")

        for j, line in enumerate(lines):
            s = line.strip().replace("\xa0", " ")
            if not s:
                continue

            if not s.startswith("|"):
                if re.match(r"^(VII|[가-차]|[\d]{1,2})\.", s) or \
                   re.match(r"^\(\d+\)", s) or \
                   any(kw in s for kw in ["주주", "소유", "분포", "의결권", "변동", "배당", "사무"]):
                    print(f"  [{j:3d}] {s[:100]}")
            else:
                if "---" in s:
                    continue
                cells = [c.strip() for c in s.split("|") if c.strip()]
                cellText = " | ".join(cells)
                isHeader = any(kw in cellText for kw in [
                    "구분", "성 명", "성명", "주주", "소유", "기초", "기말",
                    "종류", "합 계", "합계", "의결권", "주식수", "지분", "5%",
                    "보통주", "우선주", "주식사무", "명의개서"
                ])
                if isHeader or j < 5:
                    print(f"  T[{j:3d}] {cellText[:100]}")

        print()


if __name__ == "__main__":
    explore("005930")
    print("\n" + "=" * 80 + "\n")
    explore("000660")
    print("\n" + "=" * 80 + "\n")
    explore("035420")
