"""디버그: 006의 toNF + hzTopic 전체 파이프라인을 삼성전자 dividend에서 실행."""
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field

import polars as pl

sys.path.insert(0, "C:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")

from dartlab.engines.company.dart.docs.sections.pipeline import sections as buildSections
from dartlab.engines.company.dart.docs.sections.tableParser import (
    _dataRows,
    _headerCells,
    _isJunk,
    _normalizeHeader,
    splitSubtables,
)

# ── 006 인라인 함수 그대로 복사 ──
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
    unit: str|None = None
    table_type: str = "flat"
    row_keys_ordered: list[str] = field(default_factory=list)
    col_keys_ordered: list[str] = field(default_factory=list)
    header_sig: str = ""

def _ni(name):
    name = re.sub(r"\s+","",name).replace("（","(").replace("）",")").replace("ㆍ","·")
    name = _SUFFIX_RE.sub("",name).strip()
    name = _NOTE_REF_RE.sub("",name).strip()
    m = _KISU_RE.search(name)
    return m.group(2) if m else name

def _ij(name):
    s = re.sub(r"[,.\-\s]","",name)
    return s.isdigit() or not s

def _eu(lines):
    m = re.search(r"\(\s*단위\s*:\s*([^)]+)\)","\n".join(lines))
    return m.group(1).strip() if m else None

def _iudh(cells):
    h = " ".join(c.strip() for c in cells).strip()
    return bool(_UNIT_RE.match(h) or _DATE_RE.match(h)) if h else False

def _ghs(hc):
    h = _normalizeHeader(hc)
    h = _PERIOD_KW_RE.sub("",h)
    h = re.sub(r"\| *\|","|",h)
    return re.sub(r"\s+"," ",h).strip()

def _pmt(lines):
    headers,rows,sep=[],[],False
    for line in lines:
        cells=[c.strip() for c in line.strip().strip("|").split("|")]
        if all(set(c.strip())<=set("-:") for c in cells if c.strip()):
            sep=True;continue
        if not sep:
            if not headers:headers=list(cells)
        else:rows.append(cells)
    return headers,rows

def toNF(sub, py=None):
    hc = _headerCells(sub)
    if _isJunk(hc):
        return NormalizedTable(), "junk_header"
    dr = _dataRows(sub)
    if not dr:
        return NormalizedTable(), "no_data_rows"
    headers, rows = _pmt(sub)
    unit = _eu(sub)
    sig = _ghs(hc)
    if not headers or not rows:
        return NormalizedTable(unit=unit, header_sig=sig), "no_headers_or_rows"
    if _iudh(headers):
        if rows:
            headers, rows = rows[0], rows[1:]
        else:
            return NormalizedTable(unit=unit, header_sig=sig), "unit_header_no_rows"

    is_my = any(kw in " ".join(headers) for kw in _MULTI_YEAR_KW)
    if is_my:
        # 기수 찾기
        kn, ki = [], -1
        for i, row in enumerate(rows):
            for cell in row:
                m = re.search(r"제\s*(\d+)\s*기", cell)
                if m: kn.append(int(m.group(1)))
            if kn: ki = i; break

        if not kn or py is None:
            ci = next((i for i,h in enumerate(headers) if "당기" in h and "전" not in h), 1)
            tr, rks, seen = [], [], set()
            for row in rows:
                if not row or not row[0].strip(): continue
                item = _ni(row[0].strip())
                if _ij(item): continue
                val = row[ci].strip() if ci < len(row) else ""
                if val and val != "-":
                    if item not in seen: rks.append(item); seen.add(item)
                    tr.append(Triple(item, "value", val))
            return NormalizedTable(tr, unit, "multi_year", rks, ["value"], sig), f"my_no_kisu(triples={len(tr)})"

        mx = max(kn); sk = sorted(kn, reverse=True)
        k2y = {k: py - mx + k for k in kn}
        tr, rks, seen, prev = [], [], set(), ""
        for row in rows[ki+1:]:
            if not row or not row[0].strip(): continue
            first = row[0].strip()
            if first.startswith("※"): continue
            if first in _STOCK_TYPES and prev:
                item = _ni(f"{prev}-{first}"); vals = row[1:]
            elif len(row) > 1 and row[1].strip() in _STOCK_TYPES:
                item = _ni(f"{first}-{row[1].strip()}"); vals = row[2:]; prev = first
            else:
                item = _ni(first); vals = row[1:]; prev = first
            if _ij(item): continue
            ne = [(i,v.strip()) for i,v in enumerate(vals)
                  if v.strip() and v.strip() != "-" and v.strip() not in _STOCK_TYPES]
            if len(ne) >= len(sk):
                tail = ne[-len(sk):]
                for idx, (_, val) in enumerate(tail):
                    if k2y[sk[idx]] == py:
                        if item not in seen: rks.append(item); seen.add(item)
                        tr.append(Triple(item, "value", val))
        return NormalizedTable(tr, unit, "multi_year", rks, ["value"], sig), f"multi_year(triples={len(tr)})"

    # flat
    tr, rks, sr, cks = [], [], set(), []
    for h in headers[1:]:
        cks.append(_ni(h) if h.strip() else f"col_{len(cks)}")
    gp = ""
    for row in rows:
        if not row or not row[0].strip(): continue
        raw = row[0].strip()
        if raw.startswith("※") or raw.startswith("☞"): continue
        item = _ni(raw)
        if _ij(item): continue
        values = row[1:]
        if all(not v.strip() or v.strip() == "-" for v in values) and len(values) >= 2:
            gp = item; continue
        if gp: item = f"{gp}_{item}"
        if item not in sr: rks.append(item); sr.add(item)
        for i, ck in enumerate(cks):
            val = values[i].strip() if i < len(values) else ""
            if val and val != "-":
                tr.append(Triple(item, ck, val))
    return NormalizedTable(tr, unit, "flat", rks, cks, sig), f"flat(triples={len(tr)})"


# ── 테스트 ──
code = "005930"
sec = buildSections(code)
meta_cols = {"chapter", "topic", "blockType", "blockOrder", "label"}
table_rows = sec.filter(pl.col("blockType") == "table")
period_cols = sorted([
    col for col in table_rows.columns
    if col not in meta_cols and re.match(r"\d{4}", col)
])

topic = "dividend"
tt = table_rows.filter(pl.col("topic") == topic)

print(f"dividend: {tt.height} rows")

cd = defaultdict(lambda: defaultdict(list))
for p in period_cols[-3:]:
    if p not in tt.columns: continue
    py = int(re.match(r"(\d{4})", p).group()) if re.match(r"(\d{4})", p) else None
    for ri in range(tt.height):
        md = tt[p][ri]
        if md is None: continue
        for sub in splitSubtables(str(md)):
            nf, reason = toNF(sub, py)
            print(f"  {p} ri={ri}: {reason}, triples={len(nf.triples)}, sig='{nf.header_sig[:30]}'")
            if nf.triples:
                cd[nf.header_sig][p].append(nf)

print(f"\n클러스터: {len(cd)}")
for sig, pt in cd.items():
    periods = list(pt.keys())
    total_t = sum(len(t.triples) for ts in pt.values() for t in ts)
    print(f"  sig='{sig[:40]}': {len(periods)} periods, {total_t} triples")

    # 수평화 시도
    my = any(t.table_type == "multi_year" for ts in pt.values() for t in ts)
    if my:
        ipv = {}; items = []; seen = set()
        for p, ts in pt.items():
            for t in ts:
                if t.table_type != "multi_year": continue
                for rk in t.row_keys_ordered:
                    if rk not in seen: items.append(rk); seen.add(rk)
                for tr in t.triples:
                    ipv.setdefault(tr.row_key, {}).setdefault(p, tr.value)
        items = [i for i in items if not _ij(i)]
        print(f"    multi_year items: {len(items)}")
        if items:
            # overlap check
            ps = {}
            for item in items:
                for p in ipv.get(item, {}):
                    ps.setdefault(p, set()).add(item)
            if len(ps) >= 2:
                sl = list(ps.values()); tot, pairs = 0, 0
                for i in range(len(sl)):
                    for j in range(i+1, min(i+4, len(sl))):
                        u = len(sl[i]|sl[j]); inter = len(sl[i]&sl[j])
                        if u: tot += inter/u; pairs += 1
                avg = tot/pairs if pairs else 0
                print(f"    Jaccard: {avg:.3f}, items > 50: {len(items) > 50}")
            used = [p for p in period_cols[-3:] if any(p in ipv.get(i,{}) for i in items)]
            print(f"    used periods: {len(used)}")
    else:
        data = defaultdict(dict); items = []; seen = set(); cks = []; sck = set()
        for p, ts in pt.items():
            for t in ts:
                for rk in t.row_keys_ordered:
                    if rk not in seen: items.append(rk); seen.add(rk)
                for ck in t.col_keys_ordered:
                    if ck not in sck: cks.append(ck); sck.add(ck)
                for tr in t.triples: data[(tr.row_key, tr.col_key)][p] = tr.value
        items = [i for i in items if not _ij(i)]
        print(f"    flat items: {len(items)}, col_keys: {len(cks)}")
