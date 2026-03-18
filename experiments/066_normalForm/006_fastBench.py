"""실험 ID: 066-006
실험명: 정규형 단독 성공률 (기존 show 호출 없이 빠른 측정)

방법:
- sections 직접 로드 → table 블록 추출 → 정규형 수평화만 측정
- 기존 show() 비교는 생략 (속도 목적)
- 064 실험 결과와 수치 비교

실험일: 2026-03-18
"""

from __future__ import annotations

import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import polars as pl

sys.path.insert(0, "C:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")

from dartlab.engines.dart.docs.sections.tableParser import (
    splitSubtables, _headerCells, _isJunk, _dataRows, _normalizeHeader,
)
from dartlab.engines.dart.docs.sections.pipeline import sections as buildSections
from dartlab.core.dataLoader import _dataDir


# ── 인라인 정규형 로직 (004에서 복사, 최소화) ──

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

def toNF(sub,py=None):
    hc=_headerCells(sub)
    if _isJunk(hc):return NormalizedTable()
    dr=_dataRows(sub)
    if not dr:return NormalizedTable()
    headers,rows=_pmt(sub)
    unit=_eu(sub);sig=_ghs(hc)
    if not headers or not rows:return NormalizedTable(unit=unit,header_sig=sig)
    if _iudh(headers):
        if rows:headers,rows=rows[0],rows[1:]
        else:return NormalizedTable(unit=unit,header_sig=sig)
    if any(kw in " ".join(headers) for kw in _MULTI_YEAR_KW):
        return _nfMY(sub,headers,rows,py,unit,sig)
    return _nfFlat(headers,rows,unit,sig)

def _nfMY(sub,headers,rows,py,unit,sig):
    kn,ki=[],- 1
    for i,row in enumerate(rows):
        for cell in row:
            m=re.search(r"제\s*(\d+)\s*기",cell)
            if m:kn.append(int(m.group(1)))
        if kn:ki=i;break
    if not kn or py is None:
        ci=next((i for i,h in enumerate(headers) if "당기" in h and "전" not in h),1)
        tr,rks,seen=[],[],set()
        for row in rows:
            if not row or not row[0].strip():continue
            item=_ni(row[0].strip())
            if _ij(item):continue
            val=row[ci].strip() if ci<len(row) else ""
            if val and val!="-":
                if item not in seen:rks.append(item);seen.add(item)
                tr.append(Triple(item,"value",val))
        return NormalizedTable(tr,unit,"multi_year",rks,["value"],sig)
    mx=max(kn);sk=sorted(kn,reverse=True)
    k2y={k:py-mx+k for k in kn}
    tr,rks,seen,prev=[],[],set(),""
    for row in rows[ki+1:]:
        if not row or not row[0].strip():continue
        first=row[0].strip()
        if first.startswith("※"):continue
        if first in _STOCK_TYPES and prev:
            item=_ni(f"{prev}-{first}");vals=row[1:]
        elif len(row)>1 and row[1].strip() in _STOCK_TYPES:
            item=_ni(f"{first}-{row[1].strip()}");vals=row[2:];prev=first
        else:item=_ni(first);vals=row[1:];prev=first
        if _ij(item):continue
        ne=[(i,v.strip()) for i,v in enumerate(vals) if v.strip() and v.strip()!="-" and v.strip() not in _STOCK_TYPES]
        if len(ne)>=len(sk):
            tail=ne[-len(sk):]
            for idx,(_,val) in enumerate(tail):
                if k2y[sk[idx]]==py:
                    if item not in seen:rks.append(item);seen.add(item)
                    tr.append(Triple(item,"value",val))
    return NormalizedTable(tr,unit,"multi_year",rks,["value"],sig)

def _nfFlat(headers,rows,unit,sig):
    tr,rks,sr,cks=[],[],set(),[]
    for h in headers[1:]:cks.append(_ni(h) if h.strip() else f"col_{len(cks)}")
    gp=""
    for row in rows:
        if not row or not row[0].strip():continue
        raw=row[0].strip()
        if raw.startswith("※") or raw.startswith("☞"):continue
        item=_ni(raw)
        if _ij(item):continue
        values=row[1:]
        if all(not v.strip() or v.strip()=="-" for v in values) and len(values)>=2:
            gp=item;continue
        if gp:item=f"{gp}_{item}"
        if item not in sr:rks.append(item);sr.add(item)
        for i,ck in enumerate(cks):
            val=values[i].strip() if i<len(values) else ""
            if val and val!="-":tr.append(Triple(item,ck,val))
    return NormalizedTable(tr,unit,"flat",rks,cks,sig)

def _build(items,ipv,pc):
    if not items:return None
    ps={}
    for item in items:
        for p in ipv.get(item,{}):ps.setdefault(p,set()).add(item)
    if len(ps)>=2:
        sl=list(ps.values());tot,pairs=0,0
        for i in range(len(sl)):
            for j in range(i+1,min(i+4,len(sl))):
                u=len(sl[i]|sl[j]);inter=len(sl[i]&sl[j])
                if u:tot+=inter/u;pairs+=1
        if pairs and tot/pairs<0.3 and len(items)>5:return None
    if len(items)>50:return None
    used=[p for p in pc if any(p in ipv.get(i,{}) for i in items)]
    if not used:return None
    if len(used)>=3 and len(items)>15:
        t=len(items)*len(used);f=sum(1 for i in items for p in used if ipv.get(i,{}).get(p))
        if f/t<0.5:return None
    rows=[]
    for item in items:
        if not any(ipv.get(item,{}).get(p) for p in used):continue
        row={"항목":item}
        for p in used:row[p]=ipv.get(item,{}).get(p)
        rows.append(row)
    if not rows:return None
    schema={"항목":pl.Utf8}
    for p in used:schema[p]=pl.Utf8
    return pl.DataFrame(rows,schema=schema)

def hzTopic(tf,pc):
    if tf.is_empty():return []
    cd=defaultdict(lambda:defaultdict(list))
    for p in pc:
        if p not in tf.columns:continue
        py=int(re.match(r"(\d{4})",p).group()) if re.match(r"(\d{4})",p) else None
        for ri in range(tf.height):
            md=tf[p][ri]
            if md is None:continue
            for sub in splitSubtables(str(md)):
                nf=toNF(sub,py)
                if nf.triples:cd[nf.header_sig][p].append(nf)
    results=[]
    for sig,pt in cd.items():
        # type check
        my=any(t.table_type=="multi_year" for ts in pt.values() for t in ts)
        if my:
            ipv={};items=[];seen=set()
            for p,ts in pt.items():
                for t in ts:
                    if t.table_type!="multi_year":continue
                    for rk in t.row_keys_ordered:
                        if rk not in seen:items.append(rk);seen.add(rk)
                    for tr in t.triples:ipv.setdefault(tr.row_key,{}).setdefault(p,tr.value)
            items=[i for i in items if not _ij(i)]
            df=_build(items,ipv,pc)
        else:
            data=defaultdict(dict);items=[];seen=set();cks=[];sck=set()
            for p,ts in pt.items():
                for t in ts:
                    for rk in t.row_keys_ordered:
                        if rk not in seen:items.append(rk);seen.add(rk)
                    for ck in t.col_keys_ordered:
                        if ck not in sck:cks.append(ck);sck.add(ck)
                    for tr in t.triples:data[(tr.row_key,tr.col_key)][p]=tr.value
            items=[i for i in items if not _ij(i)]
            if not data:continue
            if len(cks)<=1:
                ipv={rk:pv for(rk,ck),pv in data.items() if rk in set(items)}
                df=_build(items,ipv,pc)
            elif len(cks)<=5:
                ci=[];cs=set();cpv={}
                for rk in items:
                    for ck in cks:
                        if(rk,ck) not in data:continue
                        c=f"{rk}_{ck}"
                        if c not in cs:ci.append(c);cs.add(c)
                        cpv[c]=data[(rk,ck)]
                df=_build(ci,cpv,pc)
            else:
                ipv={}
                for rk in items:
                    pv={}
                    for p in pc:
                        vals=[data.get((rk,ck),{}).get(p,"") for ck in cks]
                        vals=[v for v in vals if v]
                        if vals:pv[p]=" | ".join(vals)
                    if pv:ipv[rk]=pv
                df=_build(items,ipv,pc)
        if df is not None:results.append(df)
    return results


# ── 메인 ──

def main():
    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    meta_cols = {"chapter", "topic", "blockType", "blockOrder", "label"}
    total = 0
    nf_ok = 0
    topic_stats = defaultdict(lambda: {"total": 0, "nf": 0})
    errors = 0

    t0 = time.time()
    for i, code in enumerate(codes):
        if (i+1) % 50 == 0:
            print(f"  {i+1}/{len(codes)} ({time.time()-t0:.0f}s) nf_ok={nf_ok}/{total}")

        try:
            sec = buildSections(code)
        except Exception:
            errors += 1
            continue

        if sec is None or sec.is_empty():
            continue

        table_rows = sec.filter(pl.col("blockType") == "table")
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

            try:
                results = hzTopic(tt, period_cols)
                if results:
                    nf_ok += 1
                    ts["nf"] += 1
            except Exception:
                pass

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"정규형 단독 벤치마크 ({elapsed:.0f}s)")
    print(f"{'='*60}")
    print(f"종목: {len(codes)}, 에러: {errors}")
    print(f"총 topic: {total}")
    print(f"정규형 성공: {nf_ok} ({100*nf_ok/total:.1f}%)")

    # 기존 064 실험 결과와 비교 (STATUS.md 수치)
    # 기존: success=70,080/128,089 (54.7%)  ← 블록 단위
    # 이 실험은 topic 단위 (1 topic에 table block이 여러 개 → 하나라도 성공이면 ok)
    # 따라서 직접 비교 불가, but 방향성 확인 가능

    print(f"\n주요 topic별:")
    key = ["dividend","audit","salesOrder","employee","companyOverview",
           "majorHolder","rawMaterial","riskDerivative","shareCapital",
           "executivePay","boardOfDirectors","internalControl",
           "relatedPartyTx","shareholderMeeting","auditSystem","majorContractsAndRnd"]
    for t in key:
        s = topic_stats[t]
        if s["total"] == 0: continue
        print(f"  {t}: {s['nf']}/{s['total']} ({100*s['nf']/s['total']:.0f}%)")


if __name__ == "__main__":
    main()
