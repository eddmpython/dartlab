"""회사 카드(캐러셀) 이미지가 부실할 때 — 저작권 없는(CC0/Public-Domain) 사진을 받아 채운다.

## 어디서 가져오나 (출처 = 파이프라인 기록 — 둘 다 저작권 의무 0)
- **Wikimedia Commons** (`commons.wikimedia.org/w/api.php`) — 실사 피사체(정유탑·병입라인·
  선박엔진 등) 적중률이 가장 높은 PD/CC0 사진 저장소. LicenseShortName 이 `public domain`/`cc0`/
  `pd-*`/`no restrictions` 인 것만 채택(귀속 표기 불필요한 것만). **회사 hero 1차 스톡 소스**.
- **Openverse** (`api.openverse.org/v1/images/`) — WordPress 재단 CC0/PDM 검색 API. `license=cc0,pdm`
  로만 질의. 범용·분위기 컷 보조. (특정 회사 피사체 적중률은 Commons 보다 낮음.)
- 두 소스 모두 출처/제목/라이선스를 회사 폴더 `CREDITS.md` 에 기록(CC0/PD 는 의무 아니나 감사 추적).
- 회색조(흑백)는 카드 렌더(`CardSlide` CSS filter)가 입히므로 여기선 **컬러 원본** 그대로 저장한다.
- 카드 캐러셀 발간 이미지는 **CC0 스톡으로만** 수급한다 — 생성형(FLUX) 은 발간 카드에 쓰지 않는다(출처 깨끗한 실사로 통일).
  적중이 안 되면 다른 검색어로 재시도하고, 그래도 없으면 그 슬라이드는 이미지 없이 둔다.
- 검색어는 범용 업종어보다 **그 글의 회사명·상호, 사건명, 시설/도시명, 제품/공정명**을 앞에 둔다.
  회사명 직검색은 로고·광고·인물 오매치가 섞일 수 있으므로 `keywords` 와 눈검수로 걸러낸다.
  실제 상호가 보이는 PD/CC0 사진은 쓸 수 있지만, 카드 맥락과 무관한 로고 클로즈업은 폐기한다.

## 흐름 (회사 hero 이미지 파이프라인에 그대로 합류)
1. 이 도구가 `sns/assets/{code}/cc0-{name}.webp` 로 저장 (긴 변 1400·webp q82).
2. `sns/scripts/build_index.py` 가 자동으로 인덱싱(파일명에 card/thumbnail/og 토큰 없으면 hero 로 채택).
3. `sns/scripts/publish_assets_hf.py`가 중앙 catalog에 등록하고 hfMedia 객체와 companies manifest를 발행.
4. 블로그 frontmatter 슬라이드에서 `image: cc0-{name}` 로 가리킨다(resolveSlideImage prefix 매칭).

즉 **별도 배선 없음** — 기존 회사 이미지와 똑같은 길로 서빙된다. 차이는 출처(생성형 대신 CC0 스톡)뿐.

## 사용
    uv run python -X utf8 blog/_scripts/fetch_cc0_images.py --jobs sns/assets/_plans/cc0FetchJobs.json
    uv run python -X utf8 blog/_scripts/fetch_cc0_images.py --jobs ... --force   # 기존 cc0-*.webp 덮어쓰기

jobs JSON = 리스트, 각 항목:
    {"code": "000080", "name": "bottling-line",
     "queries": ["하이트진로 bottling plant", "brewery production line Seoul", "bottling plant"],
     "keywords": ["hite", "bottle", "brewery", "factory", "production"]}
  - code     = sns/assets/ 아래 폴더(보통 6자리 코드 또는 티커)
  - name     = 의미 이름(저장 파일 = cc0-{name}.webp, 슬라이드 image: 값과 동일)
  - queries  = 앞에서부터 시도할 검색어들. 회사/사건/시설/도시명 → 구체 공정 → 범용 업종 순으로 둔다.
  - keywords = 제목/태그에 하나라도 있어야 채택(회사명·시설명·핵심 피사체로 오매치 차단)
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS_ROOT = ROOT / "sns" / "assets"
OPENVERSE = "https://api.openverse.org/v1/images/"
OPENVERSE_TOKEN_URL = "https://api.openverse.org/v1/auth_tokens/token/"
COMMONS = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "dartlab-carousel/1.0 (license-clean CC0/PD image fetch)"}
LONG_EDGE = 1400  # 4:5 cover 에 충분, webp q82
_FREE_LICENSE_TOKENS = ("public domain", "cc0", "pd-", "no restrictions")  # 귀속 의무 없는 것만

# 정중한 요청 간격(429 회피) — Commons 무인증은 느슨, Openverse 는 토큰으로 여유.
_COMMONS_MIN_INTERVAL = 1.3
_OPENVERSE_MIN_INTERVAL = 0.4
_last_call: dict[str, float] = {"commons": 0.0, "openverse": 0.0}


def _throttle(which: str, interval: float) -> None:
    """직전 호출 후 interval 초가 지나도록 대기(API 정중성)."""
    dt = time.monotonic() - _last_call[which]
    if dt < interval:
        time.sleep(interval - dt)
    _last_call[which] = time.monotonic()


_OV_TOKEN: str | None = None
_OV_TOKEN_TRIED = False


def _env(key: str) -> str:
    """환경변수 우선, 없으면 repo 루트 .env 에서 key= 값 읽기."""
    val = os.environ.get(key)
    if val:
        return val.strip()
    envf = ROOT / ".env"
    if envf.exists():
        for line in envf.read_text(encoding="utf-8").splitlines():
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return ""


def _openverse_token() -> str | None:
    """OPENVERSE_CLIENT_ID/SECRET 로 bearer 토큰 1회 발급(레이트리밋 완화). 실패 시 무인증."""
    global _OV_TOKEN, _OV_TOKEN_TRIED
    if _OV_TOKEN_TRIED:
        return _OV_TOKEN
    _OV_TOKEN_TRIED = True
    cid, secret = _env("OPENVERSE_CLIENT_ID"), _env("OPENVERSE_CLIENT_SECRET")
    if not (cid and secret):
        return None
    try:
        resp = requests.post(
            OPENVERSE_TOKEN_URL,
            data={"client_id": cid, "client_secret": secret, "grant_type": "client_credentials"},
            headers=UA,
            timeout=25,
        )
        resp.raise_for_status()
        _OV_TOKEN = resp.json().get("access_token")
        sys.stderr.write("    openverse 인증 토큰 발급 — 레이트리밋 완화\n")
    except Exception as exc:
        sys.stderr.write(f"    openverse 토큰 발급 실패(무인증으로 진행): {exc}\n")
        _OV_TOKEN = None
    return _OV_TOKEN


def _relevant(item: dict, keywords: list[str]) -> bool:
    """제목/태그에 관련 키워드가 하나라도 있으면 채택(엉뚱한 사진 차단). keywords 비면 무조건 통과."""
    if not keywords:
        return True
    hay = (item.get("title") or "").lower()
    hay += " " + " ".join(t.get("name", "") for t in (item.get("tags") or [])).lower()
    return any(k.lower() in hay for k in keywords)


def _download(url: str) -> Image.Image | None:
    """URL 이미지 다운로드 — 200·최소크기(짧은 변 ≥600) 통과 시 RGB Image, 아니면 None."""
    try:
        resp = requests.get(url, headers=UA, timeout=30)
        if resp.status_code != 200 or len(resp.content) < 12000:
            return None
        im = Image.open(io.BytesIO(resp.content))
        im.load()
        if min(im.size) < 600:
            return None
        return im.convert("RGB")
    except Exception:
        return None


def _save_webp(im: Image.Image, dest: Path) -> int:
    """긴 변 LONG_EDGE 로 다운스케일 후 webp q82 저장 — 바이트 크기 반환."""
    w, h = im.size
    scale = min(1.0, LONG_EDGE / max(w, h))
    if scale < 1.0:
        im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "WEBP", quality=82, method=6)
    return dest.stat().st_size


def _search_openverse(query: str, n: int = 12) -> list[dict]:
    """Openverse CC0/PDM 검색 → 정규화 item 리스트(실패 시 빈 리스트)."""
    headers = dict(UA)
    token = _openverse_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(3):
        _throttle("openverse", _OPENVERSE_MIN_INTERVAL)
        try:
            resp = requests.get(
                OPENVERSE,
                params={"q": query, "license": "cc0,pdm", "page_size": n, "mature": "false"},
                headers=headers,
                timeout=25,
            )
            if resp.status_code == 429:
                time.sleep(4 * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp.json().get("results", [])
        except Exception as exc:
            sys.stderr.write(f"    openverse '{query}' 실패: {exc}\n")
            return []
    return []


def _strip_html(s: str) -> str:
    """Commons creator/title 의 HTML 태그 제거(간이)."""
    import re

    return re.sub(r"<[^>]+>", "", s or "").strip()


def _search_commons(query: str, n: int = 20) -> list[dict]:
    """Wikimedia Commons 사진 검색 → PD/CC0 만 골라 Openverse 와 동일 스키마로 정규화."""
    pages: dict = {}
    for attempt in range(3):
        _throttle("commons", _COMMONS_MIN_INTERVAL)
        try:
            resp = requests.get(
                COMMONS,
                params={
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": f"{query} filetype:bitmap",
                    "gsrnamespace": "6",
                    "gsrlimit": n,
                    "prop": "imageinfo",
                    "iiprop": "url|size|extmetadata",
                    "iiurlwidth": LONG_EDGE,
                },
                headers=UA,
                timeout=25,
            )
            if resp.status_code == 429:
                time.sleep(6 * (attempt + 1))  # Commons 백오프 — 6·12·18초
                continue
            resp.raise_for_status()
            pages = (resp.json().get("query", {}) or {}).get("pages", {}) or {}
            break
        except Exception as exc:
            sys.stderr.write(f"    commons '{query}' 실패: {exc}\n")
            return []
    if not pages:
        return []

    items = []
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {}) or {}
        lic = (meta.get("LicenseShortName", {}) or {}).get("value", "")
        if not any(tok in lic.lower() for tok in _FREE_LICENSE_TOKENS):
            continue  # 귀속 의무 있는 CC-BY/SA 등 제외 — "저작권없는" 만
        items.append(
            {
                "url": info.get("thumburl") or info.get("url", ""),
                "title": _strip_html((meta.get("ObjectName", {}) or {}).get("value", "")) or page.get("title", ""),
                "tags": [],
                "creator": _strip_html((meta.get("Artist", {}) or {}).get("value", "")) or "unknown",
                "license": lic,
                "license_version": "",
                "foreign_landing_url": info.get("descriptionurl", ""),
            }
        )
    return items


def _candidates(query: str) -> list[dict]:
    """Commons(실사 적중률 높음) 먼저, 그다음 Openverse — 둘 다 PD/CC0."""
    return _search_commons(query) + _search_openverse(query)


def _credit_line(name: str, query: str, item: dict) -> str:
    title = (item.get("title") or "(무제)").strip()
    creator = (item.get("creator") or "unknown").strip()
    lic = f"{item.get('license', '')} {item.get('license_version', '')}".strip()
    src = item.get("foreign_landing_url") or item.get("url")
    return f"- **cc0-{name}.webp** — {title} / {creator} / {lic} / [{query}] / {src}"


def run_job(job: dict, force: bool) -> tuple[str, str | None]:
    """한 회사 한 이미지 수급. (상태문자열, credit_line or None) 반환."""
    code = job["code"]
    name = job["name"]
    dest = ASSETS_ROOT / code / f"cc0-{name}.webp"
    if dest.exists() and not force:
        return (f"SKIP {code}/cc0-{name}.webp (이미 있음, --force 로 덮어쓰기)", None)

    for query in job.get("queries", []):
        for item in _candidates(query):
            if not _relevant(item, job.get("keywords", [])):
                continue
            im = _download(item.get("url", ""))
            if im is None:
                continue
            size = _save_webp(im, dest)
            lic = f"{item.get('license', '')} {item.get('license_version', '')}".strip()
            status = f"OK   {code}/cc0-{name}.webp ({size // 1024} KB) ← [{query}] {lic}"
            return (status, _credit_line(name, query, item))
    return (f"MISS {code}/cc0-{name} — 관련 PD/CC0 매치 없음", None)


def main() -> None:
    parser = argparse.ArgumentParser(description="CC0/PDM 회사 카드 이미지 수급 (Openverse)")
    parser.add_argument("--jobs", required=True, help="jobs JSON 경로")
    parser.add_argument("--force", action="store_true", help="기존 cc0-*.webp 덮어쓰기")
    args = parser.parse_args()

    jobs = json.loads(Path(args.jobs).read_text(encoding="utf-8"))
    credits_by_code: dict[str, list[str]] = {}
    n_ok = 0
    for job in jobs:
        status, credit = run_job(job, args.force)
        print(status)
        if credit:
            n_ok += 1
            credits_by_code.setdefault(job["code"], []).append(credit)

    # 회사별 CREDITS.md 누적(추가 모드 — 기존 출처 보존).
    for code, lines in credits_by_code.items():
        cred = ASSETS_ROOT / code / "CREDITS.md"
        header = "" if cred.exists() else "# 이미지 출처 (CC0 / Public Domain — Wikimedia Commons · Openverse)\n\n"
        with cred.open("a", encoding="utf-8") as fh:
            fh.write(header + "\n".join(lines) + "\n")

    print(f"\n→ {n_ok}장 수급. 다음: build_index.py → publish_assets_hf.py 로 hfMedia 게시.")


if __name__ == "__main__":
    main()
