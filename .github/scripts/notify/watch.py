"""공개 왓처 토픽 러너 (P2) — scan SSOT 직독 → 매치 → 허브 /send 브로드캐스트.

토픽 1개 = 함수 1개(레지스트리·synth 모듈 0 — YAGNI, P3 졸업 시 발견적 추출). 베이크 0(scan 라이브 직독).
중복 억제 = 허브 sentNonce 가 곧 last-seen 매치 id set: 매치별 nonce = sha1(topic:slug) → 이미 보낸 매치는
허브에서 409(멱등 드롭), 새 매치만 실제 발송. 발행 러너(send.py)와 별개 워크플로(watch.yml cron).

  - newIpo   = scan('ipo') 신규상장. slug=corpCode(발행사 안정키) 등장 1회 + confirmationRcept 있으면
               확정공모가 1회(청약 임박). 기재정정마다 rcept 가 바뀌어도 재발화 없음(발행사별 1회 보장).
  - newOrders = scan('orders') book-to-bill >= 1. 허브 /active set-diff 커서(topicActive)로 신규 진입만
               발화, 하락 후 재상승(재크로싱)은 재발화(01-arch §5 threshold_cross). slug=stockCode.

현재 운영 계약은 Skill OS ``operation.notifyPipeline``이다.
실행: uv run python -X utf8 .github/scripts/notify/watch.py [--topics newIpo,newOrders] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from hubClient import classify, post_active, post_to_hub
from sanitize import sanitize

_TERMINAL = "/terminal"  # 클릭 자기 라우트(피싱 차단).
_TERMINAL_IPO = "/terminal?ipo=1"  # newIpo 딥링크 · 터미널 IPO 공모 다이얼로그 자동 오픈(TerminalSurface ?ipo=1).


def _won(v: object) -> str | None:
    try:
        return f"{int(float(v)):,}원"
    except (TypeError, ValueError):
        return None


def _baked_ipo_df():
    """왓치 첫 관문 베이크(buildIpoReports)가 같은 runner 에 남긴 reports.parquet 직독.

    베이크와 왓치가 같은 IPO 파싱을 두 번 하지 않게(단일 파싱), 왓치는 스스로 scan('ipo')를 돌리는
    대신 방금 구운 parquet 을 읽는다. 컬럼명이 scan('ipo')와 호환(rcept·corpName·priceBand*·subscription·
    appliedPer·isSpac)이라 eval_new_ipo 무변경 소비. 부재(베이크 스킵/실패)면 None 이라 scan 폴백.
    """
    try:
        from pathlib import Path

        import polars as pl

        import dartlab.config as _cfg
        from dartlab.core.dataConfig import DATA_RELEASES

        p = Path(_cfg.dataDir) / DATA_RELEASES["ipoReports"]["dir"] / "reports.parquet"
        if p.exists():
            return pl.read_parquet(p)
    except Exception:  # noqa: BLE001 . 베이크 부재/손상은 scan 폴백(알림 자체는 끊기지 않게)
        pass
    return None


def eval_new_ipo(df=None) -> list[dict]:
    """신규상장 알림 매치. df 주입 시 그 df(테스트/베이크 parquet), 없으면 베이크 parquet 후 scan('ipo') 폴백.

    발행사별 의미 있는 2 순간만 발화(노이즈 억제): ① 등장(slug=corpCode 안정키, 기재정정 재발화 0)
    ② 확정공모가([발행조건확정] doc, confirmationRcept 존재 시, slug=corpCode:conf, 청약 임박 신호).
    항등식 미검증분도 알림(공모 사실은 사실). 데이터원 우선순위: 명시 df > 베이크 parquet > scan('ipo').
    """
    if df is None:
        df = _baked_ipo_df()
    if df is None:
        import dartlab

        df = dartlab.scan("ipo")
    items: list[dict] = []
    for r in df.iter_rows(named=True):
        rcept = r.get("rcept")
        if not rcept:
            continue
        corp = str(r.get("corpCode") or rcept)  # 발행사 안정키(기재정정에도 불변). 결측 시 rcept 폴백.
        name = r.get("corpName") or "신규상장"
        low, high = _won(r.get("priceBandLow")), _won(r.get("priceBandHigh"))
        parts: list[str] = []
        if low and high:
            parts.append(f"공모가 {low.replace('원', '')}~{high}")
        if r.get("subscription"):
            parts.append(f"청약 {r['subscription']}")
        if r.get("appliedPer") is not None:
            parts.append(f"적용배수 {r['appliedPer']}")  # 모형 의존(PER·EV/EBITDA 등), 중립 라벨로 오표기 방지
        spac = " (스팩)" if r.get("isSpac") else ""
        detail = " · ".join(parts)
        # 신호 1: 발행사 등장. slug=corpCode 라 기재정정본이 새 rcept 를 받아도 재발화 없음(발행사별 1회).
        items.append(
            {
                "topic": "newIpo",
                "slug": corp,
                "notification": {
                    "title": sanitize(f"[신규상장] {name}{spac}", 80),
                    "body": sanitize(detail or "증권신고서 접수", 120),
                    "url": _TERMINAL_IPO,
                    "tag": f"ipo:{corp}",
                },
            }
        )
        # 신호 2: 확정공모가 공시([발행조건확정] doc). 청약 임박(가장 actionable). 발행사별 1회 추가 발화.
        if r.get("confirmationRcept"):
            items.append(
                {
                    "topic": "newIpo",
                    "slug": f"{corp}:conf",
                    "notification": {
                        "title": sanitize(f"[공모가확정] {name}{spac}", 80),
                        "body": sanitize(detail or "확정공모가 공시 · 청약 임박", 120),
                        "url": _TERMINAL_IPO,
                        "tag": f"ipo:{corp}:conf",
                    },
                }
            )
    return items


def eval_new_orders(df=None, min_book_to_bill: float = 1.0) -> list[dict]:
    """scan('orders') book-to-bill>=1 레벨 매치 반환. micro-cap/잡음 가드(매출·계약건수).

    발화 dedup 은 허브 /active 커서(topicActive)가 처리(_send_stateful): 직전 활성 set 과 diff 해 신규
    진입만 발송하고, 하락으로 이탈한 종목은 set 에서 빠져 재상승(재크로싱) 시 다시 발화(01-arch §5).
    """
    if df is None:
        import dartlab

        df = dartlab.scan("orders")
    items: list[dict] = []
    for r in df.iter_rows(named=True):
        b2b = r.get("bookToBill")
        code = r.get("stockCode")
        if b2b is None or b2b < min_book_to_bill or not code:
            continue
        if not r.get("recentRevenue") or (r.get("nContract") or 0) < 1:
            continue  # micro-cap/잡음 가드(docstring 경고)
        name = r.get("corpName") or f"종목 {code}"  # 코드만으론 정체 불명(newIpo 동형 가독)
        parts = [f"book-to-bill {b2b:.2f}"]
        if r.get("grade"):
            parts.append(f"등급 {r['grade']}")
        if r.get("topCounterparty"):
            parts.append(f"주거래 {r['topCounterparty']}")
        items.append(
            {
                "topic": "newOrders",
                "slug": str(code),
                "notification": {
                    "title": sanitize(f"[신규수주] {name} 백로그 확대", 80),
                    # 딥링크 · 클릭 시 해당 종목이 터미널에 열림(newIpo ?ipo=1 동형, ?sym= 종목 선택).
                    "body": sanitize(" · ".join(parts), 120),
                    "url": f"/terminal?sym={code}",
                    "tag": f"orders:{code}",
                },
            }
        )
    return items


def eval_screen_alert(members_by_screen=None) -> list[dict]:
    """저장 스크린(notify=true) 멤버십 진입 알림. /active set-diff 커서(진입 발화, 이탈 후 재진입 재발화).

    왓처 구독 = scan.screen.watchedScreens() 각각을 evaluateScreenMembers 로 현재 멤버셋 평가. slug=
    screenId:stockCode 라 허브 /active 가 직전 멤버셋과 diff 해 신규 진입만 발화(newOrders 동형 threshold
    _cross). members_by_screen 주입 시 dartlab 실호출 없이 검증(테스트). 첫 활성화 시 현 멤버 전원이 진입으로
    보여 flood 가능해 default 토픽에서 제외(운영자가 --topics 로 롤아웃 게이트).
    """
    if members_by_screen is None:
        from dartlab.scan.screen import evaluateScreenMembers, watchedScreens

        members_by_screen = {}
        for s in watchedScreens():
            members_by_screen[s["id"]] = {
                "title": s.get("title") or s["id"],
                "members": evaluateScreenMembers(s["id"]),
            }
    items: list[dict] = []
    for sid, info in members_by_screen.items():
        title = info.get("title") or sid
        for m in info.get("members", []):
            code = m.get("stockCode")
            if not code:
                continue
            name = m.get("corpName") or f"종목 {code}"
            items.append(
                {
                    "topic": "screenAlert",
                    "slug": f"{sid}:{code}",
                    "notification": {
                        "title": sanitize(f"[스크린] {name} · {title}", 80),
                        "body": sanitize(f"{title} 조건 진입", 120),
                        "url": f"/terminal?sym={code}",
                        "tag": f"screen:{sid}:{code}",
                    },
                }
            )
    return items


def _won_short(v: object) -> str | None:
    """원 값 을 조/억 단축 표기로 (알림 body 가독). 소액은 원 그대로."""
    try:
        f = float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    a = abs(f)
    if a >= 1e12:
        return f"{f / 1e12:,.2f}조"
    if a >= 1e8:
        return f"{f / 1e8:,.0f}억"
    return f"{f:,.0f}원"


def _fmt_flash(label: str, cur: object, yoy: object) -> str | None:
    """계정 1 개 를 '라벨 값(+증감율%)' 로. 값 없으면(대시) None(조용한 절단 금지, 호출자 skip)."""
    s = _won_short(cur)
    if s is None:
        return None
    try:
        s += f"({float(yoy):+.1f}%)"  # type: ignore[arg-type]
    except (TypeError, ValueError):
        pass
    return f"{label} {s}"


def eval_earnings_flash(df=None) -> list[dict]:
    """잠정실적 알림 매치. scan("earningsFlash") 직독 후 회사별 당일 1 건(연결 우선).

    본문 숫자(매출·영업익·순이익 + 전년동기 증감율)를 body 에 박아 클릭 없이 actionable.
    slug=corpCode:rceptDt (하루 1 건). 정정본은 다른 날짜라 갱신 숫자로 재발화(의도된 동작).
    scan 이 rceptDt desc + basis desc(연결 우선) 정렬이라 같은 slug 첫-승이 연결을 택한다.
    데이터원: 영업(잠정)실적 공정공시 + 매출액/손익구조 30(15)% 변동, live DART 직독(굽기 0).
    """
    if df is None:
        import dartlab

        date_from = os.environ.get("DARTLAB_EARNINGS_DATE_FROM") or None
        df = dartlab.scan("earningsFlash", dateFrom=date_from)
    items: list[dict] = []
    seen: set[str] = set()
    for r in df.iter_rows(named=True):
        corp = str(r.get("corpCode") or r.get("rcept") or "")
        dt = str(r.get("rceptDt") or "")
        slug = f"{corp}:{dt}"
        if not corp or slug in seen:
            continue
        seen.add(slug)
        name = r.get("corpName") or "잠정실적"
        # scan 프레임워크가 stockCode 를 종목코드 로 리네임(_enrichWithKorean). 테스트 FakeDF 는 stockCode.
        code = (r.get("stockCode") or r.get("종목코드") or "").strip()
        parts = [
            p
            for p in (
                _fmt_flash("매출", r.get("revenue"), r.get("revenueYoy")),
                _fmt_flash("영업익", r.get("operatingProfit"), r.get("operatingProfitYoy")),
                _fmt_flash("순익", r.get("netProfit"), r.get("netProfitYoy")),
            )
            if p
        ]
        basis = r.get("basis") or ""
        head = f"[잠정실적] {name}" + (f" ({basis})" if basis else "")
        items.append(
            {
                "topic": "earningsFlash",
                "slug": slug,
                "notification": {
                    "title": sanitize(head, 80),
                    "body": sanitize(" · ".join(parts) or "잠정실적 공시", 120),
                    "url": f"/terminal?sym={code}" if code else _TERMINAL,
                    "tag": f"earnings:{slug}",
                },
            }
        )
    return items


_EVALUATORS = {
    "newIpo": eval_new_ipo,
    "newOrders": eval_new_orders,
    "screenAlert": eval_screen_alert,
    "earningsFlash": eval_earnings_flash,
}

# threshold_cross(돌파형) 토픽 = 허브 /active set-diff 커서 경로(재크로싱 발화). new_listing 형은 stateless /send.
# screenAlert 는 스크린 멤버십 진입(이탈 후 재진입 재발화)이라 newOrders 동형 stateful.
_STATEFUL_TOPICS = {"newOrders", "screenAlert"}

# 발송 위생. 토픽별 발송 cap(콜드스타트 폭주 가드). 24h dedupe 는 허브 sentNonce 가 영구 멱등으로 처리(불요).
# 조용한 시간(22~08)은 cron 발화시각(평일 17시 KST)이 구조적으로 회피(야간 배치 큐 미도입, YAGNI).
# newIpo=40: 윈도 발행사(~30) + confirmation 신호 여유. 초과분은 로그(newest-first 정렬이라 최신부터 발송,
# 절단되는 건 가장 오래된 stale IPO 라 터미널 목록으로 커버. 조용한 절단 금지).
_TOPIC_CAP = {"newIpo": 40, "newOrders": 15, "screenAlert": 50, "earningsFlash": 60}


def cap_matches(matches: list[dict], caps: dict[str, int] = _TOPIC_CAP) -> tuple[list[dict], list[dict]]:
    """매치를 토픽별 cap 으로 자른다 — 입력 순서(scan 정렬=관련도순) 유지. (보낼것, 드롭) 반환.

    조용한 절단 금지: 드롭분은 호출자가 로그한다.
    """
    kept: list[dict] = []
    dropped: list[dict] = []
    seen: dict[str, int] = {}
    for m in matches:
        t = m["topic"]
        cap = caps.get(t, 50)
        if seen.get(t, 0) < cap:
            kept.append(m)
            seen[t] = seen.get(t, 0) + 1
        else:
            dropped.append(m)
    return kept, dropped


def _send_stateless(hub, token, matches: list[dict], ts: int) -> list[str]:
    """new_listing 형 토픽 per-match /send + 토픽 cap. problems 리스트 반환(전건 실패만 RED)."""
    kept, dropped = cap_matches(matches)
    for m in dropped:  # 조용한 절단 금지, 드롭 명시 로그
        print(f"[watch] cap 초과 drop: {m['topic']}:{m['slug']}", flush=True)
    new_sent = dup = 0
    problems: list[str] = []
    for m in kept:
        status, body = post_to_hub(hub, token, m["topic"], m["slug"], m["notification"], ts)
        kind = classify(status)
        b = body or {}
        sent_n = int(b.get("sent") or 0)
        failed_n = int(b.get("failed") or 0)
        if kind == "problem":
            problems.append(f"{m['topic']}:{m['slug']} 발송 실패(HTTP {status})")
        elif kind == "dup":
            dup += 1  # 이미 보낸 매치(last-seen set), 정상
        elif sent_n == 0 and failed_n:
            # 허브 전건 발송 실패(sent=0). 허브가 nonce 롤백해 다음 cron 재시도. RED 가시화(조용한 영구 미발화 방지).
            problems.append(f"{m['topic']}:{m['slug']} 전건 발송 실패(failed={failed_n}, nonce 롤백·재시도 예정)")
        else:
            new_sent += 1
            if failed_n:  # 부분 실패: 일부 배송됨(nonce 유지). 조용한 절단 금지로 표면화하되 RED 는 아님.
                print(
                    f"::warning::{m['topic']}:{m['slug']} 부분 발송 실패(sent={sent_n}, failed={failed_n})", flush=True
                )
            print(f"[watch] {m['topic']}:{m['slug']} → sent={sent_n}", flush=True)
    print(f"[watch] stateless 신규 {new_sent}건 · dup {dup}건 · 실패 {len(problems)}건", flush=True)
    return problems


def _send_stateful(hub, token, topic: str, matches: list[dict], ts: int) -> list[str]:
    """threshold_cross 토픽 활성 매치 set 전체를 /active 로. 허브가 직전 set 과 diff 해 신규 진입만 발화.

    재크로싱(하락 후 재상승) 발화를 위해 per-match /send(영구 nonce) 대신 set-diff 커서 경로 사용.
    """
    active = [{"key": m["slug"], "notification": m["notification"]} for m in matches]
    status, body = post_active(hub, token, topic, active, ts)
    b = body or {}
    if classify(status) == "problem":
        return [f"{topic} /active 실패(HTTP {status})"]
    entered = int(b.get("entered") or 0)
    sent_n = int(b.get("sent") or 0)
    failed_n = int(b.get("failed") or 0)
    print(f"[watch] {topic}: 신규진입 {entered}건 · sent={sent_n} · failed={failed_n}", flush=True)
    if entered and sent_n == 0 and failed_n:
        return [f"{topic} 전건 발송 실패(failed={failed_n})"]
    if failed_n:
        print(f"::warning::{topic} 부분 발송 실패(sent={sent_n}, failed={failed_n})", flush=True)
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description="공개 왓처 토픽 러너")
    ap.add_argument("--topics", default="newIpo,newOrders", help="콤마구분 토픽(기본 전체)")
    ap.add_argument("--dry-run", action="store_true", help="POST 생략(매치만)")
    args = ap.parse_args()

    hub = os.environ.get("PUSHHUB_URL", "").rstrip("/")
    token = os.environ.get("PUSHHUB_SEND_TOKEN", "")
    if not args.dry_run and (not hub or not token):
        # 허브 미배포/secret 미설정 = 롤아웃 전 = graceful no-op(scan 도 생략, RED 아님). 배포 후 자동 활성.
        print("[watch] PUSHHUB 미설정 — skip(허브 미배포·롤아웃 전)", flush=True)
        return 0

    topics = [t.strip() for t in args.topics.split(",") if t.strip() in _EVALUATORS]
    by_topic: dict[str, list[dict]] = {}
    for t in topics:
        found = _EVALUATORS[t]()
        print(f"[watch] {t}: 매치 {len(found)}건", flush=True)
        by_topic[t] = found

    if args.dry_run:
        for found in by_topic.values():
            for m in found:
                print(
                    f"[watch] dry-run {m['topic']}:{m['slug']}: {json.dumps(m['notification'], ensure_ascii=False)}",
                    flush=True,
                )
        return 0

    ts = int(time.time())
    problems: list[str] = []
    for t, found in by_topic.items():
        # threshold_cross 는 /active set-diff(재크로싱 발화), new_listing 형은 per-match /send.
        if t in _STATEFUL_TOPICS:
            problems += _send_stateful(hub, token, t, found, ts)
        else:
            problems += _send_stateless(hub, token, found, ts)

    if problems:
        for p in problems:
            print(f"::error::왓처 발송 실패: {p}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
