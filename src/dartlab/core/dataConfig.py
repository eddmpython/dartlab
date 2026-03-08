"""데이터 릴리즈 중앙 설정.

태그명, 디렉토리, 라벨을 1곳에서 관리.
새 카테고리 추가 시 DATA_RELEASES에 한 줄만 추가하면 전체 반영.
"""

REPO = "eddmpython/dartlab"
REPO_URL = f"https://github.com/{REPO}"

DATA_RELEASES: dict[str, dict[str, str]] = {
    "docs": {
        "tag": "data-docs",
        "dir": "docsData",
        "label": "DART 공시 문서 데이터",
    },
    "finance": {
        "tag": "data-finance",
        "dir": "financeData",
        "label": "재무 숫자 데이터",
    },
}


def releaseBaseUrl(category: str = "docs") -> str:
    tag = DATA_RELEASES[category]["tag"]
    return f"{REPO_URL}/releases/download/{tag}"


def releaseApiUrl(category: str = "docs") -> str:
    tag = DATA_RELEASES[category]["tag"]
    return f"https://api.github.com/repos/{REPO}/releases/tags/{tag}"
