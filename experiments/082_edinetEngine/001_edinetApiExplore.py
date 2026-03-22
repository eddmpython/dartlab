"""실험 ID: 001
실험명: EDINET API v2 응답 구조 탐색

목적:
- EDINET API v2의 실제 응답 구조를 파악
- 유가증권보고서(120) 서류 목록 확인
- CSV 다운로드 후 파일 구조 분석
- 주요 기업 (토요타 E02144, 소니 E01777) 데이터 확인

가설:
1. documents.json API가 날짜별 서류 목록을 JSON으로 반환
2. CSV 다운로드(type=5) 시 재무+서술형 데이터가 분리된 CSV 포함
3. 대형 기업은 연 1회 유가증권보고서 제출 (3월 결산 기준 6월경)

방법:
1. 특정 날짜의 서류 목록 조회 (6월 말 = 결산서류 집중기)
2. 유가증권보고서(docTypeCode=120) 필터링
3. 첫 번째 서류 CSV 다운로드
4. ZIP 내용 + CSV 컬럼 구조 분석

결과:
(API 키 발급 후 실행)

결론:
(API 키 발급 후 실행)

실험일: 2026-03-22
"""

from __future__ import annotations

import json
import os
import sys
import zipfile
from pathlib import Path

# EDINET API 키 확인
API_KEY = os.environ.get("EDINET_API_KEY", "")
if not API_KEY:
    print("EDINET_API_KEY 환경변수가 설정되지 않았습니다.")
    print()
    print("발급 절차:")
    print("  1. https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1 접속")
    print("  2. 팝업 차단 해제 필수 (api.edinet-fsa.go.jp 허용)")
    print("  3. 전화번호: 국가코드 +81 선택, '80-XXXX-XXXX' 형식 (0 제외)")
    print("  4. 연락처 등록 후 API 키 표시됨")
    print()
    print(".env에 EDINET_API_KEY=xxx 추가 후 재실행하세요.")
    sys.exit(1)

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def explore():
    from dartlab.engines.company.edinet.openapi.client import EdinetClient

    client = EdinetClient(apiKey=API_KEY)

    # ── 1. 서류 목록 조회 (6월 말 = 3월 결산 보고서 집중기) ──
    print("=" * 60)
    print("1. 서류 목록 조회 (2024-06-28)")
    docs = client.listDocuments("2024-06-28")
    print(f"   전체 서류: {len(docs)}건")

    # 유가증권보고서 필터
    yuho = [d for d in docs if d.get("docTypeCode") == "120"]
    print(f"   유가증券보고서(120): {len(yuho)}건")

    if yuho:
        # 첫 번째 서류 구조 출력
        first = yuho[0]
        print(f"\n   첫 번째 서류 키:")
        for k, v in first.items():
            print(f"     {k}: {v!r}")

    # ── 2. 여러 날짜 샘플 ──
    print(f"\n2. 날짜별 유가증권보고서 건수")
    for date in ["2024-06-20", "2024-06-25", "2024-06-28", "2024-06-30"]:
        try:
            d = client.listDocuments(date, docType="120")
            print(f"   {date}: {len(d)}건")
        except Exception as e:
            print(f"   {date}: 오류 — {e}")

    # ── 3. CSV 다운로드 (첫 번째 유가증권보고서) ──
    if yuho:
        docId = yuho[0].get("docID", "")
        filer = yuho[0].get("filerName", "unknown")
        print(f"\n3. CSV 다운로드: {filer} ({docId})")

        try:
            zipPath = client.downloadDocument(docId, OUTPUT_DIR, downloadType=5)
            print(f"   저장: {zipPath}")
            print(f"   크기: {zipPath.stat().st_size:,} bytes")

            # ZIP 내용 분석
            with zipfile.ZipFile(zipPath, "r") as zf:
                names = zf.namelist()
                print(f"   ZIP 내 파일: {len(names)}개")
                for name in names[:20]:
                    info = zf.getinfo(name)
                    print(f"     {name} ({info.file_size:,} bytes)")

                # 첫 번째 CSV 내용 미리보기
                csv_files = [n for n in names if n.endswith(".csv")]
                if csv_files:
                    print(f"\n   첫 번째 CSV 미리보기: {csv_files[0]}")
                    with zf.open(csv_files[0]) as f:
                        content = f.read()
                        for enc in ("utf-8", "shift_jis", "cp932"):
                            try:
                                text = content.decode(enc)
                                break
                            except UnicodeDecodeError:
                                continue
                        lines = text.split("\n")
                        for line in lines[:5]:
                            print(f"     {line[:200]}")
        except Exception as e:
            print(f"   다운로드 실패: {e}")

    # ── 4. EDINET 코드 목록 ──
    print(f"\n4. EDINET 코드 목록 (기업 마스터)")
    try:
        codes = client.listEdinetCodes()
        print(f"   총 기업: {len(codes)}개")
        if codes:
            print(f"   첫 번째 기업 키:")
            for k, v in codes[0].items():
                print(f"     {k}: {v!r}")

            # 주요 기업 찾기
            targets = {"E02144": "トヨタ", "E01777": "ソニー", "E00984": "ソフトバンク"}
            for code, name in targets.items():
                found = [c for c in codes if c.get("edinetCode") == code]
                if found:
                    print(f"   {name}: {found[0].get('filerName', '?')} ({code})")
    except Exception as e:
        print(f"   조회 실패: {e}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    explore()
