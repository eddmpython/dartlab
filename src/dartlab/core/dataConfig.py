"""데이터 릴리즈 중앙 설정.

디렉토리, 라벨을 1곳에서 관리.
새 카테고리 추가 시 DATA_RELEASES에 한 줄만 추가하면 전체 반영.

모든 데이터는 HuggingFace 데이터셋(eddmpython/dartlab-data)에서 제공.
"""

HF_REPO = "eddmpython/dartlab-data"
HF_BASE_URL = f"https://huggingface.co/datasets/{HF_REPO}/resolve/main"

DATA_RELEASES: dict[str, dict] = {
    "docs": {
        "dir": "dart/docs",
        "label": "DART 공시 문서 데이터",
    },
    "finance": {
        "dir": "dart/finance",
        "label": "재무 숫자 데이터",
    },
    "report": {
        "dir": "dart/report",
        "label": "정기보고서 데이터",
    },
    "scan": {
        "dir": "dart/scan",
        "label": "전종목 횡단분석 프리빌드 데이터",
    },
    "edgarDocs": {
        "dir": "edgar/docs",
        "label": "SEC EDGAR 공시 문서 데이터",
    },
    "edgar": {
        "dir": "edgar/finance",
        "label": "SEC EDGAR 재무 데이터",
    },
    "allFilings": {
        "dir": "dart/allFilings",
        "label": "DART 전체 공시 원문 데이터",
    },
    "edinetDocs": {
        "dir": "edinet/docs",
        "label": "EDINET 공시 문서 데이터 (일본)",
    },
    "edinet": {
        "dir": "edinet/finance",
        "label": "EDINET 재무 데이터 (일본)",
    },
}


def hfBaseUrl(category: str = "docs") -> str:
    """HuggingFace 데이터셋 base URL."""
    dirPath = DATA_RELEASES[category]["dir"]
    return f"{HF_BASE_URL}/{dirPath}"
