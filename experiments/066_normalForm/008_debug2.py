"""핵심 디버그: hzTopic 내부에서 무엇이 실패하는지."""
import re, sys
from collections import defaultdict
from dataclasses import dataclass, field
import polars as pl

sys.path.insert(0, "C:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")

from dartlab.engines.company.dart.docs.sections.tableParser import (
    splitSubtables, _headerCells, _isJunk, _dataRows, _normalizeHeader,
)
from dartlab.engines.company.dart.docs.sections.pipeline import sections as buildSections

# ── 006에서 복사한 인라인 함수들 (필요 최소) ──
_MULTI_YEAR_KW = {"당기", "전기", "전전기", "당반기", "전반기", "당분기", "전분기"}
_STOCK_TYPES = {"보통주", "우선주", "기타주식"}
_KISU_RE = re.compile(r"제\s*(\d+)\s*기\s*(?:\d*분기|반기|말)?\s*\(?(당기|전기|전전기|당반기|전반기|당분기|전분기)\)?")
_SUFFIX_RE = re.compile(r"(사업)?부문$")
_NOTE_REF_RE = re.compile(r"\(\*\d*(?:,\d+)*\)")
_UNIT_RE = re.compile(r"^[\[\(（<]?\s*(?:단위|원화단위|외화단위|금액단위)\s*[:：/]?\s*[^\]）)>]*[\]）)>]?\s*$")
_PERIOD_KW_RE = re.compile(r"\d*분기|반기|당기|전기|전전기|당반기|전반기|당분기|전분기|당기말|전기말")

def _ni(name):
    name = re.sub(r"\s+","",name).replace("（","(").replace("）",")").replace("ㆍ","·")
    name = _SUFFIX_RE.sub("",name).strip()
    name = _NOTE_REF_RE.sub("",name).strip()
    m = _KISU_RE.search(name)
    return m.group(2) if m else name

def _ij(name):
    s = re.sub(r"[,.\-\s]","",name)
    return s.isdigit() or not s

def _iudh(cells):
    h = " ".join(c.strip() for c in cells).strip()
    return bool(_UNIT_RE.match(h)) if h else False

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

# 수동으로 hzTopic 실행
print(f"topic={topic}, rows={tt.height}, periods={len(period_cols)}")

cd = defaultdict(lambda: defaultdict(list))
total_triples = 0
total_subs = 0

for p in period_cols[-3:]:  # 최근 3기간만
    if p not in tt.columns:
        continue
    py = int(re.match(r"(\d{4})", p).group()) if re.match(r"(\d{4})", p) else None

    for ri in range(tt.height):
        md = tt[p][ri]
        if md is None:
            continue

        for sub in splitSubtables(str(md)):
            total_subs += 1
            hc = _headerCells(sub)
            if _isJunk(hc):
                continue
            dr = _dataRows(sub)
            if not dr:
                continue

            headers, rows = _pmt(sub)
            if not headers or not rows:
                continue

            sig = _ghs(hc)

            # 단위 헤더 체크
            if _iudh(headers):
                print(f"  {p} ri={ri}: 단위 헤더 감지: {headers}")
                if rows:
                    headers = rows[0]
                    rows = rows[1:]

            is_my = any(kw in " ".join(headers) for kw in _MULTI_YEAR_KW)

            # 트리플 생성 시뮬레이션
            if is_my:
                # 기수 찾기
                kn = []
                for i, row in enumerate(rows):
                    for cell in row:
                        m = re.search(r"제\s*(\d+)\s*기", cell)
                        if m:
                            kn.append(int(m.group(1)))
                    if kn:
                        break

                # 당기 추출
                if kn and py:
                    mx = max(kn)
                    sk = sorted(kn, reverse=True)
                    k2y = {k: py - mx + k for k in kn}

                    triple_count = 0
                    for row in rows[len(kn) > 0 and 1 or 0:]:
                        if not row or not row[0].strip():
                            continue
                        item = _ni(row[0].strip())
                        if _ij(item):
                            continue
                        vals = row[1:]
                        ne = [(i, v.strip()) for i, v in enumerate(vals)
                              if v.strip() and v.strip() != "-" and v.strip() not in _STOCK_TYPES]
                        if len(ne) >= len(sk):
                            tail = ne[-len(sk):]
                            for idx, (_, val) in enumerate(tail):
                                if k2y[sk[idx]] == py:
                                    triple_count += 1
                    total_triples += triple_count
                    print(f"  {p} ri={ri}: multi_year sig='{sig[:30]}' kisu={kn} py={py} triples={triple_count}")
                else:
                    print(f"  {p} ri={ri}: multi_year 기수 없음 kn={kn} py={py}")
            else:
                # flat
                cks = [_ni(h) if h.strip() else f"col_{i}" for i, h in enumerate(headers[1:])]
                triple_count = 0
                for row in rows:
                    if not row or not row[0].strip():
                        continue
                    item = _ni(row[0].strip())
                    if _ij(item):
                        continue
                    for i, ck in enumerate(cks):
                        val = row[1+i].strip() if 1+i < len(row) else ""
                        if val and val != "-":
                            triple_count += 1
                total_triples += triple_count
                print(f"  {p} ri={ri}: flat sig='{sig[:30]}' cks={cks[:3]} triples={triple_count}")

print(f"\n총: {total_subs} subs, {total_triples} triples")
