// @ts-nocheck
import { OrbitCamera, bindCameraControls } from './camera.js';
import { loadManifest, loadTile } from './tile-codec.js';
import { WebGlUniverseRenderer } from './webgl2-renderer.js';
import { WebGpuUniverseRenderer } from './webgpu-renderer.js';

const FAMILY_LABELS = {
	CAPABILITY: '분석 엔진',
	DATA: '공시·재무 데이터',
	ENTITY: '법인·인물',
	KNOWLEDGE: '블로그·지식',
	MEDIA: '이미지·영상',
	OTHER: '기타 근거'
};

function element(id) {
	const value = document.getElementById(id);
	if (!value) throw new Error(`필수 UI 누락: ${id}`);
	return value;
}

let canvas = element('universe-canvas');
const labelLayer = element('label-layer');
const loadingState = element('loading-state');
const loadingDetail = element('loading-detail');
const errorState = element('error-state');
const errorDetail = element('error-detail');
const backendLabel = element('backend-label');
const visibleCount = element('visible-count');
const scopeLabel = element('scope-label');
const selectionPanel = element('selection-panel');
const selectionKicker = element('selection-kicker');
const selectionTitle = element('selection-title');
const selectionFacts = element('selection-facts');
const drillButton = element('drill-button');
const backButton = element('back-button');
const labelsButton = element('labels-button');
const edgesButton = element('edges-button');

const camera = new OrbitCamera();
const tileCache = new Map();
const history = [];
let renderer = null;
let manifest = null;
let overviewScene = null;
let currentScene = { nodes: [], edges: [], label: '전체 우주' };
let selectedNode = null;
let showLabels = true;
let showEdges = true;
let frameRequested = false;

function tokenFromFragment() {
	const token = new URLSearchParams(location.hash.slice(1)).get('token') || '';
	if (token.length < 32) throw new Error('검수 session token이 없음');
	return token;
}

function apiBaseFromFragment() {
	const raw = new URLSearchParams(location.hash.slice(1)).get('api') || '';
	if (!raw) return '';
	const parsed = new URL(raw);
	const loopbackHosts = new Set(['127.0.0.1', 'localhost', '[::1]']);
	if (parsed.protocol !== 'http:' || !loopbackHosts.has(parsed.hostname)) {
		throw new Error('Universe runtime은 loopback 주소만 허용함');
	}
	if (parsed.username || parsed.password || parsed.search || parsed.hash) {
		throw new Error('Universe runtime 주소 형식이 잘못됨');
	}
	return parsed.origin;
}

function setLoading(title, detail) {
	element('loading-title').textContent = title;
	loadingDetail.textContent = detail;
	loadingState.hidden = false;
}

function mergeTiles(tiles, label) {
	const nodes = new Map();
	const edges = [];
	const edgeKeys = new Set();
	for (const tile of tiles) {
		for (const node of tile.nodes) nodes.set(node.pickId, node);
		for (const edge of tile.edges) {
			const key = `${edge.from.join(',')}:${edge.to.join(',')}:${edge.styleIndex}`;
			if (!edgeKeys.has(key)) {
				edgeKeys.add(key);
				edges.push(edge);
			}
		}
	}
	return { nodes: [...nodes.values()], edges, label };
}

async function cachedTile(tileId, token, apiBase) {
	if (!tileCache.has(tileId)) {
		tileCache.set(tileId, loadTile(tileId, token, manifest.scene.projectionDigest, apiBase));
	}
	return tileCache.get(tileId);
}

async function initializeOverview(token, apiBase) {
	const root = await cachedTile(manifest.rootTileId, token, apiBase);
	const overviewId = root.header.childTileIds[0];
	if (!overviewId) throw new Error('overview tile이 없음');
	const overview = await cachedTile(overviewId, token, apiBase);
	const pageIds = overview.header.childTileIds;
	const pages = [];
	for (let offset = 0; offset < pageIds.length; offset += 4) {
		loadingDetail.textContent = `은하계 ${Math.min(offset + 4, pageIds.length)} / ${pageIds.length}`;
		pages.push(...await Promise.all(pageIds.slice(offset, offset + 4).map((tileId) => cachedTile(tileId, token, apiBase))));
	}
	overviewScene = mergeTiles([overview, ...pages], '전체 우주');
	setScene(overviewScene, { resetCamera: true, clearHistory: true });
}

async function initializeRenderer() {
	const forcedBackend = new URLSearchParams(location.hash.slice(1)).get('backend');
	if (forcedBackend === 'webgl2') {
		const gl = new WebGlUniverseRenderer(canvas, () => showFatal('WebGL2 context 연결이 끊어졌습니다.'));
		backendLabel.textContent = 'WebGL2 가속';
		return gl;
	}
	try {
		const gpu = await WebGpuUniverseRenderer.create(canvas, () => showFatal('WebGPU device 연결이 끊어졌습니다. 화면을 다시 열어 WebGL2로 전환하세요.'));
		backendLabel.textContent = 'WebGPU 가속';
		return gpu;
	} catch (error) {
		backendLabel.dataset.webgpuFailure = error instanceof Error ? error.message : 'unknown';
		const replacement = canvas.cloneNode(false);
		canvas.replaceWith(replacement);
		canvas = replacement;
		const gl = new WebGlUniverseRenderer(canvas, () => showFatal('WebGL2 context 연결이 끊어졌습니다.'));
		backendLabel.textContent = 'WebGL2 가속';
		return gl;
	}
}

async function verifyRendererFrame() {
	if (typeof renderer.probeFrame !== 'function') return;
	let frameValid = false;
	try {
		frameValid = await renderer.probeFrame(camera, { edges: showEdges });
	} catch (_error) {
		frameValid = false;
	}
	if (frameValid) return;
	renderer.dispose();
	const replacement = canvas.cloneNode(false);
	canvas.replaceWith(replacement);
	canvas = replacement;
	renderer = new WebGlUniverseRenderer(canvas, () => showFatal('WebGL2 context 연결이 끊어졌습니다.'));
	renderer.setScene(currentScene);
	backendLabel.textContent = 'WebGL2 자동 전환';
}

function setScene(scene, { resetCamera = false, clearHistory = false } = {}) {
	currentScene = scene;
	selectedNode = null;
	selectionPanel.hidden = true;
	drillButton.hidden = true;
	if (clearHistory) history.length = 0;
	backButton.disabled = history.length === 0;
	const viewport = renderer.resize();
	camera.aspect = viewport.width / Math.max(1, viewport.height);
	if (resetCamera) camera.frame(scene.nodes.map((node) => node.position));
	renderer.setSelected(0);
	renderer.setScene(scene);
	scopeLabel.textContent = scene.label;
	visibleCount.textContent = `${scene.nodes.length.toLocaleString()}개 천체 · 전체 ${manifest.scene.objectCount.toLocaleString()}개 지식`;
	scheduleFrame();
}

function scheduleFrame() {
	if (frameRequested) return;
	frameRequested = true;
	requestAnimationFrame(() => {
		frameRequested = false;
		const size = renderer.resize();
		camera.aspect = size.width / Math.max(1, size.height);
		camera.update();
		renderer.render(camera, { edges: showEdges });
		updateLabels();
	});
}

function visibleCandidates(limit = 40) {
	return currentScene.nodes
		.map((node) => ({ node, screen: renderer.project(node.position, camera) }))
		.filter((item) => item.screen && item.screen.x > -80 && item.screen.x < canvas.clientWidth + 80 && item.screen.y > -30 && item.screen.y < canvas.clientHeight + 30)
		.sort((left, right) => {
			if (left.node === selectedNode) return -1;
			if (right.node === selectedNode) return 1;
			const levelDelta = left.node.metadata.lodLevel - right.node.metadata.lodLevel;
			return levelDelta || right.node.importance - left.node.importance || left.screen.depth - right.screen.depth;
		})
		.slice(0, limit);
}

function updateLabels() {
	labelLayer.replaceChildren();
	if (!showLabels) return;
	const occupied = [];
	let rendered = 0;
	for (const { node, screen } of visibleCandidates()) {
		if (rendered >= 18) break;
		const width = Math.min(220, Math.max(58, node.metadata.label.length * 8.5 + 12));
		const left = Math.max(4, Math.min(canvas.clientWidth - width - 4, screen.x + 9));
		const box = { left, right: left + width, top: screen.y - 11, bottom: screen.y + 11 };
		if (node !== selectedNode && occupied.some((item) => !(
			box.right + 5 < item.left || box.left > item.right + 5 || box.bottom + 4 < item.top || box.top > item.bottom + 4
		))) continue;
		const label = document.createElement('span');
		label.className = 'node-label';
		label.textContent = node.metadata.label;
		label.style.left = `${left}px`;
		label.style.top = `${screen.y}px`;
		label.style.maxWidth = `${Math.max(40, canvas.clientWidth - 8)}px`;
		labelLayer.append(label);
		occupied.push(box);
		rendered += 1;
	}
}

function pickNode(clientX, clientY) {
	const bounds = canvas.getBoundingClientRect();
	const x = clientX - bounds.left;
	const y = clientY - bounds.top;
	let best = null;
	for (const node of currentScene.nodes) {
		const screen = renderer.project(node.position, camera);
		if (!screen) continue;
		const distance = Math.hypot(screen.x - x, screen.y - y);
		const hitRadius = Math.max(8, Math.min(28, node.size * 0.72));
		if (distance <= hitRadius && (!best || distance < best.distance || (distance === best.distance && screen.depth < best.depth))) {
			best = { node, distance, depth: screen.depth };
		}
	}
	selectNode(best?.node || null);
}

function fact(term, description) {
	const dt = document.createElement('dt');
	dt.textContent = term;
	const dd = document.createElement('dd');
	dd.textContent = description;
	selectionFacts.append(dt, dd);
}

function selectNode(node) {
	selectedNode = node;
	renderer.setSelected(node?.pickId || 0);
	if (!node) {
		selectionPanel.hidden = true;
		scheduleFrame();
		return;
	}
	const metadata = node.metadata;
	selectionKicker.textContent = FAMILY_LABELS[metadata.family] || metadata.family;
	selectionTitle.textContent = metadata.label;
	selectionFacts.replaceChildren();
	fact('계층', `L${metadata.lodLevel} · ${metadata.targetKind}`);
	fact('포함 지식', Number(metadata.memberCount).toLocaleString());
	fact('근거', Number(metadata.evidenceCount).toLocaleString());
	fact('검증 참조', String(metadata.detailRef).slice(0, 32));
	drillButton.hidden = !metadata.drillTargetTileId;
	selectionPanel.hidden = false;
	scheduleFrame();
}

async function drillSelected(token, apiBase) {
	const tileId = selectedNode?.metadata.drillTargetTileId;
	if (!tileId) return;
	setLoading('은하계로 진입하고 있습니다', selectedNode.metadata.label);
	try {
		const tile = await cachedTile(tileId, token, apiBase);
		history.push(currentScene);
		const scene = mergeTiles([tile], selectedNode.metadata.label);
		setScene(scene, { resetCamera: true });
		backButton.disabled = false;
	} finally {
		loadingState.hidden = true;
	}
}

function renderLegend(styleKeys) {
	const legend = element('legend');
	styleKeys.forEach((key, index) => {
		const item = document.createElement('span');
		item.className = 'legend-item';
		const swatch = document.createElement('span');
		swatch.className = 'legend-swatch';
		swatch.style.color = `var(--series-${index % 6 + 1})`;
		swatch.style.background = 'currentColor';
		const label = document.createElement('span');
		label.textContent = FAMILY_LABELS[key] || key;
		item.append(swatch, label);
		legend.append(item);
	});
}

function showFatal(message) {
	loadingState.hidden = true;
	errorDetail.textContent = message;
	errorState.hidden = false;
}

async function main() {
	const token = tokenFromFragment();
	const apiBase = apiBaseFromFragment();
	setLoading('지식 우주를 구성하고 있습니다', '검증된 manifest를 확인하는 중');
	manifest = await loadManifest(token, apiBase);
	renderLegend(manifest.styleKeys);
	renderer = await initializeRenderer();
	await initializeOverview(token, apiBase);
	await verifyRendererFrame();
	bindCameraControls(canvas, camera, scheduleFrame, pickNode);
	new ResizeObserver(scheduleFrame).observe(canvas);
	loadingState.hidden = true;

	element('home-button').addEventListener('click', () => setScene(overviewScene, { resetCamera: true, clearHistory: true }));
	backButton.addEventListener('click', () => {
		const previous = history.pop();
		if (previous) setScene(previous, { resetCamera: true });
	});
	labelsButton.addEventListener('click', () => {
		showLabels = !showLabels;
		labelsButton.setAttribute('aria-pressed', String(showLabels));
		scheduleFrame();
	});
	edgesButton.addEventListener('click', () => {
		showEdges = !showEdges;
		edgesButton.setAttribute('aria-pressed', String(showEdges));
		scheduleFrame();
	});
	element('close-selection').addEventListener('click', () => selectNode(null));
	drillButton.addEventListener('click', () => void drillSelected(token, apiBase));
	canvas.addEventListener('dblclick', () => void drillSelected(token, apiBase));
	canvas.addEventListener('pointerdown', () => { element('interaction-hint').hidden = true; }, { once: true });
	document.addEventListener('visibilitychange', () => { if (!document.hidden) scheduleFrame(); });
	matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => {
		renderer.setScene(currentScene);
		scheduleFrame();
	});
}

let bootPromise = null;

export function bootUniverse() {
	if (!bootPromise) {
		bootPromise = main().catch((error) => showFatal(error instanceof Error ? error.message : '알 수 없는 오류'));
	}
	return bootPromise;
}

if (document.body.dataset.universeStandalone === 'true') {
	void bootUniverse();
}
