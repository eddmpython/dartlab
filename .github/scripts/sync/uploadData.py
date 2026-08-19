"""(shim) HF 업로드 — 본체는 dartlab.pipeline.hfUpload.uploadCategoryToHf 로 이동.

CLI(--target hf/gh) + SYNC_CATEGORY env 호환만 유지. GitHub Releases(--target gh)는
2026-04-08 폐지(no-op). 신규 코드는 ``python -m dartlab.pipeline ...`` 또는
``dartlab.pipeline.uploadCategoryToHf`` 를 직접 쓴다.
"""

import argparse
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, choices=["hf", "gh"])
    args = parser.parse_args()

    if args.target == "gh":
        print("[uploadData] GitHub Releases 업로드는 폐지됨(2026-04-08, HF만 유지) — skip")
        return

    category = os.environ.get("SYNC_CATEGORY", "finance")
    if "DARTLAB_DATA_DIR" not in os.environ:
        os.environ["DARTLAB_DATA_DIR"] = os.path.join(os.getcwd(), "data")

    # SYNC_CHANGED_FILE: 이 호출에서만 올릴 상대경로 목록. checkpoint 업로더가 배치 단위로 넘긴다.
    # 없으면 기존대로 dist/changed_{category}.txt(누적 매니페스트)를 hfUpload 가 읽는다.
    changedFiles = None
    changedFile = os.environ.get("SYNC_CHANGED_FILE", "").strip()
    if changedFile:
        text = Path(changedFile).read_text(encoding="utf-8") if Path(changedFile).exists() else ""
        changedFiles = [line.strip() for line in text.splitlines() if line.strip()]

    from dartlab.pipeline.hfUpload import uploadCategoryToHf

    uploadCategoryToHf(category, changedFiles=changedFiles)


if __name__ == "__main__":
    main()
