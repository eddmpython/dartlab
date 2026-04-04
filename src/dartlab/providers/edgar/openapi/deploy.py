"""EDGAR 데이터 → HuggingFace 데이터셋 배포.

수집된 EDGAR parquet 파일들을 HF datasets repo에 업로드한다.
청크 기반 업로드로 대용량 처리.

사용법::

    from dartlab.providers.edgar.openapi.deploy import deployEdgarToHF
    deployEdgarToHF(categories=["finance", "docs"])
"""

from __future__ import annotations

import os
from pathlib import Path

from dartlab.core.dataConfig import DATA_RELEASES, HF_REPO

_CATEGORY_MAP = {
    "finance": "edgar",
    "docs": "edgarDocs",
    "scan": "edgarScan",
}

_UPLOAD_CHUNK = 100


def deployEdgarToHF(
    categories: list[str] | None = None,
    *,
    token: str | None = None,
    dryRun: bool = False,
) -> dict[str, int]:
    """EDGAR 데이터를 HuggingFace datasets repo에 업로드.

    Parameters
    ----------
    categories : list
        업로드할 카테고리 ("finance", "docs", "scan").
    token : str
        HuggingFace API 토큰 (없으면 HF_TOKEN 환경변수).
    dryRun : bool
        True면 업로드하지 않고 파일 목록만 반환.

    Returns
    -------
    dict : {"finance": N, "docs": M, ...} 업로드된 파일 수.
    """
    from huggingface_hub import HfApi

    hfToken = token or os.getenv("HF_TOKEN")
    if not hfToken and not dryRun:
        raise ValueError("HF_TOKEN이 필요합니다. 환경변수 또는 token 파라미터로 설정하세요.")

    cats = categories or ["finance", "docs"]

    # 카테고리 검증
    validCats = []
    for cat in cats:
        configKey = _CATEGORY_MAP.get(cat, cat)
        if configKey not in DATA_RELEASES:
            print(f"[deploy] 카테고리 '{cat}' → configKey '{configKey}'가 DATA_RELEASES에 없음. 스킵.")
            continue
        validCats.append(cat)

    if not validCats:
        print("[deploy] 유효한 카테고리가 없습니다.")
        return {}

    api = HfApi(token=hfToken) if not dryRun else None
    result: dict[str, int] = {}

    for cat in validCats:
        configKey = _CATEGORY_MAP.get(cat, cat)
        config = DATA_RELEASES[configKey]

        from dartlab import config as _cfg

        localDir = Path(_cfg.dataDir) / config["dir"]
        if not localDir.exists():
            print(f"[deploy] {localDir} 없음. 스킵.")
            result[cat] = 0
            continue

        parquets = sorted(localDir.glob("*.parquet"))
        if not parquets:
            print(f"[deploy] {localDir}에 parquet 없음. 스킵.")
            result[cat] = 0
            continue

        hfDir = config["dir"]

        if dryRun:
            print(f"[deploy] DRY RUN — {cat}: {len(parquets)}개 파일 → {HF_REPO}/{hfDir}/")
            result[cat] = len(parquets)
            continue

        print(f"[deploy] {cat}: {len(parquets)}개 파일 업로드 시작 → {HF_REPO}/{hfDir}/")

        uploaded = 0
        for i in range(0, len(parquets), _UPLOAD_CHUNK):
            chunk = parquets[i : i + _UPLOAD_CHUNK]
            for fp in chunk:
                hfPath = f"{hfDir}/{fp.name}"
                try:
                    api.upload_file(
                        path_or_fileobj=str(fp),
                        path_in_repo=hfPath,
                        repo_id=HF_REPO,
                        repo_type="dataset",
                    )
                    uploaded += 1
                except (OSError, ValueError, RuntimeError) as e:
                    print(f"  [실패] {fp.name}: {e}")

            print(f"  {min(i + _UPLOAD_CHUNK, len(parquets))}/{len(parquets)} 완료")

        result[cat] = uploaded
        print(f"[deploy] {cat}: {uploaded}/{len(parquets)} 업로드 완료")

    return result
