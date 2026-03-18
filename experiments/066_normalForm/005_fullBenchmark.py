"""실험 ID: 066-005
실험명: 283종목 전수 벤치마크 — 정규형(클러스터링) vs 기존

목적:
- 283종목 전수에서 정규형 vs 기존의 topic-level 성공률 비교
- 정규형만 성공/기존만 성공 케이스 분류
- 정규형 패러다임의 최종 판단 근거 확보

방법:
- 각 topic에서 table 블록이 하나라도 수평화되면 '성공'
- 기존: show(topic, block) 호출
- 정규형: horizontalizeTopic → 리스트 길이 > 0

실험일: 2026-03-18
"""

from __future__ import annotations

import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field

import polars as pl

sys.path.insert(0, "C:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")

# 004에서 핵심 함수만 인라인 (import 불가한 구조이므로)
# ── 시작: 004_analysis.py에서 복사 ──

from dartlab.engines.dart.docs.sections.tableParser import (
    splitSubtables, _headerCells, _isJunk, _dataRows, _normalizeHeader,
)

_MULTI_YEAR_KW = {"당기", "전기", "전전기", "당반기", "전반기", "당분기", "전분기"}
_STOCK_TYPES = {"보통주", "우선주", "기타주식"}
_KISU_RE = re.compile(r"제\s*(\d+)\s*기\s*(?:\d*분기|반기|말)?\s*\(?(당기|전기|전전기|당반기|전반기|당분기|전분기)\)?")
_SUFFIX_RE = re.compile(r"(사업)?부문$")
_NOTE_REF_RE = re.compile(r"\(\*\d*(?:,\d+)*\)")
_UNIT_RE = re.compile(r"^[\[\(（<]?\s*(?:단위|원화단위|외화단위|금액단위)\s*[:：/]?\s*[^\]）)>]*[\]）)>]?\s*$")
_DATE_RE = re.compile(r"^[\[\(（<]?\s*(?:기준일|기준|현재|기준시점)\s*[:：/]?\s*[^\]）)>]*[\]）)>]?\s*$")
_PERIOD_KW_RE = re.compile(r"\d*분기|반기|당기|전기|전전기|당반기|전반기|당분기|전분기|당기말|전기말")


@dataclass
class Triple:
    row_key: str; col_key: str; value: str

@dataclass
class NormalizedTable:
    triples: list[Triple] = field(default_factory=list)
    unit: str | None = None
    table_type: str = "flat"
    row_keys_ordered: list[str] = field(default_factory=list)
    col_keys_ordered: list[str] = field(default_factory=list)
    header_sig: str = ""


def _normalizeItem(name):
    name = re.sub(r"\s+", "", name).replace("（","(").replace("）",")").replace("ㆍ","·")
    name = _SUFFIX_RE.sub("", name).strip()
    name = _NOTE_REF_RE.sub("", name).strip()
    m = _KISU_RE.search(name)
    return m.group(2) if m else name

def _isJunkItem(name):
    s = re.sub(r"[,.\-\s]", "", name)
    return s.isdigit() or not s

def _extractUnit(lines):
    m = re.search(r"\(\s*단위\s*:\s*([^)]+)\)", "\n".join(lines))
    return m.group(1).strip() if m else None

def _isUnitOrDateHeader(cells):
    h = " ".join(c.strip() for c in cells).strip()
    return bool(_UNIT_RE.match(h) or _DATE_RE.match(h)) if h else False

def _groupHeaderSig(hc):
    h = _normalizeHeader(hc)
    h = _PERIOD_KW_RE.sub("", h)
    h = re.sub(r"\| *\|", "|", h)
    return re.sub(r"\s+", " ", h).strip()

def _parseMdTable(lines):
    headers, rows, sep = [], [], False
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(set(c.strip()) <= {"-",":"} for c in cells if c.strip()):
            sep = True; continue
        if not sep:
            if not headers: headers = list(cells)
        else:
            rows.append(cells)
    return headers, rows


def toNormalForm(sub, period_year=None):
    hc = _headerCells(sub)
    if _isJunk(hc): return NormalizedTable()
    dr = _dataRows(sub)
    if not dr: return NormalizedTable()
    headers, rows = _parseMdTable(sub)
    unit = _extractUnit(sub)
    sig = _groupHeaderSig(hc)
    if not headers or not rows:
        return NormalizedTable(unit=unit, header_sig=sig)
    if _isUnitOrDateHeader(headers):
        if rows: headers, rows = rows[0], rows[1:]
        else: return NormalizedTable(unit=unit, header_sig=sig)
    if any(kw in " ".join(headers) for kw in _MULTI_YEAR_KW):
        return _nfMultiYear(sub, headers, rows, period_year, unit, sig)
    return _nfFlat(headers, rows, unit, sig)


def _nfMultiYear(sub, headers, rows, period_year, unit, sig):
    kisu_nums, ki = [], -1
    for i, row in enumerate(rows):
        for cell in row:
            m = re.search(r"제\s*(\d+)\s*기", cell)
            if m: kisu_nums.append(int(m.group(1)))
        if kisu_nums: ki = i; break
    if not kisu_nums or period_year is None:
        ci = next((i for i,h in enumerate(headers) if "당기" in h and "전" not in h), 1)
        triples, rks, seen = [], [], set()
        for row in rows:
            if not row or not row[0].strip(): continue
            item = _normalizeItem(row[0].strip())
            if _isJunkItem(item): continue
            val = row[ci].strip() if ci < len(row) else ""
            if val and val != "-":
                if item not in seen: rks.append(item); seen.add(item)
                triples.append(Triple(item, "value", val))
        return NormalizedTable(triples, unit, "multi_year", rks, ["value"], sig)

    mx = max(kisu_nums); sk = sorted(kisu_nums, reverse=True)
    k2y = {kn: period_year - mx + kn for kn in kisu_nums}
    triples, rks, seen, prev = [], [], set(), ""
    for row in rows[ki+1:]:
        if not row or not row[0].strip(): continue
        first = row[0].strip()
        if first.startswith("※"): continue
        if first in _STOCK_TYPES and prev:
            item = _normalizeItem(f"{prev}-{first}"); vals = row[1:]
        elif len(row)>1 and row[1].strip() in _STOCK_TYPES:
            item = _normalizeItem(f"{first}-{row[1].strip()}"); vals = row[2:]; prev = first
        else:
            item = _normalizeItem(first); vals = row[1:]; prev = first
        if _isJunkItem(item): continue
        ne = [(i,v.strip()) for i,v in enumerate(vals) if v.strip() and v.strip()!="-" and v.strip() not in _STOCK_TYPES]
        if len(ne) >= len(sk):
            tail = ne[-len(sk):]
            for idx,(_,val) in enumerate(tail):
                if k2y[sk[idx]] == period_year:
                    if item not in seen: rks.append(item); seen.add(item)
                    triples.append(Triple(item, "value", val))
    return NormalizedTable(triples, unit, "multi_year", rks, ["value"], sig)


def _nfFlat(headers, rows, unit, sig):
    triples, rks, seen_rk, cks = [], [], set(), []
    for h in headers[1:]:
        cks.append(_normalizeItem(h) if h.strip() else f"col_{len(cks)}")
    gp = ""
    for row in rows:
        if not row or not row[0].strip(): continue
        raw = row[0].strip()
        if raw.startswith("※") or raw.startswith("☞"): continue
        item = _normalizeItem(raw)
        if _isJunkItem(item): continue
        values = row[1:]
        if all(not v.strip() or v.strip()=="-" for v in values) and len(values)>=2:
            gp = item; continue
        if gp: item = f"{gp}_{item}"
        if item not in seen_rk: rks.append(item); seen_rk.add(item)
        for i,ck in enumerate(cks):
            val = values[i].strip() if i<len(values) else ""
            if val and val!="-": triples.append(Triple(item, ck, val))
    return NormalizedTable(triples, unit, "flat", rks, cks, sig)


def horizontalizeTopic(topic_frame, period_cols):
    if topic_frame.is_empty(): return []
    cluster_data = defaultdict(lambda: defaultdict(list))
    for p in period_cols:
        if p not in topic_frame.columns: continue
        py = int(re.match(r"(\d{4})", p).group()) if re.match(r"(\d{4})", p) else None
        for ri in range(topic_frame.height):
            md = topic_frame[p][ri]
            if md is None: continue
            for sub in splitSubtables(str(md)):
                nf = toNormalForm(sub, period_year=py)
                if nf.triples: cluster_data[nf.header_sig][p].append(nf)
    results = []
    for sig, pt in cluster_data.items():
        df = _hzCluster(pt, period_cols)
        if df is not None: results.append(df)
    return results


def _hzCluster(pt, pc):
    my = any(t.table_type=="multi_year" for ts in pt.values() for t in ts)
    if my: return _hzMY(pt, pc)
    return _hzFlat(pt, pc)

def _hzMY(pt, pc):
    ipv, items, seen = {}, [], set()
    for p, ts in pt.items():
        for t in ts:
            if t.table_type != "multi_year": continue
            for rk in t.row_keys_ordered:
                if rk not in seen: items.append(rk); seen.add(rk)
            for tr in t.triples:
                ipv.setdefault(tr.row_key, {}).setdefault(p, tr.value)
    items = [i for i in items if not _isJunkItem(i)]
    return _build(items, ipv, pc)

def _hzFlat(pt, pc):
    data, items, seen, cks, seen_ck = defaultdict(dict), [], set(), [], set()
    for p, ts in pt.items():
        for t in ts:
            for rk in t.row_keys_ordered:
                if rk not in seen: items.append(rk); seen.add(rk)
            for ck in t.col_keys_ordered:
                if ck not in seen_ck: cks.append(ck); seen_ck.add(ck)
            for tr in t.triples: data[(tr.row_key, tr.col_key)][p] = tr.value
    if not data: return None
    items = [i for i in items if not _isJunkItem(i)]
    if len(cks) <= 1:
        ipv = {rk: pv for (rk, ck), pv in data.items() if rk in set(items)}
        return _build(items, ipv, pc)
    if len(cks) <= 5:
        ci, cs, cpv = [], set(), {}
        for rk in items:
            for ck in cks:
                if (rk,ck) not in data: continue
                c = f"{rk}_{ck}"
                if c not in cs: ci.append(c); cs.add(c)
                cpv[c] = data[(rk,ck)]
        return _build(ci, cpv, pc)
    ipv = {}
    for rk in items:
        pv = {}
        for p in pc:
            vals = [data.get((rk,ck),{}).get(p,"") for ck in cks]
            vals = [v for v in vals if v]
            if vals: pv[p] = " | ".join(vals)
        if pv: ipv[rk] = pv
    return _build(items, ipv, pc)


def _build(items, ipv, pc):
    if not items: return None
    ps = {}
    for item in items:
        for p in ipv.get(item, {}):
            ps.setdefault(p, set()).add(item)
    if len(ps) >= 2:
        sl = list(ps.values())
        tot, pairs = 0, 0
        for i in range(len(sl)):
            for j in range(i+1, min(i+4, len(sl))):
                u = len(sl[i]|sl[j]); inter = len(sl[i]&sl[j])
                if u: tot += inter/u; pairs += 1
        if pairs and tot/pairs < 0.3 and len(items) > 5: return None
    if len(items) > 50: return None
    used = [p for p in pc if any(p in ipv.get(i,{}) for i in items)]
    if not used: return None
    if len(used)>=3 and len(items)>15:
        t = len(items)*len(used)
        f = sum(1 for i in items for p in used if ipv.get(i,{}).get(p))
        if f/t < 0.5: return None
    rows = []
    for item in items:
        if not any(ipv.get(item,{}).get(p) for p in used): continue
        row = {"항목": item}
        for p in used: row[p] = ipv.get(item,{}).get(p)
        rows.append(row)
    if not rows: return None
    schema = {"항목": pl.Utf8}
    for p in used: schema[p] = pl.Utf8
    return pl.DataFrame(rows, schema=schema)

# ── 끝: 인라인 함수들 ──


def main():
    from dartlab import Company
    from dartlab.core.dataLoader import _dataDir

    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    stocks = [f.stem for f in files]
    meta_cols = {"chapter", "topic", "blockType", "blockOrder", "label"}

    total = 0
    e_ok = 0
    n_ok = 0
    both = 0
    nf_only = 0
    e_only = 0
    fail = 0
    errors = 0

    # topic별 집계
    topic_stats = defaultdict(lambda: {"total": 0, "existing": 0, "nf": 0, "nf_only": 0, "e_only": 0})

    t0 = time.time()

    for i, sc in enumerate(stocks):
        if (i+1) % 50 == 0:
            elapsed = time.time() - t0
            print(f"  {i+1}/{len(stocks)} ({elapsed:.0f}s) nf={n_ok} e={e_ok}")

        try:
            c = Company(sc)
            sections = c.sections
        except Exception:
            errors += 1
            continue

        table_rows = sections.filter(pl.col("blockType") == "table")
        if table_rows.is_empty():
            continue

        topics = table_rows["topic"].unique().to_list()
        period_cols = sorted([
            col for col in table_rows.columns
            if col not in meta_cols and re.match(r"\d{4}", col)
        ])

        for topic in topics:
            tt = table_rows.filter(pl.col("topic") == topic)
            total += 1
            ts = topic_stats[topic]
            ts["total"] += 1

            # 정규형
            try:
                nfs = horizontalizeTopic(tt, period_cols)
                n = len(nfs) > 0
            except Exception:
                n = False

            # 기존
            try:
                sr = c.show(topic)
                e = False
                if isinstance(sr, pl.DataFrame) and "block" in sr.columns:
                    for b in sr.filter(pl.col("type") == "table")["block"].to_list():
                        try:
                            bdf = c.show(topic, b)
                            if isinstance(bdf, pl.DataFrame) and not bdf.is_empty():
                                e = True
                                break
                        except Exception:
                            pass
            except Exception:
                e = False

            if e: e_ok += 1; ts["existing"] += 1
            if n: n_ok += 1; ts["nf"] += 1
            if e and n: both += 1
            elif n and not e: nf_only += 1; ts["nf_only"] += 1
            elif e and not n: e_only += 1; ts["e_only"] += 1
            else: fail += 1

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"283종목 전수 벤치마크 ({elapsed:.0f}s)")
    print(f"{'='*60}")
    print(f"총 topic: {total}, 에러 종목: {errors}")
    print(f"기존 성공: {e_ok} ({100*e_ok/total:.1f}%)")
    print(f"정규형 성공: {n_ok} ({100*n_ok/total:.1f}%)")
    print(f"둘 다 성공: {both}")
    print(f"정규형만 성공: {nf_only}")
    print(f"기존만 성공: {e_only}")
    print(f"둘 다 실패: {fail}")

    # 주요 topic별
    print(f"\n주요 topic별:")
    key_topics = ["dividend", "audit", "salesOrder", "employee", "companyOverview",
                  "majorHolder", "rawMaterial", "riskDerivative", "shareCapital",
                  "executivePay", "boardOfDirectors", "internalControl"]
    for t in key_topics:
        s = topic_stats[t]
        if s["total"] == 0: continue
        print(f"  {t}: 기존 {s['existing']}/{s['total']} ({100*s['existing']/s['total']:.0f}%), "
              f"정규형 {s['nf']}/{s['total']} ({100*s['nf']/s['total']:.0f}%), "
              f"NF만 {s['nf_only']}, 기존만 {s['e_only']}")


if __name__ == "__main__":
    main()
