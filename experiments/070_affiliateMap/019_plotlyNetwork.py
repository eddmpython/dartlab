"""실험 ID: 019
실험명: Plotly + networkx 네트워크 시각화 프로토타입

목적:
- c.network() 데이터를 Plotly 인터랙티브 그래프로 시각화
- ego 뷰 (50~100 노드), overview 뷰 (30~40 슈퍼노드) 각각 가능한지 확인
- 사용자가 노드 hover/클릭으로 회사 정보를 볼 수 있는지 검증

가설:
1. ego 뷰 100노드 이하는 Plotly scatter + networkx layout으로 부드럽게 렌더링
2. overview 뷰 (그룹 슈퍼노드 30~40개)도 충분히 가벼움
3. 그룹별 색상, 노드 크기(degree), 엣지 방향 표현 가능

방법:
1. 삼성전자 ego 1홉 서브그래프 → networkx spring layout → Plotly scatter
2. 전체 overview (그룹 슈퍼노드) → networkx layout → Plotly scatter
3. 렌더링 속도, 인터랙티브 품질 확인

결과 (실험 후 작성):

결론:

실험일: 2026-03-19
"""

import time


def ego_chart(code: str = "005930", hops: int = 1):
    """ego 뷰 — 특정 회사 중심 서브그래프."""
    import networkx as nx
    import plotly.graph_objects as go

    from dartlab.engines.dart.affiliate import build_graph, export_ego, export_full

    t0 = time.time()
    data = build_graph(verbose=False)
    full = export_full(data)
    ego = export_ego(data, full, code, hops=hops)
    t_data = time.time() - t0

    print(f"데이터 준비: {t_data:.1f}초, 노드 {len(ego['nodes'])}개, 엣지 {len(ego['edges'])}개")

    # networkx 그래프 구축
    G = nx.DiGraph()
    for n in ego["nodes"]:
        G.add_node(n["id"], **n)
    for e in ego["edges"]:
        G.add_edge(e["source"], e["target"], **e)

    # 레이아웃
    t1 = time.time()
    pos = nx.spring_layout(G, k=2.0, iterations=50, seed=42)
    t_layout = time.time() - t1
    print(f"레이아웃: {t_layout:.3f}초")

    # 그룹별 색상
    groups = sorted(set(n.get("group", "") for n in ego["nodes"]))
    palette = [
        "#ea4647", "#3b82f6", "#22c55e", "#fb923c", "#8b5cf6",
        "#06b6d4", "#f59e0b", "#ec4899", "#64748b", "#84cc16",
        "#f43f5e", "#0ea5e9", "#a855f7", "#14b8a6", "#eab308",
    ]
    group_color = {g: palette[i % len(palette)] for i, g in enumerate(groups)}

    # 엣지 trace
    edge_x, edge_y = [], []
    for e in ego["edges"]:
        if e["source"] not in pos or e["target"] not in pos:
            continue
        x0, y0 = pos[e["source"]]
        x1, y1 = pos[e["target"]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.8, color="#cbd5e1"),
        hoverinfo="none",
        mode="lines",
    )

    # 노드 trace — 그룹별
    node_traces = []
    for g in groups:
        g_nodes = [n for n in ego["nodes"] if n.get("group") == g and n["id"] in pos]
        if not g_nodes:
            continue

        xs = [pos[n["id"]][0] for n in g_nodes]
        ys = [pos[n["id"]][1] for n in g_nodes]
        sizes = [max(8, min(40, n.get("degree", 1) * 1.5 + 5)) for n in g_nodes]
        texts = [
            f"<b>{n['label']}</b><br>"
            f"그룹: {n.get('group', '')}<br>"
            f"업종: {n.get('industry', '')}<br>"
            f"연결: {n.get('degree', 0)}"
            for n in g_nodes
        ]
        labels = [n["label"] for n in g_nodes]

        # center 노드 강조
        symbols = []
        for n in g_nodes:
            if n["id"] == code:
                symbols.append("star")
            elif n.get("type") == "person":
                symbols.append("diamond")
            else:
                symbols.append("circle")

        trace = go.Scatter(
            x=xs, y=ys,
            mode="markers+text",
            name=g or "독립",
            text=labels,
            textposition="top center",
            textfont=dict(size=9),
            hovertext=texts,
            hoverinfo="text",
            marker=dict(
                size=sizes,
                color=group_color.get(g, "#94a3b8"),
                symbol=symbols,
                line=dict(width=1, color="white"),
            ),
        )
        node_traces.append(trace)

    # Figure 조립
    center_name = data["code_to_name"].get(code, code)
    fig = go.Figure(
        data=[edge_trace] + node_traces,
        layout=go.Layout(
            title=dict(text=f"{center_name} 관계 네트워크", font=dict(size=16)),
            showlegend=True,
            hovermode="closest",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=20, r=20, t=50, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            font_family="Pretendard, -apple-system, sans-serif",
        ),
    )

    t_total = time.time() - t0
    print(f"총 시간: {t_total:.1f}초")
    return fig


def overview_chart():
    """overview 뷰 — 그룹 슈퍼노드."""
    import networkx as nx
    import plotly.graph_objects as go

    from dartlab.engines.dart.affiliate import (
        build_graph,
        export_full,
        export_overview,
    )

    t0 = time.time()
    data = build_graph(verbose=False)
    full = export_full(data)
    overview = export_overview(data, full)
    t_data = time.time() - t0

    print(f"데이터 준비: {t_data:.1f}초, 노드 {len(overview['nodes'])}개, 엣지 {len(overview['edges'])}개")

    # networkx
    G = nx.Graph()
    for n in overview["nodes"]:
        G.add_node(n["id"], **n)
    for e in overview["edges"]:
        G.add_edge(e["source"], e["target"], weight=e["weight"])

    pos = nx.spring_layout(G, k=3.0, iterations=80, seed=42, weight="weight")

    # 엣지
    edge_x, edge_y, edge_widths = [], [], []
    for e in overview["edges"]:
        if e["source"] not in pos or e["target"] not in pos:
            continue
        x0, y0 = pos[e["source"]]
        x1, y1 = pos[e["target"]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color="#cbd5e1"),
        hoverinfo="none",
        mode="lines",
    )

    # 노드
    xs = [pos[n["id"]][0] for n in overview["nodes"] if n["id"] in pos]
    ys = [pos[n["id"]][1] for n in overview["nodes"] if n["id"] in pos]
    nodes_in_pos = [n for n in overview["nodes"] if n["id"] in pos]
    sizes = [max(15, min(80, n["memberCount"] * 3)) for n in nodes_in_pos]
    texts = [
        f"<b>{n['label']}</b><br>"
        f"계열사: {n['memberCount']}개<br>"
        f"총 연결: {n['totalDegree']}"
        for n in nodes_in_pos
    ]
    labels = [n["label"] for n in nodes_in_pos]

    node_trace = go.Scatter(
        x=xs, y=ys,
        mode="markers+text",
        text=labels,
        textposition="top center",
        textfont=dict(size=10),
        hovertext=texts,
        hoverinfo="text",
        marker=dict(
            size=sizes,
            color=[f"hsl({i * 360 // len(nodes_in_pos)}, 60%, 55%)" for i in range(len(nodes_in_pos))],
            line=dict(width=1.5, color="white"),
        ),
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=dict(text="한국 상장사 그룹 관계 지도", font=dict(size=16)),
            showlegend=False,
            hovermode="closest",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=20, r=20, t=50, b=20),
            font_family="Pretendard, -apple-system, sans-serif",
        ),
    )

    t_total = time.time() - t0
    print(f"총 시간: {t_total:.1f}초")
    return fig


if __name__ == "__main__":
    print("=" * 50)
    print("1) 삼성전자 ego 뷰")
    print("=" * 50)
    fig1 = ego_chart("005930")
    n1 = sum(1 for t in fig1.data if hasattr(t, 'marker'))
    print(f"  traces: {len(fig1.data)}")

    print()
    print("=" * 50)
    print("2) Overview 뷰")
    print("=" * 50)
    fig2 = overview_chart()
    print(f"  traces: {len(fig2.data)}")

    print()
    print("=" * 50)
    print("3) 현대차 ego 뷰")
    print("=" * 50)
    fig3 = ego_chart("005380")

    # 브라우저에서 열기
    fig1.show()
    fig2.show()
