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
    model: latest             # 기본 모델 (provider 최신값 사용)
    verbose: false
    data_dir: /my/data
"""

import os
import sys
from pathlib import Path

verbose: bool = True
askLog: bool = False


def _userCacheDir() -> Path:
    """플랫폼별 사용자 캐시 디렉터리 (쓰기 가능) — pip 설치 사용자의 데이터 저장 위치.

    Windows %LOCALAPPDATA% / macOS ~/Library/Caches / 기타 $XDG_CACHE_HOME(또는 ~/.cache)
    아래 ``dartlab/``. platformdirs 의존 없이 stdlib 만으로 관례 경로 해석.
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "dartlab" / "Cache"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "dartlab"
    return Path(os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")) / "dartlab"


def _resolveDefaultDataDir() -> str:
    """기본 데이터 디렉터리 — dev 체크아웃은 repo ``data/``, pip 설치형은 사용자 캐시.

    repo ``data/`` 기본값은 site-packages 설치 사용자에겐 쓰기 불가(부모가 readonly)라 깨진다.
    dev 소스 트리(repo ``data/`` 또는 ``pyproject.toml`` 존재)는 기존 동작 그대로 repo ``data/`` 를
    쓰고, 설치형만 ``~/.cache/dartlab`` 류 쓰기 가능 경로로 fallback. env/.dartlab.yml 우선은 불변.
    """
    # pyodide(브라우저 WASM)는 pyproject.toml 이 없어 사용자 캐시(/home/pyodide/.cache)로 빠지는데,
    # 데이터 프리페치(loader/prefetch)는 /data 에 쓴다. 노트북에서 DARTLAB_DATA_DIR 를 손으로 안 잡아도
    # 되게 pyodide 는 /data 로 고정(loadDataPyodide 하드코딩·prefetch 와 일치).
    if sys.platform == "emscripten":
        return "/data"
    # dev/CI 소스 트리는 repo ``data/``. 고정 깊이(parents[2]) 대신 ``__file__`` 상위와 실행 CWD
    # 양쪽에서 ``pyproject.toml`` 을 거슬러 찾는다(editable·copied 설치·CWD=repo 모두 견고; 옛 고정
    # 깊이는 copied 설치 시 repo 를 놓쳐 사용자 캐시로 잘못 빠졌다). 어디서도 못 찾으면 설치형으로
    # 보고 쓰기 가능한 사용자 캐시로 fallback.
    for start in (Path(__file__).resolve().parent, Path.cwd()):
        cur = start.resolve()
        while True:
            if (cur / "pyproject.toml").exists():
                return str(cur / "data")
            if cur == cur.parent:
                break
            cur = cur.parent
    return str(_userCacheDir())


_DEFAULT_DATA_DIR = Path(_resolveDefaultDataDir())

dataDir: str = os.environ.get("DARTLAB_DATA_DIR") or str(_DEFAULT_DATA_DIR)

# ── 프로젝트 설정 ──

_projectConfig: dict | None = None


def _findConfigFile() -> Path | None:
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


def loadProjectConfig() -> dict:
    """프로젝트 설정 로드 (1회만, 이후 캐싱)."""
    global _projectConfig
    if _projectConfig is not None:
        return _projectConfig

    config_path = _findConfigFile()
    if config_path is None:
        _projectConfig = {}
        return _projectConfig

    try:
        import yaml  # type: ignore[import-untyped]

        with open(config_path, encoding="utf-8") as f:
            _projectConfig = yaml.safe_load(f) or {}
    except ImportError:
        # PyYAML 없으면 빈 설정
        _projectConfig = {}
    except (OSError, ValueError):
        _projectConfig = {}

    # 설정 반영
    if _projectConfig.get("verbose") is not None:
        global verbose
        verbose = bool(_projectConfig["verbose"])
    if _projectConfig.get("data_dir"):
        global dataDir
        dataDir = str(_projectConfig["data_dir"])

    return _projectConfig


def getDefaultCompany() -> str | None:
    """프로젝트 설정의 기본 종목."""
    cfg = loadProjectConfig()
    return cfg.get("company")


def getDefaultProvider() -> str | None:
    """프로젝트 설정의 기본 provider."""
    cfg = loadProjectConfig()
    return cfg.get("provider")


def getDefaultModel() -> str | None:
    """프로젝트 설정의 기본 model."""
    cfg = loadProjectConfig()
    return cfg.get("model")
