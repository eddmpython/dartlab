"""dartlab 전역 설정.

사용법::

    import dartlab
    dartlab.verbose = False   # 진행 표시 끄기
    dartlab.dataDir = "/my/data"  # 데이터 저장 경로 변경

환경변수::

    DARTLAB_DATA_DIR=/my/data    # 데이터 저장 경로

프로젝트 설정 (.dartlab.yml)::

    # .dartlab.yml — cwd → parent → home 순으로 탐색
    company: 005930           # 기본 종목
    provider: openai          # 기본 LLM provider
    model: gpt-4o             # 기본 모델
    verbose: false
    data_dir: /my/data
"""

import os
from pathlib import Path

verbose: bool = True

_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"

dataDir: str = os.environ.get("DARTLAB_DATA_DIR", str(_DEFAULT_DATA_DIR))

# ── 프로젝트 설정 ──

_project_config: dict | None = None


def _find_config_file() -> Path | None:
    """cwd → parent → home 순으로 .dartlab.yml 탐색."""
    candidates = []
    cwd = Path.cwd()
    # cwd → parents
    for d in [cwd, *cwd.parents]:
        candidates.append(d / ".dartlab.yml")
        candidates.append(d / ".dartlab.yaml")
        if d == d.parent:
            break
    # home
    home = Path.home()
    candidates.append(home / ".dartlab.yml")
    candidates.append(home / ".dartlab.yaml")

    for p in candidates:
        if p.is_file():
            return p
    return None


def load_project_config() -> dict:
    """프로젝트 설정 로드 (1회만, 이후 캐싱)."""
    global _project_config
    if _project_config is not None:
        return _project_config

    config_path = _find_config_file()
    if config_path is None:
        _project_config = {}
        return _project_config

    try:
        import yaml  # type: ignore[import-untyped]

        with open(config_path, encoding="utf-8") as f:
            _project_config = yaml.safe_load(f) or {}
    except ImportError:
        # PyYAML 없으면 빈 설정
        _project_config = {}
    except (OSError, ValueError):
        _project_config = {}

    # 설정 반영
    if _project_config.get("verbose") is not None:
        global verbose
        verbose = bool(_project_config["verbose"])
    if _project_config.get("data_dir"):
        global dataDir
        dataDir = str(_project_config["data_dir"])

    return _project_config


def get_default_company() -> str | None:
    """프로젝트 설정의 기본 종목."""
    cfg = load_project_config()
    return cfg.get("company")


def get_default_provider() -> str | None:
    """프로젝트 설정의 기본 provider."""
    cfg = load_project_config()
    return cfg.get("provider")


def get_default_model() -> str | None:
    """프로젝트 설정의 기본 model."""
    cfg = load_project_config()
    return cfg.get("model")
