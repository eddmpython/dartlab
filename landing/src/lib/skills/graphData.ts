// Skill Graph 시각화 데이터 변환 · d3-hierarchy 트리 + d3-force simulation.
import graphPayload from '$skills/graph.json';
import * as d3 from 'd3-force';
import { hierarchy, tree } from 'd3-hierarchy';

export interface GraphNode {
	id: string;
	title: string;
	category: string;
	purpose: string;
	inDegree: number;
	outDegree: number;
	cluster: string | null;
	isEntry: boolean;
	isLeaf: boolean;
	isOrphan: boolean;
	audiences: string[];
}

export interface GraphEdge {
	src: string;
	dst: string;
	kind: 'successor' | 'predecessor' | 'linkedRecipe' | 'knowledge' | 'source';
}

export interface GraphPayload {
	nodes: GraphNode[];
	edges: GraphEdge[];
	entries: string[];
	cycles: string[][];
	orphans: string[];
	unreachable: string[];
}

export interface GraphRegion {
	id: string;
	title: string;
	x: number;
	y: number;
	width: number;
	height: number;
	count: number;
}

export const graphCategoryOrder = ['start', 'runtime', 'operation', 'engines', 'recipes'] as const;

export const graphCategoryTitle: Record<string, string> = {
	start: 'Start',
	runtime: 'Runtime',
	operation: 'Operation',
	engines: 'Engines',
	recipes: 'Recipes'
};

export function loadGraph(): GraphPayload {
	return graphPayload as GraphPayload;
}

export function buildCategoryRegions(
	graph: GraphPayload,
	opts: { width: number; height: number }
): GraphRegion[] {
	const margin = 28;
	const gap = 18;
	const topHeight = Math.round(opts.height * 0.32);
	const bottomY = margin + topHeight + gap;
	const bottomHeight = opts.height - bottomY - margin;
	const topWidth = (opts.width - margin * 2 - gap * 2) / 3;
	const bottomWidth = (opts.width - margin * 2 - gap) / 2;
	const counts = graph.nodes.reduce<Record<string, number>>((acc, node) => {
		acc[node.category] = (acc[node.category] ?? 0) + 1;
		return acc;
	}, {});

	const rects: Record<string, Omit<GraphRegion, 'id' | 'title' | 'count'>> = {
		start: { x: margin, y: margin, width: topWidth, height: topHeight },
		runtime: { x: margin + topWidth + gap, y: margin, width: topWidth, height: topHeight },
		operation: { x: margin + (topWidth + gap) * 2, y: margin, width: topWidth, height: topHeight },
		engines: { x: margin, y: bottomY, width: bottomWidth, height: bottomHeight },
		recipes: { x: margin + bottomWidth + gap, y: bottomY, width: bottomWidth, height: bottomHeight }
	};

	return graphCategoryOrder.map((id) => ({
		id,
		title: graphCategoryTitle[id],
		count: counts[id] ?? 0,
		...rects[id]
	}));
}

// d3-hierarchy 트리 변환 · 카테고리 → cluster → skill 3 단계 트리.
export function buildHierarchy(graph: GraphPayload, opts: { width: number; height: number }) {
	const byCategory: Record<string, Record<string, GraphNode[]>> = {};
	for (const node of graph.nodes) {
		const cat = node.category;
		const cl = node.cluster ?? cat;
		byCategory[cat] ??= {};
		byCategory[cat][cl] ??= [];
		byCategory[cat][cl].push(node);
	}

	type TreeNode = { name: string; children?: TreeNode[]; node?: GraphNode };
	const root: TreeNode = {
		name: 'DartLab Skill OS',
		children: Object.entries(byCategory).map(([cat, clusters]) => ({
			name: cat,
			children: Object.entries(clusters).map(([cl, nodes]) => ({
				name: cl,
				children: nodes.map((n) => ({ name: n.title || n.id, node: n }))
			}))
		}))
	};

	const layout = tree<TreeNode>().size([opts.height - 80, opts.width - 240]);
	const rootHierarchy = hierarchy<TreeNode>(root, (d) => d.children);
	layout(rootHierarchy);
	return rootHierarchy;
}

// d3-force simulation 셋업 · 257 노드, knowledge 점선/linkedRecipe 굵은선.
export function buildForceSimulation(
	graph: GraphPayload,
	opts: { width: number; height: number }
) {
	const regions = buildCategoryRegions(graph, opts);
	const regionById = new Map(regions.map((region) => [region.id, region]));
	const nodes = graph.nodes.map((n) => ({ ...n }));
	const links = graph.edges
		.filter((e) => e.kind === 'successor' || e.kind === 'linkedRecipe' || e.kind === 'knowledge')
		.map((e) => ({ source: e.src, target: e.dst, kind: e.kind }));

	const sim = d3
		.forceSimulation(nodes as d3.SimulationNodeDatum[])
		.force(
			'link',
			d3
				.forceLink(links as d3.SimulationLinkDatum<d3.SimulationNodeDatum>[])
				.id((d: any) => d.id)
				.distance((link: any) => (link.kind === 'knowledge' ? 140 : 96))
				.strength((link: any) => (link.kind === 'knowledge' ? 0.08 : 0.18))
		)
		.force('charge', d3.forceManyBody().strength(-105))
		.force('collide', d3.forceCollide(17))
		.force(
			'x',
			d3
				.forceX((node: any) => {
					const region = regionById.get(node.category);
					return region ? region.x + region.width / 2 : opts.width / 2;
				})
				.strength(0.22)
		)
		.force(
			'y',
			d3
				.forceY((node: any) => {
					const region = regionById.get(node.category);
					return region ? region.y + region.height / 2 : opts.height / 2;
				})
				.strength(0.24)
		)
		.force('center', d3.forceCenter(opts.width / 2, opts.height / 2).strength(0.02));

	for (let i = 0; i < 260; i += 1) sim.tick();
	sim.stop();

	return { nodes, links, simulation: sim };
}
