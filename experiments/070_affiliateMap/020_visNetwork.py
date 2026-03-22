"""실험 ID: 020
실험명: vis.js 네트워크 시각화 — DartWings 스타일

목적:
- DartWings SubsidiarySection의 vis.js 스타일을 dartlab 전체 시장 뷰로 확장
- 다크/라이트 토글, 고급 툴팁 (지분율/그룹/업종), 클릭 하이라이트, 검색창
- 하나의 뷰로 전체 시장을 보여주되 검색/클릭으로 특정 회사 포커스

가설:
1. vis.js forceAtlas2Based로 1,600+ 노드 처리 가능
2. 노드 클릭 시 연결된 관계사만 하이라이트 → 나머지 fade
3. 검색창으로 회사 찾기 → 자동 줌인 + 하이라이트

방법:
1. 전체 시장 데이터 → vis.js HTML (DartWings 색상/레이아웃 참고)
2. 다크모드, 툴팁, 하이라이트, 검색 구현
3. tempfile HTML → webbrowser.open

결과 (실험 후 작성):

결론:

실험일: 2026-03-19
"""

import json
import tempfile
import time
import webbrowser
from pathlib import Path


# ── 그룹별 색상 — DartWings 계열 ──
GROUP_PALETTE = [
    "#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6",
    "#06b6d4", "#ec4899", "#f97316", "#14b8a6", "#6366f1",
    "#84cc16", "#e11d48", "#0ea5e9", "#a855f7", "#d97706",
    "#059669", "#7c3aed", "#dc2626", "#0891b2", "#c026d3",
]


def _build_html(nodes_json: str, edges_json: str, title: str, *, center_id: str | None = None, node_count: int = 0) -> str:
    """vis.js 네트워크 HTML — DartWings 스타일."""

    is_large = node_count > 300

    return f"""<!DOCTYPE html>
<html lang="ko" data-theme="dark">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/vis-network@9/dist/vis-network.min.js"></script>
<style>
:root[data-theme="light"] {{
    --bg: #ffffff; --bg-surface: #f9fafb; --bg-elevated: #ffffff;
    --border: #e5e7eb; --text: #18181b; --text-secondary: #52525b;
    --text-muted: #a1a1aa; --ring: #3b82f6; --shadow: rgba(0,0,0,0.08);
    --node-font: #18181b; --node-stroke: #ffffff;
    --edge-default: rgba(148,163,184,0.3); --highlight-bg: rgba(59,130,246,0.08);
}}
:root[data-theme="dark"] {{
    --bg: #09090b; --bg-surface: #18181b; --bg-elevated: #27272a;
    --border: #3f3f46; --text: #fafafa; --text-secondary: #a1a1aa;
    --text-muted: #71717a; --ring: #3b82f6; --shadow: rgba(0,0,0,0.3);
    --node-font: #fafafa; --node-stroke: #18181b;
    --edge-default: rgba(148,163,184,0.15); --highlight-bg: rgba(59,130,246,0.15);
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Pretendard', system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); overflow: hidden; }}

/* ── 헤더 ── */
#header {{
    display: flex; align-items: center; gap: 12px;
    padding: 10px 16px; background: var(--bg-surface); border-bottom: 1px solid var(--border);
    position: relative; z-index: 20;
}}
#header h1 {{ font-size: 14px; font-weight: 600; white-space: nowrap; }}
#searchWrap {{
    position: relative; flex: 1; max-width: 320px;
}}
#searchInput {{
    width: 100%; padding: 6px 12px 6px 32px; border: 1px solid var(--border);
    border-radius: 8px; background: var(--bg-elevated); color: var(--text);
    font-size: 12px; outline: none;
}}
#searchInput:focus {{ border-color: var(--ring); }}
#searchIcon {{
    position: absolute; left: 10px; top: 50%; transform: translateY(-50%);
    color: var(--text-muted); font-size: 13px; pointer-events: none;
}}
#searchResults {{
    display: none; position: absolute; top: 100%; left: 0; right: 0;
    background: var(--bg-elevated); border: 1px solid var(--border); border-radius: 8px;
    margin-top: 4px; max-height: 240px; overflow-y: auto; z-index: 100;
    box-shadow: 0 4px 12px var(--shadow);
}}
.search-item {{
    padding: 8px 12px; cursor: pointer; font-size: 12px;
    display: flex; justify-content: space-between; align-items: center;
}}
.search-item:hover {{ background: var(--highlight-bg); }}
.search-item .name {{ font-weight: 500; }}
.search-item .group {{ color: var(--text-muted); font-size: 11px; }}
.headerRight {{
    display: flex; align-items: center; gap: 8px; margin-left: auto;
}}
#stats {{ font-size: 11px; color: var(--text-muted); white-space: nowrap; }}
#themeBtn {{
    width: 32px; height: 32px; border: 1px solid var(--border); border-radius: 8px;
    background: var(--bg-elevated); cursor: pointer; font-size: 14px;
    display: flex; align-items: center; justify-content: center; color: var(--text-muted);
}}
#themeBtn:hover {{ color: var(--text); border-color: var(--text-muted); }}

/* ── 네트워크 ── */
#network {{ width: 100vw; height: calc(100vh - 45px); background: var(--bg); }}

/* ── 좌측 패널 ── */
#panel {{
    position: fixed; top: 56px; left: 12px; width: 220px;
    background: var(--bg-elevated); border: 1px solid var(--border); border-radius: 10px;
    z-index: 10; box-shadow: 0 2px 8px var(--shadow); overflow: hidden;
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
}}
#panelHeader {{
    padding: 12px 14px 8px; display: flex; align-items: baseline; gap: 8px;
}}
#panelHeader .count {{ font-size: 22px; font-weight: 700; }}
#panelHeader .label {{ font-size: 11px; color: var(--text-muted); }}
.panel-divider {{ height: 1px; background: var(--border); margin: 0 14px; }}
#groupList {{
    padding: 8px 10px; max-height: 45vh; overflow-y: auto;
}}
.group-item {{
    display: flex; align-items: center; gap: 8px; padding: 4px 6px;
    border-radius: 6px; cursor: pointer; font-size: 11px;
}}
.group-item:hover {{ background: var(--highlight-bg); }}
.group-item.active {{ background: var(--highlight-bg); font-weight: 600; }}
.group-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
.group-name {{ flex: 1; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.group-cnt {{ color: var(--text-muted); font-size: 10px; min-width: 20px; text-align: right; }}

/* ── 엣지 범례 ── */
#edgeLegend {{
    padding: 8px 14px 12px; display: flex; flex-direction: column; gap: 4px;
}}
.edge-legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 10px; }}
.edge-legend-line {{ width: 20px; height: 2px; border-radius: 1px; }}

/* ── 줌 컨트롤 ── */
#controls {{
    position: fixed; bottom: 16px; right: 16px; display: flex; gap: 4px; z-index: 10;
}}
#controls button {{
    width: 32px; height: 32px; border: 1px solid var(--border); border-radius: 50%;
    background: var(--bg-elevated); cursor: pointer; font-size: 14px;
    display: flex; align-items: center; justify-content: center;
    color: var(--text-muted); box-shadow: 0 1px 3px var(--shadow);
}}
#controls button:hover {{ color: var(--text); border-color: var(--text-muted); }}

/* ── 하단 색상 범례 ── */
#bottomLegend {{
    position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%);
    display: flex; align-items: center; gap: 12px; padding: 6px 14px;
    background: var(--bg-elevated); border: 1px solid var(--border); border-radius: 20px;
    font-size: 10px; color: var(--text-muted); z-index: 10;
    box-shadow: 0 1px 3px var(--shadow);
}}
.bl-dot {{ width: 8px; height: 8px; border-radius: 50%; }}

/* ── 툴팁 ── */
#tooltip {{
    display: none; position: fixed; background: var(--bg-elevated); border: 1px solid var(--border);
    border-radius: 10px; padding: 12px 14px; box-shadow: 0 4px 16px var(--shadow);
    z-index: 100; min-width: 200px; max-width: 280px; pointer-events: none;
}}
.tt-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }}
.tt-name {{ font-weight: 600; font-size: 13px; }}
.tt-badge {{
    font-size: 9px; padding: 2px 6px; border-radius: 4px;
    background: var(--highlight-bg); color: var(--ring);
}}
.tt-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px 12px; }}
.tt-row {{ display: flex; flex-direction: column; }}
.tt-label {{ font-size: 10px; color: var(--text-muted); }}
.tt-value {{ font-size: 12px; font-weight: 500; }}

/* ── 로딩 ── */
#loading {{
    position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
    background: var(--bg-elevated); border: 1px solid var(--border); border-radius: 12px;
    padding: 24px 32px; box-shadow: 0 4px 16px var(--shadow); z-index: 200; text-align: center;
}}
.spinner {{
    width: 28px; height: 28px; border: 3px solid var(--border);
    border-top: 3px solid var(--ring); border-radius: 50%;
    animation: spin 0.8s linear infinite; margin: 0 auto 12px;
}}
@keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}
.loading-msg {{ font-size: 12px; color: var(--text-secondary); }}
.loading-pct {{ font-size: 18px; font-weight: 700; color: var(--text); margin-top: 4px; }}

/* ── 스크롤바 ── */
::-webkit-scrollbar {{ width: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 2px; }}
</style>
</head>
<body>

<div id="header">
    <h1>🔗 {title}</h1>
    <div id="searchWrap">
        <span id="searchIcon">🔍</span>
        <input id="searchInput" type="text" placeholder="회사명 또는 종목코드 검색..." autocomplete="off">
        <div id="searchResults"></div>
    </div>
    <div class="headerRight">
        <div id="stats"></div>
        <button id="themeBtn" onclick="toggleTheme()" title="다크/라이트 전환">🌓</button>
    </div>
</div>

<div id="network"></div>

<div id="panel">
    <div id="panelHeader">
        <span class="count" id="panelCount">0</span>
        <span class="label">그룹</span>
    </div>
    <div class="panel-divider"></div>
    <div id="groupList"></div>
    <div class="panel-divider"></div>
    <div id="edgeLegend">
        <div class="edge-legend-item">
            <div class="edge-legend-line" style="background: #3b82f6;"></div>
            <span>출자 (investment)</span>
        </div>
        <div class="edge-legend-item">
            <div class="edge-legend-line" style="background: #22c55e;"></div>
            <span>지분보유 (shareholder)</span>
        </div>
    </div>
</div>

<div id="controls">
    <button onclick="zoomIn()" title="확대">＋</button>
    <button onclick="zoomOut()" title="축소">－</button>
    <button onclick="fitAll()" title="전체보기">◻</button>
    <button onclick="resetHighlight()" title="초기화">↺</button>
</div>

<div id="tooltip"></div>

<div id="loading">
    <div class="spinner"></div>
    <div class="loading-msg">네트워크 구성 중</div>
    <div class="loading-pct" id="loadingPct">0%</div>
</div>

<script>
// ── 데이터 ──
const nodesData = {nodes_json};
const edgesData = {edges_json};
const centerId = {json.dumps(center_id)};
const isLarge = {str(is_large).lower()};

// ── 노드/엣지 lookup ──
const nodeMap = {{}};
nodesData.forEach(n => {{ nodeMap[n.id] = n; }});

// ── vis.js 초기화 ──
const container = document.getElementById('network');
const nodes = new vis.DataSet(nodesData);
const edges = new vis.DataSet(edgesData);

const isDark = () => document.documentElement.getAttribute('data-theme') === 'dark';

const options = {{
    nodes: {{
        shape: 'dot',
        scaling: {{ min: 8, max: 45, label: {{ enabled: true, min: 8, max: 13 }} }},
        font: {{
            face: 'system-ui, sans-serif',
            color: isDark() ? '#fafafa' : '#18181b',
            strokeWidth: 3,
            strokeColor: isDark() ? '#18181b' : '#ffffff'
        }},
        borderWidth: 2,
        shadow: {{ enabled: !isLarge, size: 3, x: 1, y: 1, color: 'rgba(0,0,0,0.08)' }}
    }},
    edges: {{
        arrows: {{ to: {{ enabled: true, scaleFactor: 0.4, type: 'arrow' }} }},
        smooth: {{ type: 'continuous', roundness: 0.15 }},
        color: {{ opacity: 0.25, inherit: false, color: '#94a3b8' }},
        width: 0.8
    }},
    layout: {{ improvedLayout: false }},
    physics: {{
        enabled: true,
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {{
            gravitationalConstant: isLarge ? -25 : -70,
            centralGravity: isLarge ? 0.008 : 0.015,
            springLength: isLarge ? 100 : 180,
            springConstant: 0.04,
            damping: 0.5,
            avoidOverlap: isLarge ? 0.5 : 0.8
        }},
        stabilization: {{
            enabled: true,
            iterations: isLarge ? 400 : 200,
            updateInterval: 25,
            fit: true
        }}
    }},
    interaction: {{
        hover: true,
        tooltipDelay: 80,
        zoomView: true,
        dragView: true,
        dragNodes: true,
        hideEdgesOnDrag: isLarge,
        hideEdgesOnZoom: isLarge
    }}
}};

const network = new vis.Network(container, {{ nodes, edges }}, options);

// ── 로딩 ──
const loadingEl = document.getElementById('loading');
network.on('stabilizationProgress', p => {{
    const pct = Math.round(p.iterations / p.total * 100);
    document.getElementById('loadingPct').textContent = pct + '%';
}});

network.once('stabilizationIterationsDone', () => {{
    network.setOptions({{ physics: {{ enabled: false }} }});
    network.fit({{ animation: {{ duration: 500, easingFunction: 'easeOutQuad' }} }});
    loadingEl.style.display = 'none';
    if (centerId) {{
        highlightNode(centerId);
    }}
}});

// ── 통계 ──
document.getElementById('stats').textContent =
    nodesData.length + ' 노드 · ' + edgesData.length + ' 연결';

// ── 그룹 패널 ──
const groupCounts = {{}};
const groupColors = {{}};
nodesData.forEach(n => {{
    const g = n.groupName || '독립';
    groupCounts[g] = (groupCounts[g] || 0) + 1;
    if (!groupColors[g] && n.color) groupColors[g] = n.color.background;
}});
const sortedGroups = Object.entries(groupCounts).sort((a, b) => b[1] - a[1]);
const multiGroups = sortedGroups.filter(([g, c]) => c >= 2);

document.getElementById('panelCount').textContent = multiGroups.length;
const groupList = document.getElementById('groupList');

multiGroups.slice(0, 50).forEach(([g, cnt]) => {{
    const item = document.createElement('div');
    item.className = 'group-item';
    item.innerHTML =
        '<div class="group-dot" style="background:' + (groupColors[g] || '#94a3b8') + '"></div>' +
        '<span class="group-name">' + g + '</span>' +
        '<span class="group-cnt">' + cnt + '</span>';
    item.onclick = () => {{
        document.querySelectorAll('.group-item').forEach(el => el.classList.remove('active'));
        item.classList.add('active');
        highlightGroup(g);
    }};
    groupList.appendChild(item);
}});

// ── 검색 ──
const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');

searchInput.addEventListener('input', () => {{
    const q = searchInput.value.trim().toLowerCase();
    if (q.length < 1) {{ searchResults.style.display = 'none'; return; }}

    const matches = nodesData
        .filter(n => n.label.toLowerCase().includes(q) || n.id.includes(q))
        .slice(0, 12);

    if (matches.length === 0) {{ searchResults.style.display = 'none'; return; }}

    searchResults.innerHTML = '';
    matches.forEach(n => {{
        const item = document.createElement('div');
        item.className = 'search-item';
        item.innerHTML = '<span class="name">' + n.label + ' <span style="color:var(--text-muted);font-size:10px;">' + n.id + '</span></span>' +
            '<span class="group">' + (n.groupName || '') + '</span>';
        item.onclick = () => {{
            highlightNode(n.id);
            searchResults.style.display = 'none';
            searchInput.value = n.label;
        }};
        searchResults.appendChild(item);
    }});
    searchResults.style.display = 'block';
}});

searchInput.addEventListener('keydown', (e) => {{
    if (e.key === 'Escape') {{ searchResults.style.display = 'none'; }}
    if (e.key === 'Enter') {{
        const first = searchResults.querySelector('.search-item');
        if (first) first.click();
    }}
}});

document.addEventListener('click', (e) => {{
    if (!e.target.closest('#searchWrap')) searchResults.style.display = 'none';
}});

// ── 하이라이트 ──
let highlightActive = false;

function highlightNode(nodeId) {{
    const connEdges = edges.get({{ filter: e => e.from === nodeId || e.to === nodeId }});
    const connNodeIds = new Set([nodeId]);
    connEdges.forEach(e => {{ connNodeIds.add(e.from); connNodeIds.add(e.to); }});

    // 노드 fade
    const updates = [];
    nodesData.forEach(n => {{
        if (connNodeIds.has(n.id)) {{
            updates.push({{
                id: n.id,
                opacity: 1,
                font: {{ ...n.font, color: isDark() ? '#fafafa' : '#18181b', strokeColor: isDark() ? '#18181b' : '#ffffff' }}
            }});
        }} else {{
            updates.push({{
                id: n.id,
                opacity: 0.08,
                font: {{ ...n.font, color: 'transparent', strokeColor: 'transparent' }}
            }});
        }}
    }});
    nodes.update(updates);

    // 엣지 fade
    const edgeUpdates = [];
    edgesData.forEach(e => {{
        const isConn = e.from === nodeId || e.to === nodeId;
        edgeUpdates.push({{
            id: e.id,
            color: {{ ...e.color, opacity: isConn ? 0.7 : 0.03 }},
            width: isConn ? Math.max(e.width, 2) : 0.5
        }});
    }});
    edges.update(edgeUpdates);

    network.selectNodes([nodeId]);
    network.focus(nodeId, {{ scale: 1.2, animation: {{ duration: 500, easingFunction: 'easeOutQuad' }} }});
    highlightActive = true;
}}

function highlightGroup(groupName) {{
    const groupNodeIds = new Set(nodesData.filter(n => n.groupName === groupName).map(n => n.id));
    const groupEdgeIds = new Set();
    edgesData.forEach(e => {{
        if (groupNodeIds.has(e.from) && groupNodeIds.has(e.to)) groupEdgeIds.add(e.id);
    }});

    const updates = [];
    nodesData.forEach(n => {{
        if (groupNodeIds.has(n.id)) {{
            updates.push({{ id: n.id, opacity: 1, font: {{ ...n.font, color: isDark() ? '#fafafa' : '#18181b', strokeColor: isDark() ? '#18181b' : '#ffffff' }} }});
        }} else {{
            updates.push({{ id: n.id, opacity: 0.06, font: {{ ...n.font, color: 'transparent', strokeColor: 'transparent' }} }});
        }}
    }});
    nodes.update(updates);

    const edgeUpdates = [];
    edgesData.forEach(e => {{
        const isIn = groupEdgeIds.has(e.id);
        edgeUpdates.push({{ id: e.id, color: {{ ...e.color, opacity: isIn ? 0.7 : 0.02 }}, width: isIn ? Math.max(e.width, 1.5) : 0.3 }});
    }});
    edges.update(edgeUpdates);

    network.fit({{ nodes: [...groupNodeIds], animation: {{ duration: 500, easingFunction: 'easeOutQuad' }} }});
    highlightActive = true;
}}

function resetHighlight() {{
    const updates = [];
    nodesData.forEach(n => {{
        updates.push({{ id: n.id, opacity: 1, font: {{ ...n.font, color: isDark() ? '#fafafa' : '#18181b', strokeColor: isDark() ? '#18181b' : '#ffffff' }} }});
    }});
    nodes.update(updates);

    const edgeUpdates = [];
    edgesData.forEach(e => {{
        edgeUpdates.push({{ id: e.id, color: e.color, width: e.width }});
    }});
    edges.update(edgeUpdates);

    network.unselectAll();
    document.querySelectorAll('.group-item').forEach(el => el.classList.remove('active'));
    highlightActive = false;
}}

// ── 네트워크 이벤트 ──
network.on('click', params => {{
    if (params.nodes.length > 0) {{
        highlightNode(params.nodes[0]);
    }} else if (highlightActive) {{
        resetHighlight();
    }}
}});

// ── 툴팁 ──
const tooltip = document.getElementById('tooltip');

network.on('hoverNode', params => {{
    const n = nodeMap[params.node];
    if (!n || !n.meta) return;
    const m = n.meta;

    let html = '<div class="tt-header"><span class="tt-name">' + m.name + '</span>';
    if (m.group) html += '<span class="tt-badge">' + m.group + '</span>';
    html += '</div><div class="tt-grid">';
    if (m.industry) html += '<div class="tt-row"><span class="tt-label">업종</span><span class="tt-value">' + m.industry + '</span></div>';
    if (m.market) html += '<div class="tt-row"><span class="tt-label">시장</span><span class="tt-value">' + m.market + '</span></div>';
    if (m.degree != null) html += '<div class="tt-row"><span class="tt-label">연결</span><span class="tt-value">' + m.degree + '개</span></div>';
    if (m.outDegree != null) html += '<div class="tt-row"><span class="tt-label">출자 →</span><span class="tt-value">' + m.outDegree + '</span></div>';
    if (m.inDegree != null) html += '<div class="tt-row"><span class="tt-label">← 피출자</span><span class="tt-value">' + m.inDegree + '</span></div>';
    html += '</div>';

    tooltip.innerHTML = html;
    tooltip.style.display = 'block';
    tooltip.style.left = Math.min(params.event.center.x + 15, window.innerWidth - 300) + 'px';
    tooltip.style.top = Math.min(params.event.center.y - 10, window.innerHeight - 200) + 'px';
}});

network.on('blurNode', () => {{ tooltip.style.display = 'none'; }});

network.on('hoverEdge', params => {{
    const edge = edgesData.find(e => e.id === params.edge);
    if (!edge || !edge.meta) return;
    const m = edge.meta;

    let html = '<div class="tt-header"><span class="tt-name" style="font-size:12px;">' + m.sourceName + ' → ' + m.targetName + '</span></div>';
    html += '<div class="tt-grid">';
    if (m.type) html += '<div class="tt-row"><span class="tt-label">유형</span><span class="tt-value">' + m.type + '</span></div>';
    if (m.purpose) html += '<div class="tt-row"><span class="tt-label">목적</span><span class="tt-value">' + m.purpose + '</span></div>';
    if (m.ownershipPct != null) html += '<div class="tt-row"><span class="tt-label">지분율</span><span class="tt-value" style="color:#3b82f6;font-weight:600;">' + m.ownershipPct.toFixed(1) + '%</span></div>';
    html += '</div>';

    tooltip.innerHTML = html;
    tooltip.style.display = 'block';
    tooltip.style.left = Math.min(params.event.center.x + 15, window.innerWidth - 300) + 'px';
    tooltip.style.top = Math.min(params.event.center.y - 10, window.innerHeight - 200) + 'px';
}});

network.on('blurEdge', () => {{ tooltip.style.display = 'none'; }});

// ── 테마 전환 ──
function toggleTheme() {{
    const html = document.documentElement;
    const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    const dark = next === 'dark';

    const fontColor = dark ? '#fafafa' : '#18181b';
    const strokeColor = dark ? '#18181b' : '#ffffff';

    const updates = [];
    nodesData.forEach(n => {{
        updates.push({{ id: n.id, font: {{ ...n.font, color: fontColor, strokeColor: strokeColor }} }});
    }});
    nodes.update(updates);
}}

// ── 줌 ──
function zoomIn() {{ network.moveTo({{ scale: network.getScale() * 1.3, animation: true }}); }}
function zoomOut() {{ network.moveTo({{ scale: network.getScale() / 1.3, animation: true }}); }}
function fitAll() {{ resetHighlight(); network.fit({{ animation: true }}); }}

// ── 키보드 ──
document.addEventListener('keydown', e => {{
    if (e.target === searchInput) return;
    if (e.key === 'Escape') {{ resetHighlight(); network.fit({{ animation: true }}); }}
    if (e.key === '/' || e.key === 'f' && (e.ctrlKey || e.metaKey)) {{
        e.preventDefault(); searchInput.focus();
    }}
}});
</script>
</body>
</html>"""


def _group_color_map(nodes: list[dict]) -> dict[str, str]:
    groups = sorted(set(n.get("group", "") for n in nodes if n.get("type") == "company"))
    return {g: GROUP_PALETTE[i % len(GROUP_PALETTE)] for i, g in enumerate(groups)}


def _prepare_vis_data(nodes: list[dict], edges: list[dict], group_colors: dict[str, str], center_id: str | None = None):
    node_label_map = {n["id"]: n.get("label", n["id"]) for n in nodes}

    vis_nodes = []
    for n in nodes:
        if n.get("type") == "person":
            continue
        group = n.get("group", "")
        color = group_colors.get(group, "#94a3b8")
        degree = n.get("degree", 1)
        is_center = n["id"] == center_id if center_id else False

        vis_nodes.append({
            "id": n["id"],
            "label": n.get("label", n["id"]),
            "value": max(3, degree * 1.5),
            "color": {
                "background": "#f59e0b" if is_center else color,
                "border": "#d97706" if is_center else color,
                "highlight": {"background": "#fbbf24" if is_center else color, "border": "#92400e" if is_center else color},
            },
            "font": {"size": 14 if is_center else 10},
            "groupName": group,
            "meta": {
                "name": n.get("label", n["id"]),
                "group": group,
                "industry": n.get("industry", ""),
                "market": n.get("market", ""),
                "degree": n.get("degree"),
                "inDegree": n.get("inDegree"),
                "outDegree": n.get("outDegree"),
            },
        })

    edge_type_colors = {"investment": "#3b82f6", "shareholder": "#22c55e"}
    edge_type_labels = {"investment": "출자", "shareholder": "지분보유"}

    node_ids = {n["id"] for n in vis_nodes}
    vis_edges = []
    for i, e in enumerate(edges):
        if e.get("type") == "person_shareholder":
            continue
        if e["source"] not in node_ids or e["target"] not in node_ids:
            continue
        pct = e.get("ownershipPct")
        width = 0.8 + (pct / 25 if pct else 0)

        vis_edges.append({
            "id": f"e_{i}",
            "from": e["source"],
            "to": e["target"],
            "width": min(width, 4),
            "color": {"color": edge_type_colors.get(e.get("type", ""), "#94a3b8"), "opacity": 0.25},
            "meta": {
                "sourceName": node_label_map.get(e["source"], e["source"]),
                "targetName": node_label_map.get(e["target"], e["target"]),
                "type": edge_type_labels.get(e.get("type", ""), e.get("type", "")),
                "purpose": e.get("purpose", ""),
                "ownershipPct": pct,
            },
        })

    return vis_nodes, vis_edges


def _open_html(html: str, name: str = "network"):
    tmp = Path(tempfile.gettempdir()) / f"dartlab_{name}.html"
    tmp.write_text(html, encoding="utf-8")
    webbrowser.open(str(tmp))
    print(f"  → {tmp}")
    return tmp


def network_view(code: str | None = None, hops: int = 1):
    """네트워크 뷰 — code 없으면 전체, 있으면 ego."""
    from dartlab.engines.company.dart.affiliate import build_graph, export_ego, export_full

    t0 = time.time()
    data = build_graph(verbose=False)
    full = export_full(data)

    if code:
        view_data = export_ego(data, full, code, hops=hops)
        center_name = data["code_to_name"].get(code, code)
        title = f"{center_name} 관계 네트워크"
        name = f"ego_{code}"
    else:
        view_data = full
        title = "한국 상장사 관계 네트워크"
        center_name = None
        name = "full"

    print(f"  데이터: {time.time() - t0:.1f}초, 노드 {len(view_data['nodes'])}개, 엣지 {len(view_data['edges'])}개")

    group_colors = _group_color_map(view_data["nodes"])
    vis_nodes, vis_edges = _prepare_vis_data(view_data["nodes"], view_data["edges"], group_colors, center_id=code)

    html = _build_html(
        json.dumps(vis_nodes, ensure_ascii=False),
        json.dumps(vis_edges, ensure_ascii=False),
        title,
        center_id=code,
        node_count=len(vis_nodes),
    )
    return _open_html(html, name)


if __name__ == "__main__":
    print("=" * 50)
    print("1) 전체 시장 뷰")
    print("=" * 50)
    network_view()

    print()
    print("=" * 50)
    print("2) 삼성전자 ego 뷰")
    print("=" * 50)
    network_view("005930")
