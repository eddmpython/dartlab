"""Ollama 설치 감지 및 안내."""

from __future__ import annotations

import platform
import shutil
import subprocess

OLLAMA_DEFAULT_URL = "http://localhost:11434"


def _detect_gpu() -> dict:
    """GPU 상태 감지.

    Returns:
            {"available": bool, "name": str | None, "vram_mb": int | None}
    """
    gpu_info: dict = {"available": False, "name": None, "vram_mb": None}

    # nvidia-smi (NVIDIA GPU)
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            line = result.stdout.strip().split("\n")[0]
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2:
                gpu_info["available"] = True
                gpu_info["name"] = parts[0]
                try:
                    gpu_info["vram_mb"] = int(float(parts[1]))
                except (ValueError, IndexError):
                    pass
                return gpu_info
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    # macOS: system_profiler (Apple Silicon / AMD GPU)
    if platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and "Chipset Model" in result.stdout:
                for line in result.stdout.split("\n"):
                    if "Chipset Model" in line:
                        gpu_info["available"] = True
                        gpu_info["name"] = line.split(":")[-1].strip()
                        break
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass

    return gpu_info


def detect_ollama() -> dict:
    """Ollama 상태 종합 감지.

    Returns:
            {
                    "installed": bool,
                    "running": bool,
                    "models": ["llama3.1", ...],
                    "url": "http://localhost:11434",
                    "gpu": {"available": bool, "name": str | None, "vram_mb": int | None},
            }
    """
    import requests

    result: dict = {
        "installed": False,
        "running": False,
        "models": [],
        "url": OLLAMA_DEFAULT_URL,
        "gpu": _detect_gpu(),
    }

    try:
        resp = requests.get(f"{OLLAMA_DEFAULT_URL}/api/tags", timeout=2)
        if resp.status_code == 200:
            result["installed"] = True
            result["running"] = True
            data = resp.json()
            result["models"] = [m["name"] for m in data.get("models", [])]
            return result
    except (requests.ConnectionError, requests.Timeout):
        pass

    if shutil.which("ollama"):
        result["installed"] = True

    return result


def get_install_guide() -> str:
    """OS별 Ollama 설치 안내 텍스트."""
    os_name = platform.system()

    guide = "[ Ollama 설치 안내 ]\n\n"

    if os_name == "Windows":
        guide += (
            "1. https://ollama.com/download/windows 에서 설치파일 다운로드\n"
            "2. 설치 후 터미널에서: ollama serve\n"
            "3. 모델 다운로드: ollama pull llama3.1\n"
        )
    elif os_name == "Darwin":
        guide += (
            "1. brew install ollama\n"
            "   또는 https://ollama.com/download/mac 에서 다운로드\n"
            "2. 서버 시작: ollama serve\n"
            "3. 모델 다운로드: ollama pull llama3.1\n"
        )
    else:
        guide += (
            "1. curl -fsSL https://ollama.com/install.sh | sh\n"
            "2. 서버 시작: ollama serve\n"
            "3. 모델 다운로드: ollama pull llama3.1\n"
        )

    guide += "\n설치 완료 후 다시 시도하세요.\n문서: https://ollama.com/\n"
    return guide
