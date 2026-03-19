"""vis.js 네트워크 시각화 — 브라우저에서 인터랙티브 관계 지도.

DartLab 브랜딩 (다크 기본, #ea4647 primary), vis-network CDN,
forceAtlas2Based 물리 엔진.

사용법::

    import dartlab

    # 전체 시장 관계 지도
    dartlab.network().show()

    # 특정 회사 ego 뷰
    c = dartlab.Company("005930")
    c.network().show()              # ego 1홉
    c.network(hops=2).show()        # ego 2홉

plotly, networkx, scipy는 optional dependency (charts extra).
vis-network은 CDN으로 로드하므로 별도 설치 불필요.
"""

from __future__ import annotations

import base64
import json
import tempfile
import webbrowser
from pathlib import Path

# ── DartLab 브랜드 색상 ──

_BRAND = {
    "primary": "#ea4647",
    "primaryDark": "#c83232",
    "accent": "#fb923c",
    "bgDark": "#050811",
    "bgDarker": "#030509",
    "bgCard": "#0f1219",
    "bgCardHover": "#1a1f2b",
    "text": "#f1f5f9",
    "textMuted": "#94a3b8",
    "textDim": "#64748b",
    "border": "#1e2433",
    "success": "#34d399",
    "warning": "#fbbf24",
}

_GROUP_PALETTE = [
    "#3b82f6",
    "#22c55e",
    "#f59e0b",
    "#ef4444",
    "#8b5cf6",
    "#06b6d4",
    "#ec4899",
    "#f97316",
    "#14b8a6",
    "#6366f1",
    "#84cc16",
    "#e11d48",
    "#0ea5e9",
    "#a855f7",
    "#d97706",
    "#059669",
    "#7c3aed",
    "#dc2626",
    "#0891b2",
    "#c026d3",
]

_EDGE_COLORS = {"investment": "#3b82f6", "shareholder": "#22c55e"}
_EDGE_LABELS = {"investment": "출자", "shareholder": "지분보유"}


# ── favicon base64 ──


def _favicon_b64() -> str:
    """landing/static/favicon.png → base64 data URI."""
    # 모듈 위치 기준 상대 경로로 찾기
    candidates = [
        Path(__file__).resolve().parents[3] / "landing" / "static" / "favicon.png",
        Path(__file__).resolve().parents[2] / "landing" / "static" / "favicon.png",
    ]
    for p in candidates:
        if p.exists():
            data = p.read_bytes()
            return "data:image/png;base64," + base64.b64encode(data).decode()
    return ""


# ── 데이터 변환 ──


def _group_color_map(nodes: list[dict]) -> dict[str, str]:
    groups = sorted({n.get("group", "") for n in nodes if n.get("type") == "company"})
    return {g: _GROUP_PALETTE[i % len(_GROUP_PALETTE)] for i, g in enumerate(groups)}


def _prepare_vis_data(
    nodes: list[dict],
    edges: list[dict],
    group_colors: dict[str, str],
    center_id: str | None = None,
) -> tuple[list[dict], list[dict]]:
    """export_full/export_ego → vis.js 노드/엣지."""
    label_map = {n["id"]: n.get("label", n["id"]) for n in nodes}

    vis_nodes = []
    for n in nodes:
        if n.get("type") == "person":
            continue
        group = n.get("group", "")
        color = group_colors.get(group, "#475569")
        degree = n.get("degree", 1)
        is_center = (n["id"] == center_id) if center_id else False

        vis_nodes.append(
            {
                "id": n["id"],
                "label": n.get("label", n["id"]),
                "value": max(3, degree * 1.5),
                "color": {
                    "background": _BRAND["accent"] if is_center else color,
                    "border": _BRAND["primaryDark"] if is_center else color,
                    "highlight": {
                        "background": _BRAND["primary"] if is_center else color,
                        "border": _BRAND["primaryDark"] if is_center else color,
                    },
                },
                "font": {"size": 14 if is_center else 10},
                "groupName": group,
                "meta": {
                    "name": n.get("label", n["id"]),
                    "code": n["id"],
                    "group": group,
                    "industry": n.get("industry", ""),
                    "market": n.get("market", ""),
                    "degree": n.get("degree"),
                    "inDegree": n.get("inDegree"),
                    "outDegree": n.get("outDegree"),
                },
            }
        )

    node_ids = {n["id"] for n in vis_nodes}
    vis_edges = []
    for i, e in enumerate(edges):
        if e.get("type") == "person_shareholder":
            continue
        if e["source"] not in node_ids or e["target"] not in node_ids:
            continue
        pct = e.get("ownershipPct")
        width = 0.8 + (pct / 25 if pct else 0)

        vis_edges.append(
            {
                "id": f"e_{i}",
                "from": e["source"],
                "to": e["target"],
                "width": min(width, 4),
                "color": {
                    "color": _EDGE_COLORS.get(e.get("type", ""), "#94a3b8"),
                    "opacity": 0.25,
                },
                "meta": {
                    "sourceName": label_map.get(e["source"], e["source"]),
                    "targetName": label_map.get(e["target"], e["target"]),
                    "type": _EDGE_LABELS.get(e.get("type", ""), e.get("type", "")),
                    "purpose": e.get("purpose", ""),
                    "ownershipPct": pct,
                },
            }
        )

    return vis_nodes, vis_edges


# ── HTML 생성 ──


def _build_html(
    nodes_json: str,
    edges_json: str,
    title: str,
    *,
    center_id: str | None = None,
    node_count: int = 0,
) -> str:
    is_large = node_count > 300
    favicon = _favicon_b64()
    b = _BRAND

    return f"""<!DOCTYPE html>
<html lang="ko" data-theme="dark">
<head>
<meta charset="UTF-8">
<title>{title} — DartLab</title>
{f'<link rel="icon" href="{favicon}">' if favicon else ""}
<script src="https://cdn.jsdelivr.net/npm/vis-network@9/dist/vis-network.min.js"></script>
<style>
:root[data-theme="dark"] {{
    --bg: {b["bgDark"]}; --bg-surface: {b["bgCard"]}; --bg-elevated: {b["bgCardHover"]};
    --border: {b["border"]}; --text: {b["text"]}; --text-sec: {b["textMuted"]};
    --text-dim: {b["textDim"]}; --primary: {b["primary"]}; --accent: {b["accent"]};
    --shadow: rgba(0,0,0,0.4); --highlight: rgba(234,70,71,0.1);
    --node-font: {b["text"]}; --node-stroke: {b["bgDark"]};
}}
:root[data-theme="light"] {{
    --bg: #ffffff; --bg-surface: #f9fafb; --bg-elevated: #ffffff;
    --border: #e5e7eb; --text: #18181b; --text-sec: #52525b;
    --text-dim: #94a3b8; --primary: {b["primary"]}; --accent: {b["accent"]};
    --shadow: rgba(0,0,0,0.08); --highlight: rgba(234,70,71,0.06);
    --node-font: #18181b; --node-stroke: #ffffff;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Pretendard', system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); overflow: hidden; }}

#header {{
    display: flex; align-items: center; gap: 10px;
    padding: 8px 14px; background: var(--bg-surface); border-bottom: 1px solid var(--border);
    z-index: 20; position: relative;
}}
.logo {{ display: flex; align-items: center; gap: 6px; text-decoration: none; }}
.logo-icon {{ width: 20px; height: 20px; background: var(--primary); border-radius: 5px;
    display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 800; color: #fff; }}
.logo-text {{ font-size: 13px; font-weight: 700; color: var(--text); letter-spacing: -0.3px; }}
.logo-sep {{ color: var(--text-dim); font-size: 12px; margin: 0 2px; }}
#title {{ font-size: 13px; font-weight: 500; color: var(--text-sec); }}

#searchWrap {{ position: relative; flex: 1; max-width: 300px; margin-left: auto; }}
#searchInput {{
    width: 100%; padding: 5px 10px 5px 28px; border: 1px solid var(--border);
    border-radius: 6px; background: var(--bg-elevated); color: var(--text);
    font-size: 11px; outline: none;
}}
#searchInput::placeholder {{ color: var(--text-dim); }}
#searchInput:focus {{ border-color: var(--primary); box-shadow: 0 0 0 2px rgba(234,70,71,0.15); }}
#searchIcon {{ position: absolute; left: 8px; top: 50%; transform: translateY(-50%); color: var(--text-dim); font-size: 12px; pointer-events: none; }}
#searchResults {{
    display: none; position: absolute; top: 100%; left: 0; right: 0;
    background: var(--bg-elevated); border: 1px solid var(--border); border-radius: 6px;
    margin-top: 2px; max-height: 220px; overflow-y: auto; z-index: 100;
    box-shadow: 0 4px 12px var(--shadow);
}}
.sr-item {{ padding: 6px 10px; cursor: pointer; font-size: 11px; display: flex; justify-content: space-between; }}
.sr-item:hover {{ background: var(--highlight); }}
.sr-name {{ font-weight: 500; }}
.sr-code {{ color: var(--text-dim); font-size: 10px; margin-left: 4px; }}
.sr-group {{ color: var(--text-dim); font-size: 10px; }}

.hdr-right {{ display: flex; align-items: center; gap: 6px; }}
#stats {{ font-size: 10px; color: var(--text-dim); white-space: nowrap; }}
.icon-btn {{
    width: 28px; height: 28px; border: 1px solid var(--border); border-radius: 6px;
    background: var(--bg-elevated); cursor: pointer; font-size: 12px;
    display: flex; align-items: center; justify-content: center; color: var(--text-dim);
}}
.icon-btn:hover {{ color: var(--text); border-color: var(--text-sec); }}

#network {{ width: 100vw; height: calc(100vh - 41px); background: var(--bg); }}

/* 좌측 패널 */
#panel {{
    position: fixed; top: 52px; left: 10px; width: 200px;
    background: var(--bg-elevated); border: 1px solid var(--border); border-radius: 8px;
    z-index: 10; box-shadow: 0 2px 8px var(--shadow); overflow: hidden;
    max-height: calc(100vh - 70px);
}}
#panelHead {{ padding: 10px 12px 6px; display: flex; align-items: baseline; gap: 6px; }}
#panelHead .cnt {{ font-size: 20px; font-weight: 700; }}
#panelHead .lbl {{ font-size: 10px; color: var(--text-dim); }}
.pdiv {{ height: 1px; background: var(--border); margin: 0 12px; }}
#groupList {{ padding: 6px 8px; max-height: 50vh; overflow-y: auto; }}
.gi {{
    display: flex; align-items: center; gap: 6px; padding: 3px 5px;
    border-radius: 5px; cursor: pointer; font-size: 10px;
}}
.gi:hover {{ background: var(--highlight); }}
.gi.active {{ background: var(--highlight); font-weight: 600; }}
.gi-dot {{ width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }}
.gi-name {{ flex: 1; color: var(--text-sec); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.gi-cnt {{ color: var(--text-dim); font-size: 9px; min-width: 16px; text-align: right; }}
#edgeLegend {{ padding: 6px 12px 10px; display: flex; flex-direction: column; gap: 3px; }}
.el-item {{ display: flex; align-items: center; gap: 5px; font-size: 9px; color: var(--text-dim); }}
.el-line {{ width: 16px; height: 2px; border-radius: 1px; }}

/* 줌 컨트롤 */
#controls {{
    position: fixed; bottom: 14px; right: 14px; display: flex; gap: 3px; z-index: 10;
}}
#controls button {{
    width: 28px; height: 28px; border: 1px solid var(--border); border-radius: 50%;
    background: var(--bg-elevated); cursor: pointer; font-size: 13px;
    display: flex; align-items: center; justify-content: center;
    color: var(--text-dim); box-shadow: 0 1px 3px var(--shadow);
}}
#controls button:hover {{ color: var(--text); border-color: var(--text-sec); }}

/* 툴팁 */
#tooltip {{
    display: none; position: fixed; background: var(--bg-elevated); border: 1px solid var(--border);
    border-radius: 8px; padding: 10px 12px; box-shadow: 0 4px 16px var(--shadow);
    z-index: 100; min-width: 180px; max-width: 260px; pointer-events: none;
}}
.tt-hd {{ display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }}
.tt-nm {{ font-weight: 600; font-size: 12px; }}
.tt-cd {{ font-size: 9px; color: var(--text-dim); }}
.tt-badge {{ font-size: 8px; padding: 1px 5px; border-radius: 3px; background: var(--highlight); color: var(--primary); }}
.tt-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 3px 10px; }}
.tt-r {{ display: flex; flex-direction: column; }}
.tt-l {{ font-size: 9px; color: var(--text-dim); }}
.tt-v {{ font-size: 11px; font-weight: 500; }}
.tt-pct {{ color: var(--primary); font-weight: 600; }}

/* 로딩 */
#loading {{
    position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
    background: var(--bg-elevated); border: 1px solid var(--border); border-radius: 10px;
    padding: 20px 28px; box-shadow: 0 4px 16px var(--shadow); z-index: 200; text-align: center;
}}
.spinner {{
    width: 24px; height: 24px; border: 3px solid var(--border);
    border-top: 3px solid var(--primary); border-radius: 50%;
    animation: spin 0.8s linear infinite; margin: 0 auto 10px;
}}
@keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}
.ld-msg {{ font-size: 11px; color: var(--text-sec); }}
.ld-pct {{ font-size: 16px; font-weight: 700; color: var(--text); margin-top: 2px; }}

::-webkit-scrollbar {{ width: 3px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 2px; }}
</style>
</head>
<body>

<div id="header">
    <div class="logo">
        <div class="logo-icon">D</div>
        <span class="logo-text">DartLab</span>
    </div>
    <span class="logo-sep">/</span>
    <span id="title">{title}</span>
    <div id="searchWrap">
        <span id="searchIcon">⌕</span>
        <input id="searchInput" type="text" placeholder="회사명 또는 종목코드 검색 (/ 키)" autocomplete="off">
        <div id="searchResults"></div>
    </div>
    <div class="hdr-right">
        <span id="stats"></span>
        <button class="icon-btn" onclick="toggleTheme()" title="다크/라이트 전환">◐</button>
    </div>
</div>

<div id="network"></div>

<div id="panel">
    <div id="panelHead"><span class="cnt" id="panelCnt">0</span><span class="lbl">그룹</span></div>
    <div class="pdiv"></div>
    <div id="groupList"></div>
    <div class="pdiv"></div>
    <div id="edgeLegend">
        <div class="el-item"><div class="el-line" style="background:#3b82f6"></div>출자 (investment)</div>
        <div class="el-item"><div class="el-line" style="background:#22c55e"></div>지분보유 (shareholder)</div>
    </div>
</div>

<div id="controls">
    <button onclick="zoomIn()" title="확대">＋</button>
    <button onclick="zoomOut()" title="축소">－</button>
    <button onclick="fitAll()" title="전체보기">◻</button>
    <button onclick="resetHighlight()" title="초기화">↺</button>
</div>

<div id="tooltip"></div>
<div id="loading"><div class="spinner"></div><div class="ld-msg">네트워크 구성 중</div><div class="ld-pct" id="ldPct">0%</div></div>

<script>
const N = {nodes_json};
const E = {edges_json};
const CID = {json.dumps(center_id)};
const BIG = {str(is_large).lower()};

const nMap = {{}};
N.forEach(n => {{ nMap[n.id] = n; }});

const container = document.getElementById('network');
const nodes = new vis.DataSet(N);
const edges = new vis.DataSet(E);
const dk = () => document.documentElement.getAttribute('data-theme') === 'dark';

const opts = {{
    nodes: {{
        shape: 'dot',
        scaling: {{ min: 8, max: 45, label: {{ enabled: true, min: 8, max: 13 }} }},
        font: {{ face: 'system-ui, sans-serif', color: dk() ? '{b["text"]}' : '#18181b', strokeWidth: 3, strokeColor: dk() ? '{b["bgDark"]}' : '#fff' }},
        borderWidth: 2,
        shadow: {{ enabled: !BIG, size: 3, x: 1, y: 1, color: 'rgba(0,0,0,0.08)' }}
    }},
    edges: {{
        arrows: {{ to: {{ enabled: true, scaleFactor: 0.4, type: 'arrow' }} }},
        smooth: {{ type: 'continuous', roundness: 0.15 }},
        color: {{ opacity: 0.25, inherit: false, color: '#94a3b8' }},
        width: 0.8
    }},
    layout: {{ improvedLayout: false }},
    physics: {{
        enabled: true, solver: 'forceAtlas2Based',
        forceAtlas2Based: {{
            gravitationalConstant: BIG ? -25 : -70,
            centralGravity: BIG ? 0.008 : 0.015,
            springLength: BIG ? 100 : 180,
            springConstant: 0.04, damping: 0.5,
            avoidOverlap: BIG ? 0.5 : 0.8
        }},
        stabilization: {{ enabled: true, iterations: BIG ? 400 : 200, updateInterval: 25, fit: true }}
    }},
    interaction: {{
        hover: true, tooltipDelay: 80, zoomView: true, dragView: true, dragNodes: true,
        hideEdgesOnDrag: BIG, hideEdgesOnZoom: BIG
    }}
}};

const net = new vis.Network(container, {{ nodes, edges }}, opts);

const ldEl = document.getElementById('loading');
net.on('stabilizationProgress', p => {{
    document.getElementById('ldPct').textContent = Math.round(p.iterations / p.total * 100) + '%';
}});
net.once('stabilizationIterationsDone', () => {{
    net.setOptions({{ physics: {{ enabled: false }} }});
    net.fit({{ animation: {{ duration: 500, easingFunction: 'easeOutQuad' }} }});
    ldEl.style.display = 'none';
    if (CID) highlightNode(CID);
}});

document.getElementById('stats').textContent = N.length + ' 노드 · ' + E.length + ' 연결';

/* ── 그룹 패널 ── */
const gc = {{}}, gcol = {{}};
N.forEach(n => {{
    const g = n.groupName || '독립';
    gc[g] = (gc[g] || 0) + 1;
    if (!gcol[g] && n.color) gcol[g] = n.color.background;
}});
const sg = Object.entries(gc).sort((a, b) => b[1] - a[1]).filter(([, c]) => c >= 2);
document.getElementById('panelCnt').textContent = sg.length;
const gl = document.getElementById('groupList');
sg.slice(0, 50).forEach(([g, c]) => {{
    const el = document.createElement('div');
    el.className = 'gi';
    el.innerHTML = '<div class="gi-dot" style="background:' + (gcol[g] || '#475569') + '"></div><span class="gi-name">' + g + '</span><span class="gi-cnt">' + c + '</span>';
    el.onclick = () => {{
        gl.querySelectorAll('.gi').forEach(x => x.classList.remove('active'));
        el.classList.add('active');
        highlightGroup(g);
    }};
    gl.appendChild(el);
}});

/* ── 검색 ── */
const sI = document.getElementById('searchInput'), sR = document.getElementById('searchResults');
sI.addEventListener('input', () => {{
    const q = sI.value.trim().toLowerCase();
    if (q.length < 1) {{ sR.style.display = 'none'; return; }}
    const m = N.filter(n => n.label.toLowerCase().includes(q) || n.id.includes(q)).slice(0, 10);
    if (!m.length) {{ sR.style.display = 'none'; return; }}
    sR.innerHTML = '';
    m.forEach(n => {{
        const el = document.createElement('div');
        el.className = 'sr-item';
        el.innerHTML = '<span><span class="sr-name">' + n.label + '</span><span class="sr-code">' + n.id + '</span></span><span class="sr-group">' + (n.groupName || '') + '</span>';
        el.onclick = () => {{ highlightNode(n.id); sR.style.display = 'none'; sI.value = n.label; }};
        sR.appendChild(el);
    }});
    sR.style.display = 'block';
}});
sI.addEventListener('keydown', e => {{ if (e.key === 'Escape') sR.style.display = 'none'; if (e.key === 'Enter') {{ const f = sR.querySelector('.sr-item'); if (f) f.click(); }} }});
document.addEventListener('click', e => {{ if (!e.target.closest('#searchWrap')) sR.style.display = 'none'; }});

/* ── 하이라이트 ── */
let hlActive = false;

function highlightNode(id) {{
    const ce = edges.get({{ filter: e => e.from === id || e.to === id }});
    const cn = new Set([id]);
    ce.forEach(e => {{ cn.add(e.from); cn.add(e.to); }});
    const nu = [], eu = [];
    N.forEach(n => {{
        const vis = cn.has(n.id);
        nu.push({{ id: n.id, opacity: vis ? 1 : 0.07, font: {{ ...n.font, color: vis ? (dk() ? '{b["text"]}' : '#18181b') : 'transparent', strokeColor: vis ? (dk() ? '{b["bgDark"]}' : '#fff') : 'transparent' }} }});
    }});
    E.forEach(e => {{
        const c = e.from === id || e.to === id;
        eu.push({{ id: e.id, color: {{ ...e.color, opacity: c ? 0.7 : 0.02 }}, width: c ? Math.max(e.width, 2) : 0.4 }});
    }});
    nodes.update(nu); edges.update(eu);
    net.selectNodes([id]);
    net.focus(id, {{ scale: 1.5, animation: {{ duration: 400, easingFunction: 'easeOutQuad' }} }});
    hlActive = true;
}}

function highlightGroup(g) {{
    const gn = new Set(N.filter(n => n.groupName === g).map(n => n.id));
    const ge = new Set(); E.forEach(e => {{ if (gn.has(e.from) && gn.has(e.to)) ge.add(e.id); }});
    const nu = [], eu = [];
    N.forEach(n => {{
        const vis = gn.has(n.id);
        nu.push({{ id: n.id, opacity: vis ? 1 : 0.05, font: {{ ...n.font, color: vis ? (dk() ? '{b["text"]}' : '#18181b') : 'transparent', strokeColor: vis ? (dk() ? '{b["bgDark"]}' : '#fff') : 'transparent' }} }});
    }});
    E.forEach(e => {{
        const c = ge.has(e.id);
        eu.push({{ id: e.id, color: {{ ...e.color, opacity: c ? 0.7 : 0.02 }}, width: c ? Math.max(e.width, 1.5) : 0.3 }});
    }});
    nodes.update(nu); edges.update(eu);
    net.fit({{ nodes: [...gn], animation: {{ duration: 400, easingFunction: 'easeOutQuad' }} }});
    hlActive = true;
}}

function resetHighlight() {{
    const nu = [], eu = [];
    N.forEach(n => {{ nu.push({{ id: n.id, opacity: 1, font: {{ ...n.font, color: dk() ? '{b["text"]}' : '#18181b', strokeColor: dk() ? '{b["bgDark"]}' : '#fff' }} }}); }});
    E.forEach(e => {{ eu.push({{ id: e.id, color: e.color, width: e.width }}); }});
    nodes.update(nu); edges.update(eu);
    net.unselectAll();
    gl.querySelectorAll('.gi').forEach(x => x.classList.remove('active'));
    hlActive = false;
}}

net.on('click', p => {{
    if (p.nodes.length > 0) highlightNode(p.nodes[0]);
    else if (hlActive) resetHighlight();
}});

/* ── 툴팁 ── */
const tt = document.getElementById('tooltip');
net.on('hoverNode', p => {{
    const n = nMap[p.node]; if (!n?.meta) return;
    const m = n.meta;
    let h = '<div class="tt-hd"><span class="tt-nm">' + m.name + '</span><span class="tt-cd">' + m.code + '</span>';
    if (m.group) h += '<span class="tt-badge">' + m.group + '</span>';
    h += '</div><div class="tt-grid">';
    if (m.industry) h += '<div class="tt-r"><span class="tt-l">업종</span><span class="tt-v">' + m.industry + '</span></div>';
    if (m.market) h += '<div class="tt-r"><span class="tt-l">시장</span><span class="tt-v">' + m.market + '</span></div>';
    if (m.degree != null) h += '<div class="tt-r"><span class="tt-l">연결</span><span class="tt-v">' + m.degree + '개</span></div>';
    if (m.outDegree != null) h += '<div class="tt-r"><span class="tt-l">출자 →</span><span class="tt-v">' + m.outDegree + '</span></div>';
    if (m.inDegree != null) h += '<div class="tt-r"><span class="tt-l">← 피출자</span><span class="tt-v">' + m.inDegree + '</span></div>';
    h += '</div>';
    tt.innerHTML = h; tt.style.display = 'block';
    tt.style.left = Math.min(p.event.center.x + 15, innerWidth - 280) + 'px';
    tt.style.top = Math.min(p.event.center.y - 10, innerHeight - 180) + 'px';
}});
net.on('blurNode', () => {{ tt.style.display = 'none'; }});
net.on('hoverEdge', p => {{
    const e = E.find(x => x.id === p.edge); if (!e?.meta) return;
    const m = e.meta;
    let h = '<div class="tt-hd"><span class="tt-nm" style="font-size:11px">' + m.sourceName + ' → ' + m.targetName + '</span></div><div class="tt-grid">';
    if (m.type) h += '<div class="tt-r"><span class="tt-l">유형</span><span class="tt-v">' + m.type + '</span></div>';
    if (m.purpose) h += '<div class="tt-r"><span class="tt-l">목적</span><span class="tt-v">' + m.purpose + '</span></div>';
    if (m.ownershipPct != null) h += '<div class="tt-r"><span class="tt-l">지분율</span><span class="tt-v tt-pct">' + m.ownershipPct.toFixed(1) + '%</span></div>';
    h += '</div>';
    tt.innerHTML = h; tt.style.display = 'block';
    tt.style.left = Math.min(p.event.center.x + 15, innerWidth - 280) + 'px';
    tt.style.top = Math.min(p.event.center.y - 10, innerHeight - 180) + 'px';
}});
net.on('blurEdge', () => {{ tt.style.display = 'none'; }});

/* ── 테마 ── */
function toggleTheme() {{
    const h = document.documentElement, nx = h.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    h.setAttribute('data-theme', nx);
    const d = nx === 'dark', fc = d ? '{b["text"]}' : '#18181b', sc = d ? '{b["bgDark"]}' : '#fff';
    const u = []; N.forEach(n => {{ u.push({{ id: n.id, font: {{ ...n.font, color: fc, strokeColor: sc }} }}); }});
    nodes.update(u);
}}

function zoomIn() {{ net.moveTo({{ scale: net.getScale() * 1.3, animation: true }}); }}
function zoomOut() {{ net.moveTo({{ scale: net.getScale() / 1.3, animation: true }}); }}
function fitAll() {{ resetHighlight(); net.fit({{ animation: true }}); }}

document.addEventListener('keydown', e => {{
    if (e.target === sI) return;
    if (e.key === 'Escape') {{ resetHighlight(); net.fit({{ animation: true }}); }}
    if (e.key === '/' || (e.key === 'f' && (e.ctrlKey || e.metaKey))) {{ e.preventDefault(); sI.focus(); }}
}});
</script>
</body>
</html>"""


# ── 공개 API ──


class NetworkView:
    """네트워크 시각화 결과 — .show()로 브라우저 오픈."""

    def __init__(self, html: str, name: str = "network") -> None:
        self._html = html
        self._name = name

    def show(self) -> Path:
        """브라우저에서 네트워크 시각화를 연다."""
        tmp = Path(tempfile.gettempdir()) / f"dartlab_{self._name}.html"
        tmp.write_text(self._html, encoding="utf-8")
        webbrowser.open(str(tmp))
        return tmp

    def save(self, path: str | Path) -> Path:
        """HTML 파일로 저장."""
        p = Path(path)
        p.write_text(self._html, encoding="utf-8")
        return p


def render_network(
    nodes: list[dict],
    edges: list[dict],
    title: str = "관계 네트워크",
    *,
    center_id: str | None = None,
) -> NetworkView:
    """export_full/export_ego 결과 → NetworkView."""
    group_colors = _group_color_map(nodes)
    vis_nodes, vis_edges = _prepare_vis_data(nodes, edges, group_colors, center_id=center_id)
    html = _build_html(
        json.dumps(vis_nodes, ensure_ascii=False),
        json.dumps(vis_edges, ensure_ascii=False),
        title,
        center_id=center_id,
        node_count=len(vis_nodes),
    )
    name = f"ego_{center_id}" if center_id else "full"
    return NetworkView(html, name)
