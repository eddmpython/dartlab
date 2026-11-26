"""DartLab 이용 숫자 보고. 누가 얼마나 쓰는지 공개 집계로 본다.

사람을 식별하는 값은 읽지도 저장하지도 않는다. 모든 숫자는 각 서비스가 이미 집계해 둔 값이다.
북극성 지표(검증된 분석 루프, ``operation.productDirection``)가 아니라 방향을 보는 채택 신호다.

읽는 곳:

1. PyPI (pypistats.org): 운영체제별 일 다운로드 180일. Linux 는 CI 와 서버 설치가 대부분이라
   Windows 와 macOS 다운로드를 사람이 직접 설치한 수에 가깝게 본다.
2. GitHub 저장소: 별과 포크가 생긴 시각(달별 증가), 최근 14일 방문과 클론과 유입처.
   방문과 클론은 저장소 관리 권한이 있는 토큰으로만 읽힌다. 없으면 그 줄을 건너뛴다.
3. GitHub 윈도우 앱 저장소: 판별 누적 다운로드.
4. HuggingFace 데이터셋: 최근 30일 다운로드. 라이브러리가 데이터를 받을 때 늘고 우리 CI 도 센다.

GitHub 방문과 클론, HF 다운로드는 지난 기간만 보여 주므로 ``--history`` 로 받은 날의 값을
CSV 에 쌓아 두어야 추이가 남는다.

사용법::

    uv run python -X utf8 tests/audit/usageReport.py
    uv run python -X utf8 tests/audit/usageReport.py --history ~/.dartlab/usage/history.csv
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

PYPI_HUMAN_OS = ("Windows", "Darwin")
HISTORY_COLUMNS = ("fetchedOn", "source", "metric", "period", "value")


def weekStart(day: dt.date) -> dt.date:
    """그 날이 속한 주의 월요일."""
    return day - dt.timedelta(days=day.weekday())


def summarizePypiSystem(rows: list[dict], today: dt.date, *, days: int = 30, weeks: int = 8) -> dict:
    """pypistats system 응답의 data 행을 최근 days 일 운영체제별 합계와 주별 사람 설치 추이로 묶는다.

    Args:
        rows: ``{"category", "date", "downloads"}`` 행 목록.
        today: 기준일. 이 날 이전 days 일을 최근 구간으로 센다.
        days: 최근 구간 길이.
        weeks: 주별 추이에 남길 주 수. 기준일이 속한 주는 다 차지 않아 뺀다.

    Returns:
        ``{"recentByOs": {os: n}, "recentTotal": n, "recentHuman": n, "weeklyHuman": [(월요일, n)]}``.
    """
    since = today - dt.timedelta(days=days)
    recent: Counter[str] = Counter()
    weekly: Counter[dt.date] = Counter()
    thisWeek = weekStart(today)
    firstWeek = thisWeek - dt.timedelta(weeks=weeks)
    for row in rows:
        day = dt.date.fromisoformat(row["date"])
        category = str(row.get("category") or "null")
        count = int(row.get("downloads") or 0)
        if since <= day < today:
            recent[category] += count
        if category in PYPI_HUMAN_OS and firstWeek <= weekStart(day) < thisWeek:
            weekly[weekStart(day)] += count
    weeklyHuman = [(firstWeek + dt.timedelta(weeks=i), weekly[firstWeek + dt.timedelta(weeks=i)]) for i in range(weeks)]
    return {
        "recentByOs": dict(recent),
        "recentTotal": sum(recent.values()),
        "recentHuman": sum(recent[name] for name in PYPI_HUMAN_OS),
        "weeklyHuman": weeklyHuman,
    }


def countByMonth(timestamps: list[str], *, months: int = 6, today: dt.date) -> list[tuple[str, int]]:
    """ISO 시각 목록을 최근 months 달의 달별 건수로 센다. 기준일이 속한 달을 포함한다."""
    counts = Counter(stamp[:7] for stamp in timestamps if stamp)
    keys: list[str] = []
    year, month = today.year, today.month
    for _ in range(months):
        keys.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return [(key, counts.get(key, 0)) for key in reversed(keys)]


def releaseDownloads(releases: list[dict]) -> list[tuple[str, str, int]]:
    """GitHub releases 응답을 (판 이름, 낸 날, 첨부 파일 다운로드 합) 목록으로 바꾼다. 최신 판이 앞이다."""
    out: list[tuple[str, str, int]] = []
    for release in releases:
        total = sum(int(asset.get("download_count") or 0) for asset in release.get("assets") or [])
        out.append((str(release.get("tag_name") or ""), str(release.get("published_at") or "")[:10], total))
    return sorted(out, key=lambda item: item[1], reverse=True)


def historyRows(report: dict, fetchedOn: dt.date) -> list[dict]:
    """보고 하나를 CSV 에 쌓을 행으로 편다. 지난 기간만 보여 주는 값과 누적값만 남긴다."""
    day = fetchedOn.isoformat()
    rows: list[dict] = []

    def add(source: str, metric: str, period: str, value: int | None) -> None:
        if value is not None:
            rows.append({"fetchedOn": day, "source": source, "metric": metric, "period": period, "value": int(value)})

    pypi = report.get("pypi") or {}
    for name, count in sorted((pypi.get("recentByOs") or {}).items()):
        add("pypi", f"downloads.{name}", "last30d", count)
    github = report.get("github") or {}
    add("github", "stars", "total", github.get("stars"))
    add("github", "forks", "total", github.get("forks"))
    traffic = github.get("traffic") or {}
    for key in ("views", "viewUniques", "clones", "cloneUniques"):
        add("github", key, "last14d", traffic.get(key))
    desktop = report.get("desktop") or []
    if desktop:
        add("desktop", "downloads", "total", sum(count for _, _, count in desktop))
    add("huggingface", "downloads", "last30d", report.get("hfDownloads"))
    return rows


def appendHistory(path: Path, rows: list[dict]) -> None:
    """행을 CSV 끝에 붙인다. 같은 날 같은 값은 다시 쓰지 않는다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    seen: set[tuple[str, ...]] = set()
    if path.exists():
        with path.open(encoding="utf-8", newline="") as handle:
            seen = {tuple(row[col] for col in HISTORY_COLUMNS) for row in csv.DictReader(handle)}
    fresh = [row for row in rows if tuple(str(row[col]) for col in HISTORY_COLUMNS) not in seen]
    writeHeader = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HISTORY_COLUMNS)
        if writeHeader:
            writer.writeheader()
        writer.writerows(fresh)


def _githubToken() -> str | None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    try:
        done = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() or None


def _getJson(client, url: str, **kwargs):
    response = client.get(url, **kwargs)
    response.raise_for_status()
    return response.json()


def _githubPages(client, url: str, headers: dict) -> list[dict]:
    items: list[dict] = []
    page = 1
    while True:
        batch = _getJson(client, url, params={"per_page": 100, "page": page}, headers=headers)
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


def collect(repo: str, desktopRepo: str, package: str, hfDataset: str, today: dt.date) -> dict:
    """네 곳에서 집계를 읽는다. 한 곳이 실패해도 나머지는 채우고 실패는 errors 에 남긴다."""
    import httpx

    report: dict = {"errors": []}
    token = _githubToken()
    base = {"Accept": "application/vnd.github+json"}
    if token:
        base["Authorization"] = f"Bearer {token}"
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        try:
            system = _getJson(client, f"https://pypistats.org/api/packages/{package}/system")
            report["pypi"] = summarizePypiSystem(system.get("data") or [], today)
        except httpx.HTTPError as exc:
            report["errors"].append(f"pypi: {type(exc).__name__}")
        try:
            meta = _getJson(client, f"https://api.github.com/repos/{repo}", headers=base)
            stars = _githubPages(
                client,
                f"https://api.github.com/repos/{repo}/stargazers",
                {**base, "Accept": "application/vnd.github.star+json"},
            )
            forks = _githubPages(client, f"https://api.github.com/repos/{repo}/forks", base)
            report["github"] = {
                "stars": meta.get("stargazers_count"),
                "forks": meta.get("forks_count"),
                "starsByMonth": countByMonth([s.get("starred_at", "") for s in stars], today=today),
                "forksByMonth": countByMonth([f.get("created_at", "") for f in forks], today=today),
            }
        except httpx.HTTPError as exc:
            report["errors"].append(f"github: {type(exc).__name__}")
        if "github" in report:
            try:
                views = _getJson(client, f"https://api.github.com/repos/{repo}/traffic/views", headers=base)
                clones = _getJson(client, f"https://api.github.com/repos/{repo}/traffic/clones", headers=base)
                referrers = _getJson(
                    client, f"https://api.github.com/repos/{repo}/traffic/popular/referrers", headers=base
                )
                report["github"]["traffic"] = {
                    "views": views.get("count"),
                    "viewUniques": views.get("uniques"),
                    "clones": clones.get("count"),
                    "cloneUniques": clones.get("uniques"),
                    "referrers": [(r.get("referrer"), r.get("count"), r.get("uniques")) for r in referrers],
                }
            except httpx.HTTPError as exc:
                report["errors"].append(f"github traffic(관리 권한 토큰 필요): {type(exc).__name__}")
        try:
            releases = _githubPages(client, f"https://api.github.com/repos/{desktopRepo}/releases", base)
            report["desktop"] = releaseDownloads(releases)
        except httpx.HTTPError as exc:
            report["errors"].append(f"desktop: {type(exc).__name__}")
        try:
            report["hfDownloads"] = _getJson(client, f"https://huggingface.co/api/datasets/{hfDataset}").get(
                "downloads"
            )
        except httpx.HTTPError as exc:
            report["errors"].append(f"huggingface: {type(exc).__name__}")
    return report


def render(report: dict, today: dt.date) -> str:
    """보고를 사람이 읽는 글로 만든다."""
    lines = [f"DartLab 이용 숫자 ({today.isoformat()} 기준)", ""]
    pypi = report.get("pypi")
    if pypi:
        byOs = pypi["recentByOs"]
        parts = ", ".join(f"{name} {byOs[name]}" for name in sorted(byOs, key=lambda k: -byOs[k]))
        lines.append(f"[PyPI 설치] 최근 30일 {pypi['recentTotal']}번 ({parts})")
        lines.append(f"  사람 설치 추정(Windows+macOS): {pypi['recentHuman']}번")
        weekly = "  ".join(f"{start.strftime('%m-%d')} {count}" for start, count in pypi["weeklyHuman"])
        lines.append(f"  주별 사람 설치: {weekly}")
    github = report.get("github")
    if github:
        lines.append(f"[GitHub] 별 {github['stars']}개, 포크 {github['forks']}개")
        lines.append("  달별 새 별: " + "  ".join(f"{m} {n}" for m, n in github["starsByMonth"]))
        lines.append("  달별 새 포크: " + "  ".join(f"{m} {n}" for m, n in github["forksByMonth"]))
        traffic = github.get("traffic")
        if traffic:
            lines.append(
                f"  최근 14일 방문 {traffic['views']}번(방문자 {traffic['viewUniques']}명), "
                f"클론 {traffic['clones']}번(클론한 곳 {traffic['cloneUniques']}곳, CI 포함)"
            )
            refs = ", ".join(f"{name} {uniques}명" for name, _, uniques in traffic["referrers"])
            lines.append(f"  유입처: {refs or '없음'}")
    desktop = report.get("desktop")
    if desktop:
        total = sum(count for _, _, count in desktop)
        latest = desktop[0]
        lines.append(f"[윈도우 앱] 누적 다운로드 {total}번, 최신 {latest[0]}({latest[1]}) {latest[2]}번")
    if report.get("hfDownloads") is not None:
        lines.append(f"[HF 데이터] 최근 30일 다운로드 {report['hfDownloads']}번 (라이브러리와 우리 CI 포함)")
    for error in report.get("errors") or []:
        lines.append(f"[읽지 못함] {error}")
    return "\n".join(lines)


def main() -> int:
    """공개 집계를 읽어 출력하고, 원하면 CSV 에 쌓는다."""
    parser = argparse.ArgumentParser(description="DartLab 이용 숫자 보고")
    parser.add_argument("--repo", default="eddmpython/dartlab")
    parser.add_argument("--desktop-repo", default="eddmpython/dartlab-desktop")
    parser.add_argument("--package", default="dartlab")
    parser.add_argument("--hf-dataset", default="eddmpython/dartlab-data")
    parser.add_argument("--history", type=Path, default=None, help="받은 날의 값을 쌓을 CSV")
    args = parser.parse_args()

    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date()
    report = collect(args.repo, args.desktop_repo, args.package, args.hf_dataset, today)
    print(render(report, today))
    if args.history is not None:
        appendHistory(args.history.expanduser(), historyRows(report, today))
        print(f"\n[history] {args.history}")
    collected = any(key in report for key in ("pypi", "github", "desktop", "hfDownloads"))
    return 0 if collected else 1


if __name__ == "__main__":
    sys.exit(main())
