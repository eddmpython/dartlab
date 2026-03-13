"""
실험 ID: 057-009
실험명: EDGAR sectionMappings draft 생성

목적:
- 현재 canonical boundary 후보를 기반으로 EDGAR sectionMappings 초안을 생성한다.
- 패키지 mapperData에 들어갈 최소 안정 매핑을 실험 산출물로 남긴다.

가설:
1. 10-K와 20-F의 핵심 item title은 바로 stable topic id로 고정할 수 있다.
2. 10-Q는 현재 Full Document 하나만 유지하는 것이 안전하다.

방법:
1. 패키지의 sectionMappings.json을 읽는다.
2. output/formTopicDrafts.json의 candidate와 대조한다.
3. current mapping coverage와 미매핑 candidate를 출력한다.

결과 (실험 후 작성):
- 실행 후 갱신

결론:
- 실행 후 갱신

실험일: 2026-03-12
"""

from __future__ import annotations

import json
from pathlib import Path


def draftPath() -> Path:
    return Path(__file__).resolve().parent / "output" / "formTopicDrafts.json"


def mappingPath() -> Path:
    return Path(__file__).resolve().parents[2] / "src" / "dartlab" / "engines" / "edgar" / "docs" / "sections" / "mapperData" / "sectionMappings.json"


def main() -> None:
    drafts = json.loads(draftPath().read_text(encoding="utf-8"))
    mappings = json.loads(mappingPath().read_text(encoding="utf-8"))

    print("=" * 72)
    print("057-009 EDGAR sectionMappings draft")
    print("=" * 72)

    for formType, rows in drafts.items():
        covered = 0
        uncovered: list[str] = []
        for row in rows:
            title = row["section_title"]
            if title in mappings:
                covered += 1
            else:
                uncovered.append(title)
        print(f"{formType}: covered={covered}/{len(rows)}")
        if uncovered:
            for title in uncovered:
                print(f"  - {title}")


if __name__ == "__main__":
    main()
