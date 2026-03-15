"""데이터 릴리즈 중앙 설정.

태그명, 디렉토리, 라벨을 1곳에서 관리.
새 카테고리 추가 시 DATA_RELEASES에 한 줄만 추가하면 전체 반영.

finance는 GitHub Release 1000에셋 제한 때문에 종목코드 범위별 다중 태그 사용.
"""

REPO = "eddmpython/dartlab"
REPO_URL = f"https://github.com/{REPO}"

_SHARD_RANGES = [
    {"min": 0, "max": 49999},
    {"min": 50000, "max": 99999},
    {"min": 100000, "max": 199999},
    {"min": 200000, "max": 999999},
]

DATA_RELEASES: dict[str, dict] = {
    "docs": {
        "tag": "data-docs",
        "dir": "dart/docs",
        "label": "DART 공시 문서 데이터",
    },
    "finance": {
        "dir": "dart/finance",
        "label": "재무 숫자 데이터",
        "shards": [{"tag": f"data-finance-{i + 1}", **r} for i, r in enumerate(_SHARD_RANGES)],
    },
    "report": {
        "dir": "dart/report",
        "label": "정기보고서 데이터",
        "shards": [{"tag": f"data-report-{i + 1}", **r} for i, r in enumerate(_SHARD_RANGES)],
    },
    "edgarDocs": {
        "tag": "data-edgar-docs",
        "dir": "edgar/docs",
        "label": "SEC EDGAR 공시 문서 데이터",
    },
    "edgar": {
        "dir": "edgar/finance",
        "label": "SEC EDGAR 재무 데이터",
    },
}


def shardTag(stockCode: str, category: str = "finance") -> str:
    """종목코드 → 해당 카테고리의 shard 태그."""
    shards = DATA_RELEASES[category]["shards"]
    try:
        code = int(stockCode)
    except ValueError:
        return shards[-1]["tag"]
    for shard in shards:
        if shard["min"] <= code <= shard["max"]:
            return shard["tag"]
    return shards[-1]["tag"]


def financeTag(stockCode: str) -> str:
    """종목코드 → 해당 finance shard 태그 (하위 호환)."""
    return shardTag(stockCode, "finance")


def shardAllTags(category: str) -> list[str]:
    """카테고리의 전체 shard 태그 목록."""
    return [s["tag"] for s in DATA_RELEASES[category]["shards"]]


def financeAllTags() -> list[str]:
    """finance 전체 shard 태그 목록 (하위 호환)."""
    return shardAllTags("finance")


def releaseBaseUrl(category: str = "docs", stockCode: str | None = None) -> str:
    conf = DATA_RELEASES[category]
    if "shards" in conf and stockCode:
        tag = shardTag(stockCode, category)
    elif "shards" in conf:
        tag = conf["shards"][0]["tag"]
    else:
        tag = conf["tag"]
    return f"{REPO_URL}/releases/download/{tag}"


def releaseApiUrl(category: str = "docs", tag: str | None = None) -> str:
    if tag is None:
        tag = DATA_RELEASES[category]["tag"]
    return f"https://api.github.com/repos/{REPO}/releases/tags/{tag}"
