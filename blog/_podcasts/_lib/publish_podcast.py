"""DartLab 팟캐스트 발행자 (R2 SSOT).

운영자가 NotebookLM 에서 내려받은 m4a 를 넘기면, 이 스크립트가:
  1. m4a -> mp3 전사 (Spotify 는 RSS 로 m4a/AAC 를 임포트하지 않으므로 mp3 필수)
  2. 길이(ffprobe) + 바이트(os.stat) 측정
  3. guid mint-once (published.json 에 기록, 재발행 시 재사용, 구독자 중복 방지)
  4. 오디오 + 쇼커버를 R2(dartlab-podcast) 로 업로드 (node + wrangler, 기존 CF 토큰)
  5. 모든 발행 에피소드로 index.json(프론트 크로스링크) + feed.xml(RSS) 재생성 후 업로드
  6. 에피소드 URL / 피드 URL 출력

사용:
    uv run python -X utf8 blog/_podcasts/_lib/publish_podcast.py \
        --episode P01-dartlab-2700-filings \
        --audio "C:/Users/MSI/Downloads/2700개기업공시를한줄로통합하는dartlab.m4a"

    # 오디오 재업로드 없이 feed/index 만 재생성
    uv run python -X utf8 blog/_podcasts/_lib/publish_podcast.py --rebuild-only

    # 업로드 없이 로컬 검증
    uv run python -X utf8 blog/_podcasts/_lib/publish_podcast.py --episode ... --audio ... --dry-run

레포에는 텍스트만 커밋된다(episode.yaml, published.json, script.md, cover 소스).
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

LIB_DIR = Path(__file__).resolve().parent
PODCAST_DIR = LIB_DIR.parent
ROOT = PODCAST_DIR.parents[1]
EPISODES_DIR = PODCAST_DIR / "episodes"
CHANNEL_YAML = PODCAST_DIR / "channel.yaml"

KST = timezone(timedelta(hours=9))
ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"
ATOM_NS = "http://www.w3.org/2005/Atom"

NODE = shutil.which("node")
FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")
WRANGLER_JS = ROOT / "infra" / "workers" / "pushHub" / "node_modules" / "wrangler" / "bin" / "wrangler.js"


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


# --- 커버 ---


def normalize_cover(src: Path, out_jpg: Path, size: int = 3000, max_bytes: int = 500_000) -> None:
    """커버를 정사각 RGB size x size JPEG(<max_bytes) 로 정규화."""
    im = Image.open(src).convert("RGB")
    w, h = im.size
    s = min(w, h)
    left, top = (w - s) // 2, (h - s) // 2
    im = im.crop((left, top, left + s, top + s))
    # Apple 최소 1400, 소스보다 크게 억지 업스케일 안 함, 상한 size(3000)
    target = min(size, max(s, 1400))
    im = im.resize((target, target), Image.LANCZOS)
    q = 90
    while q >= 40:
        im.save(out_jpg, "JPEG", quality=q, optimize=True)
        if out_jpg.stat().st_size <= max_bytes:
            return
        q -= 5


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


# --- feed / index ---


def build_index(channel: dict, records: list[dict]) -> str:
    """프론트 크로스링크 레지스트리 index.json 문자열."""
    base = channel["r2"]["baseUrl"].rstrip("/")
    eps = []
    for r in sorted(records, key=lambda x: x["episodeNo"], reverse=True):
        eps.append(
            {
                "slug": r["slug"],
                "episodeId": r["episodeId"],
                "episodeNo": r["episodeNo"],
                "date": r["publishedAt"][:10],
                "title": r["title"],
                "audioUrl": f"{base}/{r['audioKey']}",
                "durationSec": r["durationSec"],
                "guid": r["guid"],
                "stockCode": r.get("stockCode", ""),
                "topicSlug": r.get("topicSlug", ""),
                "cardType": r.get("cardType", "meta"),
                "summary": r.get("summary", ""),
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

    return {
        "slug": slug,
        "episodeId": meta["episodeId"],
        "episodeNo": int(meta["episodeNo"]),
        "title": meta["title"],
        "summary": " ".join((meta.get("summary") or "").split()),
        "audioKey": pub["audioKey"],
        "mp3Bytes": pub["mp3Bytes"],
        "durationSec": pub["durationSec"],
        "guid": pub["guid"],
        "publishedAt": pub["publishedAt"],
        "stockCode": meta.get("stockCode", ""),
        "topicSlug": meta.get("topicSlug", ""),
        "cardType": meta.get("cardType", "meta"),
        "links": meta.get("links", {"blogSlug": "", "cardSlug": "", "terminalCode": ""}),
    }


def all_published_records(channel: dict) -> list[dict]:
    """published.json 이 있는 모든 에피소드의 발행 레코드."""
    records = []
    for ep_dir in episode_dirs(None):
        pub_path = ep_dir / "published.json"
        if not pub_path.exists():
            continue
        meta = load_yaml(ep_dir / "episode.yaml").get("episode", {})
        pub = json.loads(pub_path.read_text(encoding="utf-8"))
        records.append(
            {
                "slug": meta["slug"],
                "episodeId": meta["episodeId"],
                "episodeNo": int(meta["episodeNo"]),
                "title": meta["title"],
                "summary": " ".join((meta.get("summary") or "").split()),
                "audioKey": pub["audioKey"],
                "mp3Bytes": pub["mp3Bytes"],
                "durationSec": pub["durationSec"],
                "guid": pub["guid"],
                "publishedAt": pub["publishedAt"],
                "stockCode": meta.get("stockCode", ""),
                "topicSlug": meta.get("topicSlug", ""),
                "cardType": meta.get("cardType", "meta"),
                "links": meta.get("links", {"blogSlug": "", "cardSlug": "", "terminalCode": ""}),
            }
        )
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


def main(argv: list[str]) -> int:
    """CLI 진입점."""
    parser = argparse.ArgumentParser(description="DartLab 팟캐스트 발행 (R2 SSOT)")
    parser.add_argument("--episode", help="에피소드 폴더명 (예 P01-dartlab-2700-filings). 생략 시 미변경")
    parser.add_argument("--audio", help="원본 m4a 경로 (전사 대상)")
    parser.add_argument("--rebuild-only", action="store_true", help="오디오 미변경, feed/index/cover 만 재생성")
    parser.add_argument("--no-cover", action="store_true", help="쇼커버 업로드 건너뜀")
    parser.add_argument("--dry-run", action="store_true", help="업로드 없이 로컬 검증")
    args = parser.parse_args(argv)

    channel = load_channel()
    env = load_env() if not args.dry_run else {"CI": "1"}
    base = channel["r2"]["baseUrl"].rstrip("/")

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
