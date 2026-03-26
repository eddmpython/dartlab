"""
실험 ID: 010b
실험명: non_current_assets 오매핑 제거

목적:
- 010 Phase 1에서 발견된 세부 태그 → non_current_assets 오매핑 제거
- NoncurrentAssets (합산 태그)만 남기고, noncurrent suffix 세부 태그는 제거
- 동일 패턴인 non_current_liabilities도 함께 점검

방법:
1. learnedSynonyms에서 non_current_assets로 매핑된 태그 전수 스캔
2. NoncurrentAssets 외 세부 태그 식별 + 제거
3. non_current_liabilities도 동일 패턴 스캔 + 제거
4. 제거 후 007 재실행으로 D4 정확도 확인

결과 (실험 후 작성):
- [아래에 기록]

결론:
- [아래에 기록]

실험일: 2026-03-10
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

_MAPPER_DATA = Path(__file__).resolve().parents[2] / "mapperData"

KEEP_TAGS = {
    "non_current_assets": {"noncurrentassets", "assetsnoncurrent"},
    "non_current_liabilities": {"noncurrentliabilities", "liabilitiesnoncurrent"},
}


def loadLearnedSynonyms():
    path = _MAPPER_DATA / "learnedSynonyms.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def saveLearnedSynonyms(data):
    path = _MAPPER_DATA / "learnedSynonyms.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  saved: {path}")


def loadStandardAccounts():
    path = _MAPPER_DATA / "standardAccounts.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["accounts"]


def scanAndRemove():
    print("=" * 70)
    print("010b: non_current_assets/liabilities 오매핑 제거")
    print("=" * 70)

    accounts = loadStandardAccounts()
    commonTagsSet = set()
    for acct in accounts:
        for tag in acct.get("commonTags", []):
            commonTagsSet.add(tag.lower())

    learned = loadLearnedSynonyms()
    tagMappings = learned["tagMappings"]
    before = len(tagMappings)

    targetSids = set(KEEP_TAGS.keys())
    toRemove = {}

    for sid in targetSids:
        keepTags = KEEP_TAGS[sid]
        mismapped = []
        for tag, mappedSid in tagMappings.items():
            if mappedSid == sid:
                if tag not in keepTags and tag not in commonTagsSet:
                    mismapped.append(tag)
        toRemove[sid] = mismapped

    for sid, tags in toRemove.items():
        print(f"\n  [{sid}] 제거 대상: {len(tags)}개")
        for tag in sorted(tags)[:30]:
            print(f"    - {tag}")
        if len(tags) > 30:
            print(f"    ... +{len(tags) - 30}개 더")

    totalRemove = sum(len(v) for v in toRemove.values())
    print(f"\n  총 제거 대상: {totalRemove}개")

    if totalRemove == 0:
        print("  제거할 것 없음")
        return

    for sid, tags in toRemove.items():
        for tag in tags:
            if tag in tagMappings:
                del tagMappings[tag]

    after = len(tagMappings)
    print(f"\n  before: {before}")
    print(f"  removed: {totalRemove}")
    print(f"  after: {after}")

    learned["tagMappings"] = tagMappings
    learned["_metadata"]["totalMappings"] = after
    saveLearnedSynonyms(learned)

    nca = [t for t, s in tagMappings.items() if s in {"non_current_assets", "noncurrent_assets"}]
    ncl = [t for t, s in tagMappings.items() if s in {"non_current_liabilities", "noncurrent_liabilities"}]
    print(f"\n  남은 non_current_assets 매핑: {len(nca)}개 — {sorted(nca)}")
    print(f"  남은 non_current_liabilities 매핑: {len(ncl)}개 — {sorted(ncl)}")


if __name__ == "__main__":
    scanAndRemove()
    print("\n  완료.")
