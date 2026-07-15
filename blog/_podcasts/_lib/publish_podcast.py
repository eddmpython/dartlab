"""DartLab 팟캐스트 발행자 (R2 SSOT).

운영자가 NotebookLM 에서 내려받은 m4a 를 넘기면, 이 스크립트가:
  1. m4a -> mp3 전사 (Spotify 는 RSS 로 m4a/AAC 를 임포트하지 않으므로 mp3 필수)
  2. 길이(ffprobe) + 바이트(os.stat) 측정
  3. guid mint-once (published.json 에 기록, 재발행 시 재사용, 구독자 중복 방지)
  4. 오디오 + 쇼커버 + 에피소드 커버 + 정적 영상을 R2(dartlab-podcast) 로 업로드
  5. 재사용 원본 이미지는 HF media repo 로 업로드
  6. 모든 발행 에피소드로 index.json(프론트 크로스링크) + feed.xml(RSS) 재생성 후 업로드
  7. 에피소드 URL / 피드 URL 출력

사용:
    uv run python -X utf8 blog/_podcasts/_lib/publish_podcast.py \
        --episode P01-dartlab-2700-filings \
        --audio "C:/Users/MSI/Downloads/2700개기업공시를한줄로통합하는dartlab.m4a"

    # 오디오 재업로드 없이 feed/index 만 재생성
    uv run python -X utf8 blog/_podcasts/_lib/publish_podcast.py --rebuild-only

    # 업로드 없이 로컬 검증
    uv run python -X utf8 blog/_podcasts/_lib/publish_podcast.py --episode ... --audio ... --dry-run

레포에는 텍스트와 작은 이미지 소스만 커밋된다(episode.yaml, published.json, script.md, cover/static 소스).
오디오 mp3/m4a 는 R2 런타임 산출물이라 레포에 두지 않는다(용량 격리).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

import yaml
from PIL import Image

from dartlab.core.dataConfig import HF_MEDIA_BASE_URL, HF_MEDIA_REPO

LIB_DIR = Path(__file__).resolve().parent
PODCAST_DIR = LIB_DIR.parent
ROOT = PODCAST_DIR.parents[1]
EPISODES_DIR = PODCAST_DIR / "episodes"
CHANNEL_YAML = PODCAST_DIR / "channel.yaml"
UPLOADS_DIR = PODCAST_DIR / "_uploads"

KST = timezone(timedelta(hours=9))
ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"
ATOM_NS = "http://www.w3.org/2005/Atom"

NODE = shutil.which("node")
FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")
WRANGLER_JS = ROOT / "infra" / "workers" / "pushHub" / "node_modules" / "wrangler" / "bin" / "wrangler.js"
SOURCE_ASSET_PREFIX = "podcasts"


# --- 환경 ---


def load_env() -> dict[str, str]:
    """레포 루트 .env 에서 Cloudflare 자격증명을 읽어 subprocess 용 env dict 반환."""
    import os

    env = dict(os.environ)
    dotenv = ROOT / ".env"
    if dotenv.exists():
        for line in dotenv.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            env[key.strip()] = val.strip().strip('"').strip("'")
    env["CI"] = "1"
    missing = [k for k in ("CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID") if not env.get(k)]
    if missing:
        raise SystemExit(f"[publish] .env 에 필요한 키 없음: {', '.join(missing)}")
    return env


# --- R2 업로드 ---


def r2_put(
    env: dict[str, str], bucket: str, key: str, local_path: Path, content_type: str, cache_control: str | None = None
) -> None:
    """node + wrangler 로 R2 객체 업로드 (원격)."""
    if NODE is None or not WRANGLER_JS.exists():
        raise SystemExit("[publish] node 또는 wrangler.js 를 찾을 수 없음 (infra/workers/pushHub 확인).")
    cmd = [
        NODE,
        str(WRANGLER_JS),
        "r2",
        "object",
        "put",
        "--remote",
        f"{bucket}/{key}",
        "--file",
        str(local_path),
        "--content-type",
        content_type,
    ]
    if cache_control:
        cmd += ["--cache-control", cache_control]
    print(f"  R2 put  {key}  ({local_path.stat().st_size:,} B, {content_type})")
    subprocess.run(cmd, cwd=str(ROOT), env=env, check=True, stdout=subprocess.DEVNULL)


# --- 오디오 ---


def transcode_to_mp3(src: Path, out_mp3: Path) -> None:
    """m4a/기타 -> mp3 128k 44.1k, 시크 안전 xing 헤더, id3v2.3."""
    if FFMPEG is None:
        raise SystemExit("[publish] ffmpeg 없음.")
    cmd = [
        FFMPEG,
        "-y",
        "-i",
        str(src),
        "-vn",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "128k",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-write_xing",
        "1",
        "-id3v2_version",
        "3",
        str(out_mp3),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def probe_duration_sec(path: Path) -> int:
    """ffprobe 로 초 단위 길이(반올림) 반환."""
    if FFPROBE is None:
        raise SystemExit("[publish] ffprobe 없음.")
    out = subprocess.run(
        [
            FFPROBE,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return int(round(float(out.stdout.strip())))


def fmt_hhmmss(sec: int) -> str:
    """초 -> HH:MM:SS."""
    h, rem = divmod(int(sec), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def sha8(path: Path) -> str:
    """파일 SHA256 앞 8 hex."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:8]


def camel_upload_slug(raw: str) -> str:
    """topicSlug/slug 를 팟빵용 영문 camelCase 파일명 조각으로 변환."""
    import re

    parts = [p for p in re.split(r"[^0-9A-Za-z]+", raw) if p]
    if not parts:
        return "episode"
    first = parts[0][:1].lower() + parts[0][1:]
    rest = [p[:1].upper() + p[1:] for p in parts[1:]]
    return "".join([first, *rest])


# --- 커버 ---


def normalize_cover(src: Path, out_jpg: Path, size: int = 3000, max_bytes: int = 500_000) -> None:
    """커버를 정사각 RGB JPEG(<max_bytes) 로 정규화."""
    im = Image.open(src).convert("RGB")
    w, h = im.size
    s = min(w, h)
    left, top = (w - s) // 2, (h - s) // 2
    im = im.crop((left, top, left + s, top + s))
    target = min(size, max(s, 1400))
    while target >= 1400:
        resized = im.resize((target, target), Image.LANCZOS)
        q = 90
        while q >= 35:
            resized.save(out_jpg, "JPEG", quality=q, optimize=True)
            if out_jpg.stat().st_size <= max_bytes:
                return
            q -= 5
        if target == 1400:
            break
        target = max(1400, int(target * 0.85))
    raise SystemExit(f"[cover] 500KB 이하 JPEG 정규화 실패: {src}")


def normalize_thumbnail(
    src: Path, out_jpg: Path, width: int = 1280, height: int = 720, max_bytes: int = 500_000
) -> None:
    """썸네일을 16:9 RGB JPEG(<max_bytes) 로 정규화."""
    im = Image.open(src).convert("RGB")
    w, h = im.size
    target_ratio = width / height
    current_ratio = w / h
    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        im = im.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        im = im.crop((0, top, w, top + new_h))
    resized = im.resize((width, height), Image.LANCZOS)
    q = 90
    while q >= 35:
        resized.save(out_jpg, "JPEG", quality=q, optimize=True)
        if out_jpg.stat().st_size <= max_bytes:
            return
        q -= 5
    raise SystemExit(f"[thumbnail] 500KB 이하 JPEG 정규화 실패: {src}")


# --- 로드/저장 ---


def load_yaml(path: Path) -> dict:
    """YAML 파일 로드."""
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_channel() -> dict:
    """channel.yaml 의 channel/r2/cover 병합 dict 반환."""
    return load_yaml(CHANNEL_YAML)


def episode_dirs(only: str | None) -> list[Path]:
    """발행 대상 에피소드 폴더 목록."""
    if only:
        d = EPISODES_DIR / only
        if not d.exists():
            raise SystemExit(f"[publish] 에피소드 폴더 없음: {d}")
        return [d]
    return sorted(p for p in EPISODES_DIR.iterdir() if p.is_dir() and (p / "episode.yaml").exists())


def resolve_episode_image_source(ep_dir: Path, source: str) -> Path:
    """episode.yaml image.source 를 에피소드 폴더 우선으로 해석."""
    src = Path(source)
    if src.is_absolute():
        return src
    ep_candidate = ep_dir / src
    if ep_candidate.exists():
        return ep_candidate
    return PODCAST_DIR / src


def resolve_audio_source(raw: str) -> Path:
    """episode.yaml audio.sourceHint 또는 --audio 값을 실제 파일 경로로 해석."""
    src = Path(raw)
    if src.is_absolute():
        return src
    cand = ROOT / src
    if cand.exists():
        return cand
    return Path.home() / src


def source_asset_key(meta: dict, source_path: Path) -> str:
    """HF media repo 에 올릴 원본 이미지 콘텐츠해시 경로."""
    suffix = source_path.suffix.lower() or ".bin"
    stem = source_path.stem.replace(" ", "-")
    return f"{SOURCE_ASSET_PREFIX}/{meta['slug']}/{stem}.{sha8(source_path)}{suffix}"


def source_asset_fields(ep_dir: Path, meta: dict) -> tuple[list[dict], list[dict]]:
    """재사용 원본 이미지 공개 필드와 내부 업로드 필드."""
    raw_assets = meta.get("sourceAssets") or []
    if isinstance(raw_assets, dict):
        raw_assets = [raw_assets]
    public_assets: list[dict] = []
    upload_assets: list[dict] = []
    code = str(meta.get("stockCode") or "").strip()
    for raw in raw_assets:
        if not isinstance(raw, dict):
            continue
        # 공유 풀 참조(한 세트): 회사 에피소드는 companies/{code} 풀 자산을 재사용한다. 재업로드하지 않고 이름으로 기록(프론트가 companies/index.json 으로 해석). 명시 key 있으면 URL 도 기록.
        if str(raw.get("pool") or "").strip() == "companyAsset" and code:
            pool_name = str(raw.get("name") or Path(str(raw.get("source") or "")).stem).strip()
            if not pool_name:
                continue
            entry = {
                "name": pool_name,
                "role": str(raw.get("role") or "source").strip(),
                "pool": "companyAsset",
                "code": code,
            }
            explicit_key = str(raw.get("key") or "").strip()
            if explicit_key:
                entry["key"] = explicit_key
                entry["url"] = f"{HF_MEDIA_BASE_URL.rstrip('/')}/{explicit_key}"
            public_assets.append(entry)
            continue
        source = str(raw.get("source") or "").strip()
        if not source:
            continue
        src = resolve_episode_image_source(ep_dir, source)
        key = str(raw.get("key") or "").strip()
        if not key and src.exists():
            key = source_asset_key(meta, src)
        elif not key:
            key = f"{SOURCE_ASSET_PREFIX}/{meta['slug']}/{src.name}"
        role = str(raw.get("role") or "source").strip()
        name = str(raw.get("name") or src.stem).strip()
        public_assets.append(
            {
                "name": name,
                "role": role,
                "key": key,
                "url": f"{HF_MEDIA_BASE_URL.rstrip('/')}/{key}",
            }
        )
        upload_assets.append({"sourcePath": str(src), "key": key, "name": name, "role": role})
    return public_assets, upload_assets


def episode_caption(meta: dict) -> str:
    """플랫폼 본문/설명용 캡션. 이미지는 짧게, 맥락은 이 필드로 분리한다."""
    raw = meta.get("caption") or {}
    if isinstance(raw, str):
        return raw.strip()
    if not isinstance(raw, dict):
        return ""
    parts: list[str] = []
    for key in ("hook", "body", "cta"):
        val = str(raw.get(key) or "").strip()
        if val:
            parts.append(val)
    tags = raw.get("hashtags") or []
    if isinstance(tags, list):
        cleaned = [str(tag).strip() for tag in tags if str(tag).strip()]
        if cleaned:
            parts.append(" ".join(cleaned))
    return "\n\n".join(parts).strip()


def episode_image_fields(channel: dict, ep_dir: Path, meta: dict) -> dict:
    """에피소드별 커버와 썸네일의 공개 URL, 내부 업로드 소스 필드."""
    base = channel["r2"]["baseUrl"].rstrip("/")
    image = meta.get("image") or {}
    source = str(image.get("source") or "").strip()
    key = str(image.get("key") or "").strip()
    if source and not key:
        key = f"episodes/{meta['slug']}/cover-3000.jpg"

    static_image = meta.get("staticImage") or meta.get("thumbnail") or {}
    static_source = str(static_image.get("source") or "").strip()
    static_key = str(static_image.get("key") or "").strip()
    if static_source and not static_key:
        static_key = f"episodes/{meta['slug']}/static-video.jpg"

    thumbnail = meta.get("thumbnail") or {}
    thumb_source = str(thumbnail.get("source") or "").strip()
    thumb_key = str(thumbnail.get("key") or "").strip()
    if thumb_source and not thumb_key:
        thumb_key = f"episodes/{meta['slug']}/thumbnail.jpg"
    if not thumb_source and static_source:
        thumb_source = static_source
    if not thumb_key and static_key:
        thumb_key = static_key

    public_sources, upload_sources = source_asset_fields(ep_dir, meta)

    fields = {
        "imageKey": key,
        "imageUrl": f"{base}/{key}" if key else "",
        "staticImageKey": static_key,
        "staticImageUrl": f"{base}/{static_key}" if static_key else "",
        "thumbnailKey": thumb_key,
        "thumbnailUrl": f"{base}/{thumb_key}" if thumb_key else "",
        "sourceAssets": public_sources,
    }
    if source:
        fields["_imageSource"] = str(resolve_episode_image_source(ep_dir, source))
        fields["_imageKey"] = key
    if static_source:
        fields["_staticImageSource"] = str(resolve_episode_image_source(ep_dir, static_source))
        fields["_staticImageKey"] = static_key
    if thumb_source:
        fields["_thumbnailSource"] = str(resolve_episode_image_source(ep_dir, thumb_source))
        fields["_thumbnailKey"] = thumb_key
    if upload_sources:
        fields["_sourceAssetUploads"] = upload_sources
    return fields


def published_record(channel: dict, ep_dir: Path, meta: dict, pub: dict) -> dict:
    """episode.yaml + published.json 을 index/feed 용 레코드로 변환."""
    record = {
        "slug": meta["slug"],
        "episodeId": meta["episodeId"],
        "episodeNo": int(meta["episodeNo"]),
        "title": meta["title"],
        "summary": " ".join((meta.get("summary") or "").split()),
        "caption": episode_caption(meta),
        "audioKey": pub["audioKey"],
        "mp3Bytes": pub["mp3Bytes"],
        "durationSec": pub["durationSec"],
        "guid": pub["guid"],
        "publishedAt": pub["publishedAt"],
        "stockCode": meta.get("stockCode", ""),
        "topicSlug": meta.get("topicSlug", ""),
        "cardType": meta.get("cardType", "meta"),
        "youtubeId": str(meta.get("youtubeId") or "").strip(),
        "links": meta.get("links", {"blogSlug": "", "cardSlug": "", "terminalCode": ""}),
    }
    record.update(episode_image_fields(channel, ep_dir, meta))
    return record


# --- feed / index ---


def build_index(channel: dict, records: list[dict]) -> str:
    """프론트 크로스링크 레지스트리 index.json 문자열."""
    base = channel["r2"]["baseUrl"].rstrip("/")
    eps = []
    for r in sorted(records, key=lambda x: x["episodeNo"], reverse=True):
        fallback_image = f"{base}/{channel['cover']['key']}"
        image_url = r.get("imageUrl") or fallback_image
        static_url = r.get("staticImageUrl") or r.get("thumbnailUrl") or image_url
        thumbnail_url = r.get("thumbnailUrl") or static_url
        eps.append(
            {
                "slug": r["slug"],
                "episodeId": r["episodeId"],
                "episodeNo": r["episodeNo"],
                "date": r["publishedAt"][:10],
                "title": r["title"],
                "audioUrl": f"{base}/{r['audioKey']}",
                "imageUrl": image_url,
                "staticImageUrl": static_url,
                "thumbnailUrl": thumbnail_url,
                "sourceAssets": r.get("sourceAssets") or [],
                "durationSec": r["durationSec"],
                "guid": r["guid"],
                "stockCode": r.get("stockCode", ""),
                "topicSlug": r.get("topicSlug", ""),
                "cardType": r.get("cardType", "meta"),
                "youtubeId": r.get("youtubeId", ""),
                "summary": r.get("summary", ""),
                "caption": r.get("caption", ""),
                "links": r.get("links", {"blogSlug": "", "cardSlug": "", "terminalCode": ""}),
            }
        )
    return (
        json.dumps(
            {"version": 1, "channel": channel["channel"]["title"], "episodes": eps}, ensure_ascii=False, indent=2
        )
        + "\n"
    )


def item_link(channel: dict, r: dict) -> str:
    """RSS item link. 회사 에피소드는 터미널 딥링크, 아니면 채널 링크."""
    link = channel["channel"]["link"].rstrip("/")
    code = r.get("stockCode", "")
    if code:
        return f"{link}/terminal?sym={code}"
    return link


def build_feed(channel: dict, records: list[dict]) -> str:
    """RSS 2.0 + iTunes feed.xml 문자열. records 는 발행된 에피소드."""
    ch = channel["channel"]
    r2 = channel["r2"]
    base = r2["baseUrl"].rstrip("/")
    cover_url = f"{base}/{channel['cover']['key']}"
    desc = " ".join(ch["description"].split())

    lines: list[str] = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(f'<rss version="2.0" xmlns:itunes="{ITUNES_NS}" xmlns:content="{CONTENT_NS}" xmlns:atom="{ATOM_NS}">')
    lines.append("  <channel>")
    lines.append(f"    <title>{xml_escape(ch['title'])}</title>")
    lines.append(f"    <link>{xml_escape(ch['link'])}</link>")
    lines.append(f"    <language>{xml_escape(ch['language'])}</language>")
    lines.append(f"    <description>{xml_escape(desc)}</description>")
    lines.append(f"    <copyright>{xml_escape(ch['copyright'])}</copyright>")
    lines.append(f"    <itunes:author>{xml_escape(ch['author'])}</itunes:author>")
    lines.append(f"    <itunes:summary>{xml_escape(desc)}</itunes:summary>")
    lines.append("    <itunes:owner>")
    lines.append(f"      <itunes:name>{xml_escape(ch['ownerName'])}</itunes:name>")
    lines.append(f"      <itunes:email>{xml_escape(ch['ownerEmail'])}</itunes:email>")
    lines.append("    </itunes:owner>")
    lines.append(f'    <itunes:image href="{xml_escape(cover_url)}"/>')
    lines.append(f'    <itunes:category text="{xml_escape(ch["category"])}">')
    lines.append(f'      <itunes:category text="{xml_escape(ch["subCategory"])}"/>')
    lines.append("    </itunes:category>")
    lines.append(f"    <itunes:explicit>{'true' if ch.get('explicit') else 'false'}</itunes:explicit>")
    lines.append(f"    <itunes:type>{xml_escape(ch.get('type', 'episodic'))}</itunes:type>")
    lines.append(f'    <atom:link href="{xml_escape(base + "/feed.xml")}" rel="self" type="application/rss+xml"/>')

    for r in sorted(records, key=lambda x: x["publishedAt"], reverse=True):
        pub_dt = datetime.fromisoformat(r["publishedAt"])
        audio_url = f"{base}/{r['audioKey']}"
        image_url = r.get("imageUrl") or cover_url
        summary = r.get("summary", "")
        lines.append("    <item>")
        lines.append(f"      <title>{xml_escape(r['title'])}</title>")
        lines.append(f"      <link>{xml_escape(item_link(channel, r))}</link>")
        lines.append(f"      <itunes:episode>{r['episodeNo']}</itunes:episode>")
        lines.append(f'      <guid isPermaLink="false">{xml_escape(r["guid"])}</guid>')
        lines.append(f"      <pubDate>{format_datetime(pub_dt)}</pubDate>")
        lines.append(f"      <description><![CDATA[{summary}]]></description>")
        lines.append(f"      <itunes:summary>{xml_escape(summary)}</itunes:summary>")
        lines.append(f"      <itunes:duration>{fmt_hhmmss(r['durationSec'])}</itunes:duration>")
        lines.append("      <itunes:explicit>false</itunes:explicit>")
        lines.append(f'      <itunes:image href="{xml_escape(image_url)}"/>')
        lines.append(f'      <enclosure url="{xml_escape(audio_url)}" length="{r["mp3Bytes"]}" type="audio/mpeg"/>')
        lines.append("    </item>")

    lines.append("  </channel>")
    lines.append("</rss>")
    return "\n".join(lines) + "\n"


# --- 발행 ---


def publish_episode(env: dict, channel: dict, ep_dir: Path, audio_override: str | None, dry_run: bool) -> dict:
    """단일 에피소드 발행(오디오 업로드 + published.json 갱신). 발행 레코드 반환."""
    meta = load_yaml(ep_dir / "episode.yaml").get("episode", {})
    status = meta.get("status", "draft")
    if status not in ("ready", "published"):
        raise SystemExit(f"[publish] {ep_dir.name}: status={status} (ready 이상만 발행)")

    slug = meta["slug"]
    audio_key = f"episodes/{slug}/audio.mp3"
    pub_path = ep_dir / "published.json"
    pub = json.loads(pub_path.read_text(encoding="utf-8")) if pub_path.exists() else {}

    audio_src = audio_override or meta.get("audio", {}).get("sourceHint", "")
    if audio_src and not Path(audio_src).is_absolute():
        cand = ROOT / audio_src
        audio_src = str(cand if cand.exists() else Path.home() / audio_src)

    need_audio = bool(audio_override) or "guid" not in pub or "mp3Bytes" not in pub
    tmp_dir = LIB_DIR / ".tmp"
    tmp_dir.mkdir(exist_ok=True)

    if need_audio:
        if not audio_src or not Path(audio_src).exists():
            raise SystemExit(f"[publish] {ep_dir.name}: 오디오 소스 없음 (--audio 로 m4a 경로 지정): {audio_src}")
        mp3_tmp = tmp_dir / f"{slug}.mp3"
        print(f"[{ep_dir.name}] 전사 {Path(audio_src).name} -> mp3 ...")
        transcode_to_mp3(Path(audio_src), mp3_tmp)
        dur = probe_duration_sec(mp3_tmp)
        size = mp3_tmp.stat().st_size
        guid = pub.get("guid") or str(uuid.uuid4())
        published_at = pub.get("publishedAt") or datetime.now(KST).replace(microsecond=0).isoformat()
        pub = {
            "guid": guid,
            "audioKey": audio_key,
            "mp3Bytes": size,
            "durationSec": dur,
            "publishedAt": published_at,
            "mp3Sha8": sha8(mp3_tmp),
        }
        print(f"  duration={fmt_hhmmss(dur)}  size={size:,} B  guid={guid}")
        if not dry_run:
            r2_put(env, channel["r2"]["bucket"], audio_key, mp3_tmp, "audio/mpeg", "public, max-age=86400")
            pub_path.write_text(json.dumps(pub, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        mp3_tmp.unlink(missing_ok=True)

    return published_record(channel, ep_dir, meta, pub)


def all_published_records(channel: dict) -> list[dict]:
    """published.json 이 있는 모든 에피소드의 발행 레코드."""
    records = []
    for ep_dir in episode_dirs(None):
        pub_path = ep_dir / "published.json"
        if not pub_path.exists():
            continue
        meta = load_yaml(ep_dir / "episode.yaml").get("episode", {})
        pub = json.loads(pub_path.read_text(encoding="utf-8"))
        records.append(published_record(channel, ep_dir, meta, pub))
    return records


def upload_cover(env: dict, channel: dict, dry_run: bool) -> None:
    """쇼커버 소스를 정규화해 R2 로 업로드."""
    src = PODCAST_DIR / channel["cover"]["source"]
    if not src.exists():
        print(f"[cover] 소스 없음, 건너뜀: {src}")
        return
    tmp = LIB_DIR / ".tmp"
    tmp.mkdir(exist_ok=True)
    out_jpg = tmp / "show-cover-3000.jpg"
    normalize_cover(src, out_jpg)
    print(f"[cover] 정규화 {out_jpg.stat().st_size:,} B")
    if not dry_run:
        r2_put(env, channel["r2"]["bucket"], channel["cover"]["key"], out_jpg, "image/jpeg", "public, max-age=86400")
    out_jpg.unlink(missing_ok=True)


def render_episode_stills(episode_ids: list[str]) -> None:
    """render_episode_image.py 를 subprocess 로 호출해 카드풍 스틸(커버/정적)을 생성한다(업로드 전)."""
    renderer = LIB_DIR / "render_episode_image.py"
    for ep_id in episode_ids:
        try:
            subprocess.run([sys.executable, str(renderer), "--episode", ep_id], check=True)
        except subprocess.CalledProcessError as exc:
            print(f"[render] {ep_id} 스틸 생성 실패(소스 없음 등), 건너뜀: {exc}")


def upload_episode_images(env: dict, channel: dict, records: list[dict], dry_run: bool) -> None:
    """에피소드별 커버와 썸네일 소스를 정규화해 R2 로 업로드."""
    tmp = LIB_DIR / ".tmp"
    tmp.mkdir(exist_ok=True)
    uploaded_16x9: set[tuple[str, str]] = set()
    for r in sorted(records, key=lambda x: x["episodeNo"]):
        src_raw = r.get("_imageSource") or ""
        key = r.get("_imageKey") or ""
        if src_raw and key:
            src = Path(src_raw)
            if not src.exists():
                print(f"[episode-cover] 소스 없음, 건너뜀: {src}")
            else:
                out_jpg = tmp / f"{r['slug']}-cover-3000.jpg"
                normalize_cover(src, out_jpg)
                print(f"[episode-cover] #{r['episodeNo']} 정규화 {out_jpg.stat().st_size:,} B")
                if not dry_run:
                    r2_put(env, channel["r2"]["bucket"], key, out_jpg, "image/jpeg", "public, max-age=86400")
                out_jpg.unlink(missing_ok=True)

        static_src_raw = r.get("_staticImageSource") or ""
        static_key = r.get("_staticImageKey") or ""
        if static_src_raw and static_key:
            static_src = Path(static_src_raw)
            marker = (str(static_src.resolve()) if static_src.exists() else static_src_raw, static_key)
            uploaded_16x9.add(marker)
            if not static_src.exists():
                print(f"[episode-static] 소스 없음, 건너뜀: {static_src}")
            else:
                static_jpg = tmp / f"{r['slug']}-static-video.jpg"
                normalize_thumbnail(static_src, static_jpg)
                print(f"[episode-static] #{r['episodeNo']} 정규화 {static_jpg.stat().st_size:,} B")
                if not dry_run:
                    r2_put(env, channel["r2"]["bucket"], static_key, static_jpg, "image/jpeg", "public, max-age=86400")
                static_jpg.unlink(missing_ok=True)

        thumb_src_raw = r.get("_thumbnailSource") or ""
        thumb_key = r.get("_thumbnailKey") or ""
        if not thumb_src_raw or not thumb_key:
            continue
        thumb_src = Path(thumb_src_raw)
        marker = (str(thumb_src.resolve()) if thumb_src.exists() else thumb_src_raw, thumb_key)
        if marker in uploaded_16x9:
            continue
        if not thumb_src.exists():
            print(f"[episode-thumbnail] 소스 없음, 건너뜀: {thumb_src}")
            continue
        thumb_jpg = tmp / f"{r['slug']}-thumbnail.jpg"
        normalize_thumbnail(thumb_src, thumb_jpg)
        print(f"[episode-thumbnail] #{r['episodeNo']} 정규화 {thumb_jpg.stat().st_size:,} B")
        if not dry_run:
            r2_put(env, channel["r2"]["bucket"], thumb_key, thumb_jpg, "image/jpeg", "public, max-age=86400")
        thumb_jpg.unlink(missing_ok=True)


def upload_hf_source_assets(records: list[dict], dry_run: bool, repo: str = HF_MEDIA_REPO) -> None:
    """에피소드 원본 이미지를 HF media repo 에 업로드."""
    planned: dict[str, Path] = {}
    for r in records:
        for asset in r.get("_sourceAssetUploads") or []:
            key = str(asset.get("key") or "").strip()
            src = Path(str(asset.get("sourcePath") or ""))
            if not key:
                continue
            if not src.exists():
                print(f"[hf-source] 소스 없음, 건너뜀: {src}")
                continue
            planned.setdefault(key, src)

    if not planned:
        print("[hf-source] 업로드할 원본 이미지 없음")
        return
    for key, src in sorted(planned.items()):
        print(f"  HF put  {key}  ({src.stat().st_size:,} B)")
    if dry_run:
        print("[hf-source] dry-run: 실제 업로드 안 함")
        return

    from huggingface_hub import CommitOperationAdd, HfApi

    from dartlab.core.hfRetry import retryHfCall
    from dartlab.pipeline.hfUpload import _resolveHfToken

    ops = [CommitOperationAdd(path_in_repo=key, path_or_fileobj=str(src)) for key, src in sorted(planned.items())]
    retryHfCall(
        HfApi(token=_resolveHfToken()).create_commit,
        repo_id=repo,
        repo_type="dataset",
        operations=ops,
        commit_message=f"팟캐스트: 원본 이미지 {len(ops)}개 업로드",
    )
    print(f"[hf-source] {repo} 원본 이미지 {len(ops)}개 업로드 완료")


def archive_manual_upload_pair(ep_dir: Path, audio_override: str | None, dry_run: bool) -> None:
    """팟빵 등 수동 업로드용 m4a + 16:9 jpg 한 쌍을 _uploads 에 저장."""
    meta = load_yaml(ep_dir / "episode.yaml").get("episode", {})
    raw_audio = audio_override or meta.get("audio", {}).get("sourceHint", "")
    if not raw_audio:
        print(f"[uploads] {ep_dir.name}: 오디오 소스 없음, _uploads 사본 건너뜀")
        return
    audio_src = resolve_audio_source(raw_audio)
    if not audio_src.exists():
        raise SystemExit(f"[uploads] 오디오 소스 없음: {audio_src}")

    static = meta.get("staticImage") or meta.get("thumbnail") or {}
    static_source = str(static.get("source") or "").strip()
    if not static_source:
        raise SystemExit(f"[uploads] {ep_dir.name}: staticImage.source 없음")
    static_src = resolve_episode_image_source(ep_dir, static_source)
    if not static_src.exists():
        raise SystemExit(f"[uploads] 16:9 이미지 없음: {static_src}")

    name = (
        f"{int(meta['episodeNo']):02d}{camel_upload_slug(str(meta.get('topicSlug') or meta.get('slug') or 'episode'))}"
    )
    audio_out = UPLOADS_DIR / f"{name}{audio_src.suffix.lower() or '.m4a'}"
    image_out = UPLOADS_DIR / f"{name}.jpg"
    print(f"[uploads] archive {audio_out.name} + {image_out.name}")
    if dry_run:
        print("[uploads] dry-run: 실제 복사 안 함")
        return
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(audio_src, audio_out)
    shutil.copy2(static_src, image_out)
    if audio_out.stat().st_size != audio_src.stat().st_size:
        raise SystemExit(f"[uploads] 오디오 사본 크기 불일치: {audio_out}")
    if image_out.stat().st_size <= 0:
        raise SystemExit(f"[uploads] 이미지 사본 비정상: {image_out}")


def main(argv: list[str]) -> int:
    """CLI 진입점."""
    parser = argparse.ArgumentParser(description="DartLab 팟캐스트 발행 (R2 SSOT)")
    parser.add_argument("--episode", help="에피소드 폴더명 (예 P01-dartlab-2700-filings). 생략 시 미변경")
    parser.add_argument("--audio", help="원본 m4a 경로 (전사 대상)")
    parser.add_argument("--rebuild-only", action="store_true", help="오디오 미변경, feed/index/cover 만 재생성")
    parser.add_argument("--no-cover", action="store_true", help="쇼커버 업로드 건너뜀")
    parser.add_argument("--no-hf-source-assets", action="store_true", help="원본 이미지 HF 업로드 건너뜀")
    parser.add_argument("--no-uploads-archive", action="store_true", help="팟빵용 _uploads 사본 생성 건너뜀")
    parser.add_argument("--hf-source-assets-only", action="store_true", help="R2 없이 원본 이미지만 HF 업로드")
    parser.add_argument("--hf-repo", default=HF_MEDIA_REPO, help="원본 이미지를 올릴 HF dataset repo")
    parser.add_argument(
        "--render-images", action="store_true", help="업로드 전 render_episode_image.py 로 카드풍 스틸(커버/정적) 생성"
    )
    parser.add_argument("--dry-run", action="store_true", help="업로드 없이 로컬 검증")
    args = parser.parse_args(argv)

    channel = load_channel()
    env = load_env() if (not args.dry_run and not args.hf_source_assets_only) else {"CI": "1"}
    base = channel["r2"]["baseUrl"].rstrip("/")

    if args.hf_source_assets_only:
        records = all_published_records(channel)
        if not records:
            raise SystemExit("[publish] 발행된 에피소드 0. 원본 이미지 업로드 대상 없음.")
        upload_hf_source_assets(records, args.dry_run, args.hf_repo)
        return 0

    if args.episode and not args.rebuild_only:
        publish_episode(env, channel, EPISODES_DIR / args.episode, args.audio, args.dry_run)

    records = all_published_records(channel)
    if args.dry_run and args.episode and not records:
        records = [publish_episode(env, channel, EPISODES_DIR / args.episode, args.audio, True)]
    if not records:
        raise SystemExit("[publish] 발행된 에피소드 0. --episode + --audio 로 첫 발행 필요.")

    index_json = build_index(channel, records)
    feed_xml = build_feed(channel, records)
    tmp = LIB_DIR / ".tmp"
    tmp.mkdir(exist_ok=True)
    (tmp / "index.json").write_text(index_json, encoding="utf-8")
    (tmp / "feed.xml").write_text(feed_xml, encoding="utf-8")
    print(f"[build] index.json ({len(records)} 편) + feed.xml 생성")

    if not args.no_cover:
        upload_cover(env, channel, args.dry_run)
    if args.render_images:
        render_ids = [args.episode] if args.episode else [r["episodeId"] for r in records]
        render_episode_stills([e for e in render_ids if e])
    upload_episode_images(env, channel, records, args.dry_run)
    if args.episode and not args.rebuild_only and not args.no_uploads_archive:
        archive_manual_upload_pair(EPISODES_DIR / args.episode, args.audio, args.dry_run)
    if not args.no_hf_source_assets:
        upload_hf_source_assets(records, args.dry_run, args.hf_repo)

    if not args.dry_run:
        r2_put(
            env, channel["r2"]["bucket"], "index.json", tmp / "index.json", "application/json", "public, max-age=300"
        )
        r2_put(env, channel["r2"]["bucket"], "feed.xml", tmp / "feed.xml", "application/rss+xml", "public, max-age=300")

    print("\n=== 발행 완료 ===")
    print(f"피드 URL   : {base}/feed.xml")
    print(f"인덱스 URL : {base}/index.json")
    for r in sorted(records, key=lambda x: x["episodeNo"], reverse=True):
        print(f"  #{r['episodeNo']} {r['title']}  ({fmt_hhmmss(r['durationSec'])})  {base}/{r['audioKey']}")
    if args.dry_run:
        print("\n(dry-run: 실제 업로드 안 함)")
    else:
        print("\n다음: feed.xml 을 castfeedvalidator.com 로 검증 후, 애플/스포티/유튜브뮤직에 피드 URL 제출(최초 1회).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
