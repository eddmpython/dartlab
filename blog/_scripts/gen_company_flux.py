"""회사 카드(캐러셀) hero 이미지가 부실할 때 — 주제에 정확히 맞는 이미지를 FLUX 로 생성한다.

## 왜 생성형인가 (CC0 스톡과의 분담)
- 회사 hero 는 "0.5초 안에 그 사업을 식별"시켜야 한다(소주 병입라인·정유 증류탑·선박 대형엔진 등).
  이런 **특정 피사체**는 CC0 스톡(`fetch_cc0_images.py` → Openverse)에서 적중률이 낮다 — 실측상
  6건 중 1건만 주제 일치. 그래서 특정 회사 hero 는 **FLUX 생성**이 1차, CC0 스톡은 보조(범용·분위기).
- FLUX(Replicate flux-1.1-pro)는 산출물 저작권이 깨끗(생성형 결과·로고/워터마크 금지 프롬프트)하다.
  비용은 사전충전. 회사 기존 hero 들도 이 경로로 만들어졌다(동일 파이프라인).

## 흐름 (회사 hero 이미지 파이프라인에 그대로 합류 — 별도 배선 없음)
1. 이 도구가 `sns/assets/{code}/{name}.webp` 로 저장 (4:5 portrait·webp q90).
2. `sns/scripts/build_index.py` 가 자동 인덱싱(hero).
3. `sns/scripts/publish_assets_hf.py`가 중앙 catalog에 등록하고 hfMedia 객체와 companies manifest를 발행.
4. 슬라이드에서 `image: {name}` 로 가리킨다.

## 사용
    uv run python -X utf8 blog/_scripts/gen_company_flux.py --jobs sns/assets/_plans/companyFluxJobs.json
    uv run python -X utf8 blog/_scripts/gen_company_flux.py --jobs ... --force   # 기존 파일 덮어쓰기

jobs JSON = 리스트, 각 항목: {"code": "010950", "name": "refinery-towers", "prompt": "..."}
  - code   = sns/assets/ 아래 폴더(6자리 코드 또는 티커)
  - name   = 의미 이름(저장 파일 = {name}.webp, 슬라이드 image: 값과 동일)
  - prompt = FLUX 프롬프트(영문 권장). "no text/logo/watermark" 는 자동 부착.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
ASSETS_ROOT = ROOT / "sns" / "assets"
API = "https://api.replicate.com/v1/predictions"
NO_TEXT = "no text, no logos, no watermark, no brand marks, no signage"
GAP_SECONDS = 12  # 분당 6건 rate-limit → 순차 12초 간격

load_dotenv(ROOT / ".env")
TOKEN = os.getenv("REPLICATE_API_TOKEN", "")
HEADERS = {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}


def _create(prompt: str) -> str:
    """FLUX 예측 생성 요청 — prediction id 반환. 4:5 portrait(캐러셀 카드 비율)."""
    payload = {
        "version": "black-forest-labs/flux-1.1-pro",
        "input": {
            "prompt": f"{prompt}, cinematic, photorealistic, {NO_TEXT}",
            "aspect_ratio": "4:5",
            "output_format": "webp",
            "output_quality": 90,
            "safety_tolerance": 2,
        },
    }
    r = requests.post(API, headers=HEADERS, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["id"]


def _poll(pid: str, timeout: int = 180) -> str:
    """완료까지 폴링 — 산출 이미지 URL 반환. 실패/타임아웃이면 예외."""
    url = f"{API}/{pid}"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        j = r.json()
        status = j.get("status")
        if status == "succeeded":
            out = j.get("output")
            return out[0] if isinstance(out, list) else out
        if status in ("failed", "canceled"):
            raise RuntimeError(f"FLUX {status}: {j.get('error')}")
        time.sleep(2)
    raise TimeoutError(f"FLUX poll timeout {pid}")


def _download(url: str, dest: Path) -> int:
    """이미지 다운로드 후 저장 — 바이트 크기 반환."""
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)
    return dest.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser(description="회사 카드 hero 이미지 FLUX 생성")
    parser.add_argument("--jobs", required=True, help="jobs JSON 경로")
    parser.add_argument("--force", action="store_true", help="기존 파일 덮어쓰기")
    args = parser.parse_args()

    if not TOKEN:
        sys.stderr.write("REPLICATE_API_TOKEN 없음 (.env 확인)\n")
        sys.exit(1)

    jobs = json.loads(Path(args.jobs).read_text(encoding="utf-8"))
    pending = []
    for job in jobs:
        dest = ASSETS_ROOT / job["code"] / f"{job['name']}.webp"
        if dest.exists() and not args.force:
            print(f"SKIP {job['code']}/{job['name']}.webp (이미 있음)")
            continue
        pending.append((job, dest))

    for i, (job, dest) in enumerate(pending):
        print(f"[{i + 1}/{len(pending)}] {job['code']}/{job['name']} 생성 중...")
        pid = _create(job["prompt"])
        img_url = _poll(pid)
        size = _download(img_url, dest)
        print(f"  -> {dest.relative_to(ROOT)} ({size // 1024} KB)")
        if i < len(pending) - 1:
            time.sleep(GAP_SECONDS)

    print(f"\n→ {len(pending)}장 생성. 다음: build_index.py → publish_assets_hf.py 로 hfMedia 게시.")


if __name__ == "__main__":
    main()
