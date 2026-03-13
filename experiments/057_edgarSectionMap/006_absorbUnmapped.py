"""
실험 ID: 057-006
실험명: unmapped title 흡수 — sectionMappings.json 업데이트

목적:
- 005에서 발견된 unmapped title을 분류하고 sectionMappings.json에 추가한다.
- 10-K/10-Q 정규화 개선 + 40-F 전용 매핑 추가

가설:
1. 10-K/10-Q unmapped는 대부분 정규화 강화로 해결된다.
2. 40-F는 별도 topicId 체계가 필요하다.

방법:
1. 005 unmapped 목록을 분류한다:
   a. 정규화로 기존 매핑에 합류 가능한 것
   b. 새 topicId가 필요한 것
   c. 무시해도 되는 것 (1 ticker, 1~2 rows)
2. mapper.py 정규화 규칙 추가
3. sectionMappings.json에 새 항목 추가
4. 005를 다시 돌려서 커버리지 100% 확인

분류 결과:

=== 10-K unmapped (7개) ===
- Item 8A/8B "CONSOLIDATED FINANCIAL STATEMENTS..." → 이미 mapper에 8A/8B 처리 있음, 대문자 매칭 안 됨
  → mapper.py 정규화 강화 (upper 비교 추가)
- Item 103 "of SEC Regulation S-K..." → 405/601과 동일 패턴, 환경 규정
  → sectionMappings.json에 추가
- Item 8A/8B "ITEM 8A"/"ITEM 8B" → 이미 mapper에 처리 있으나 매칭 안 됨
  → mapper.py에서 이미 처리하고 있음 — normalizeSectionTitle 결과 확인 필요

=== 10-Q unmapped (18개) ===
- "Part I - Item 6. EXHIBITS" → 대소문자 차이 (기존: "Part II - Item 6. Exhibits")
  주의: Part I vs Part II 차이! Part I에 Item 6은 없어야 정상
  → 실제로는 Part II - Item 6의 파싱 오류일 수 있음
- "Part I - Item 5. OTHER INFORMATION" / "Other Information" / "Other Information." → Part II - Item 5
  → 이것도 Part 오분류 가능성
- AAL 전용 (Item 1A, 1B에 회사명 포함) → 특이 케이스
  → sectionMappings에 추가
- markdown table 잔해 ("| Item 6. | Exhibits |" 등) → 정규화로 처리
  → mapper.py에 pipe 정규화 추가
- "Part II - Item 7. Signatures" → Signatures 매핑 추가

=== 20-F unmapped (1개) ===
- "Item 3D. Risk Factors..." → Item 3 sub-item
  → sectionMappings에 추가

=== 40-F unmapped (20개) ===
전부 새 매핑 필요. Canadian form 고유 구조.

실험일: 2026-03-13
"""

from __future__ import annotations

import json
from pathlib import Path


def _buildNewMappings() -> dict[str, str]:
    return {
        "Item 103. of SEC Regulation S-K": "item103EnvironmentalDisclosure",

        "Item 3D.  Risk Factors. Additional risks and uncertainties not currently known to us or": "item3KeyInformation",

        "Part I - Item 6. EXHIBITS": "partIIItem6Exhibits",
        "Part I - Item 6. Exhibits": "partIIItem6Exhibits",
        "Part I - Item 6. Exhibits.": "partIIItem6Exhibits",
        "Part I - Item 5. OTHER INFORMATION": "partIIItem5OtherInformation",
        "Part I - Item 5. Other Information": "partIIItem5OtherInformation",
        "Part I - Item 5. Other Information.": "partIIItem5OtherInformation",
        "Part I - Item 5.  Other Information": "partIIItem5OtherInformation",
        "Part I - Item 1A. RISK FACTORS": "partIIItem1ARiskFactors",
        "Part I - Item 1B. Collateral Related Covenants": "partIItem1BCollateralRelatedCovenants",

        "Part I - Item 1A. CONDENSED CONSOLIDATED FINANCIAL STATEMENTS OF AMERICAN AIRLINES GROUP INC.": "partIItem1FinancialStatements",
        "Part I - Item 1A. AMERICAN AIRLINES GROUP INC. CONDENSED CONSOLIDATED FINANCIAL STATEMENTS": "partIItem1FinancialStatements",
        "Part I - Item 1B. AMERICAN AIRLINES, INC. CONDENSED CONSOLIDATED FINANCIAL STATEMENTS": "partIItem1FinancialStatements",
        "Part I - Item 1B. CONDENSED CONSOLIDATED FINANCIAL STATEMENTS OF AMERICAN AIRLINES, INC.": "partIItem1FinancialStatements",

        "Part II - Item 7. Signatures": "signatures",

        "Code Of Ethics": "codeOfEthics",
        "Off-Balance Sheet Arrangements": "offBalanceSheetArrangements",
        "Principal Accountant Fees And Services": "principalAccountantFeesAndServices",
        "Disclosure Controls And Procedures": "disclosureControlsAndProcedures",
        "Exhibit Index": "exhibitIndex",
        "Consent To Service Of Process": "consentToServiceOfProcess",
        "Annual Information Form": "annualInformationForm",
        "Audit Committee Pre-Approval Policies And Procedures": "auditCommitteePreApprovalPolicies",
        "Mine Safety Disclosure": "mineSafetyDisclosure",
        "Audit Committee": "auditCommittee",
        "Audited Annual Financial Statements": "auditedAnnualFinancialStatements",
        "Undertakings": "undertakings",
        "New York Stock Exchange Disclosure": "nyseDisclosure",
        "Financial Statements": "financialStatements",
        "Recovery Of Erroneously Awarded Compensation": "recoveryOfErroneouslyAwardedCompensation",
        "Note To United States Readers - Differences": "noteToUSReadersDifferences",
        "Management'S Discussion And Analysis": "mdna",
        "MD&A": "mdna",
        "Cash Requirements": "cashRequirements",
        "Disclosure Regarding Foreign Jurisdictions That Prevent Inspections": "disclosureRegardingForeignJurisdictions",
    }


def main() -> None:
    mappingPath = (
        Path(__file__).resolve().parents[2]
        / "src" / "dartlab" / "engines" / "edgar" / "docs"
        / "sections" / "mapperData" / "sectionMappings.json"
    )

    existing = json.loads(mappingPath.read_text(encoding="utf-8"))
    newMappings = _buildNewMappings()

    added = 0
    for key, value in newMappings.items():
        if key not in existing:
            existing[key] = value
            added += 1
            print(f"  + {key} → {value}")
        else:
            print(f"  = {key} (이미 있음: {existing[key]})")

    mappingPath.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print()
    print(f"기존: {len(existing) - added}, 추가: {added}, 합계: {len(existing)}")


if __name__ == "__main__":
    main()
