"""dartlab pyodide wheel 빌드 + HF 업로드.

pyodide 전용 wheel: METADATA에서 Requires-Dist를 제거하여
micropip.install(URL) 한 줄로 설치 가능하게 한다.
PyPI wheel은 그대로 유지 (full deps).
"""

import subprocess
import sys
import zipfile
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


_PYODIDE_STRIP = {
    # server / AI / MCP: pyodide 불필요
    "fastapi",
    "uvicorn",
    "sse-starlette",
    "sse_starlette",
    "mcp",
    "qrcode",
    "plotly",
    "huggingface-hub",
    "huggingface_hub",
    "google-genai",
    "google_genai",
    "openai",
    "anthropic",
    # marimo(노트북 프레임워크): pyodide 데이터분석 wheel 에 불필요 + transitive msgspec(순수휠 없음)이
    # micropip.install(wheel) 을 깨뜨린다. dartlab core 는 marimo 를 lazy import 라 strip 안전.
    "marimo",
    # duckdb: C 확장(pyodide-repo 부재), scan 등 일부 경로만 lazy 사용. 노트북 예제 경로 미사용이라 strip.
    "duckdb",
}

# pyodide 빌트인이지만 버전 제약이 맞지 않는 패키지 → 버전 제거 후 유지
_PYODIDE_RELAX_VERSION = {"lxml", "polars", "numpy"}

# pyodide 빌트인인데 원본 deps에 없는 패키지 → 추가
_PYODIDE_ADD = ["pyarrow"]


def strip_deps(wheel_path: Path) -> Path:
    """wheel METADATA에서 pyodide 미지원 deps만 제거한 pyodide 전용 wheel 생성.

    httpx, lxml, beautifulsoup4, rich, pydantic, numpy 등
    pyodide 빌트인으로 설치 가능한 deps는 유지한다.
    """
    out_path = wheel_path.parent / wheel_path.name.replace(".whl", ".pyodide.whl")

    with zipfile.ZipFile(wheel_path, "r") as src, zipfile.ZipFile(out_path, "w") as dst:
        for item in src.infolist():
            data = src.read(item.filename)

            if item.filename.endswith("/METADATA"):
                text = data.decode("utf-8")
                lines = []
                strip_set = {s.lower().replace("-", "_") for s in _PYODIDE_STRIP}
                relax_set = {s.lower().replace("-", "_") for s in _PYODIDE_RELAX_VERSION}
                for line in text.splitlines():
                    if line.startswith("Requires-Dist:"):
                        raw = line.split(":")[1].strip()
                        pkg = raw.split(";")[0].split(">")[0].split("<")[0].split("=")[0].split("[")[0].strip()
                        pkg_norm = pkg.lower().replace("-", "_")
                        if pkg_norm in strip_set:
                            continue  # pyodide 미지원 — 제거
                        # 환경 마커 제거
                        if "; sys_platform" in line:
                            line = line.split(";")[0].strip()
                        # 버전 제약 완화 (pyodide 빌트인 버전과 충돌 방지)
                        if pkg_norm in relax_set:
                            line = f"Requires-Dist: {pkg}"
                    lines.append(line)
                # pyodide 전용 추가 deps
                for add_pkg in _PYODIDE_ADD:
                    lines.append(f"Requires-Dist: {add_pkg}")
                data = ("\n".join(lines) + "\n").encode("utf-8")

            if item.filename.endswith("/RECORD"):
                data = b""

            dst.writestr(item, data)

    print(f"pyodide wheel: {out_path.name} ({out_path.stat().st_size / 1024:.0f} KB)")
    return out_path


def upload_to_hf(wheel_path: Path, token: str | None = None) -> str:
    """wheel을 HF datasets에 업로드."""
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    # pyodide wheel은 원래 이름으로 업로드 (.pyodide 접미사 제거)
    repo_name = wheel_path.name.replace(".pyodide.whl", ".whl")
    url = api.upload_file(
        path_or_fileobj=str(wheel_path),
        path_in_repo=f"{HF_DIR}/{repo_name}",
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
    print(f"원본 wheel: {whl} ({whl.stat().st_size / 1024:.0f} KB)")

    # deps 제거한 pyodide 전용 wheel
    pyodide_whl = strip_deps(whl)

    # 로컬 복사
    import shutil

    local_copy = Path(__file__).parent / pyodide_whl.name
    shutil.copy2(pyodide_whl, local_copy)

    if args.upload:
        import os

        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
        token = args.token or os.environ.get("HF_TOKEN")
        if not token:
            print("⚠ HF_TOKEN 필요: --token 또는 환경변수", file=sys.stderr)
            sys.exit(1)
        upload_to_hf(pyodide_whl, token)


if __name__ == "__main__":
    main()
