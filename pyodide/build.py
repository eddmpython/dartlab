"""dartlab pyodide wheel 빌드 + HF 업로드.

옛날엔 METADATA 에서 Requires-Dist 를 손으로 잘라낸 별도 pyodide wheel 을 만들었다. 이제는
``pyproject.toml`` 의존성이 ``sys_platform != 'emscripten'`` 마커로 pyodide 비호환 dep(marimo·
duckdb·fastapi·openai·mcp·plotly 등)을 이미 배제한다. micropip 이 emscripten 환경에서 마커를
평가해 그 dep 들을 자동으로 건너뛰고, 남은 C 확장(polars·pyarrow·lxml·numpy)은 pyodide lockfile
에서 자동 로드한다. 그래서 별도 strip 수술이 불필요하고, PyPI 와 동일한 plain wheel 하나를 그대로
HF 에 올리면 ``micropip.install(wheel)`` 한 줄로 브라우저 설치가 끝난다.

새 pyodide 비호환 dep 은 ``pyproject.toml`` 에서 ``sys_platform != 'emscripten'`` 마커를 붙이면
된다(그게 유일 SSOT). tests/audit 의 wheel 마커 게이트가 빌드 시 검증한다.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
HF_REPO = "eddmpython/dartlab-data"
HF_DIR = "pyodide"


def build_wheel() -> Path:
    """uv build --wheel → dist/*.whl 경로 반환."""
    subprocess.run(["uv", "build", "--wheel"], cwd=ROOT, check=True)
    wheels = sorted(DIST.glob("dartlab-*.whl"), key=lambda p: p.stat().st_mtime)
    if not wheels:
        raise FileNotFoundError("빌드된 wheel 없음")
    return wheels[-1]


def upload_to_hf(wheel_path: Path, token: str | None = None) -> str:
    """plain wheel 을 HF datasets 의 pyodide/ 로 업로드."""
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    url = api.upload_file(
        path_or_fileobj=str(wheel_path),
        path_in_repo=f"{HF_DIR}/{wheel_path.name}",
        repo_id=HF_REPO,
        repo_type="dataset",
    )
    print(f"업로드 완료: {url}")
    return url


def main():
    import argparse

    parser = argparse.ArgumentParser(description="dartlab pyodide wheel 빌드/업로드")
    parser.add_argument("--upload", action="store_true", help="HF에 업로드")
    parser.add_argument("--token", help="HF 토큰 (없으면 환경변수 HF_TOKEN)")
    args = parser.parse_args()

    whl = build_wheel()
    print(f"wheel: {whl} ({whl.stat().st_size / 1024:.0f} KB)")

    if args.upload:
        import os

        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
        token = args.token or os.environ.get("HF_TOKEN")
        if not token:
            print("⚠ HF_TOKEN 필요: --token 또는 환경변수", file=sys.stderr)
            sys.exit(1)
        upload_to_hf(whl, token)


if __name__ == "__main__":
    main()
