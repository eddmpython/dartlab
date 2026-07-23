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

const ROUTE_RUNTIME_ORIGIN = 'http://127.0.0.1:8765';
const ROUTE_SESSION_SCHEMA = 'du-u6-route-session-v1';
const ROUTE_RETRY_INTERVAL_MS = 1500;
const ALLOWED_FRAGMENT_KEYS = new Set(['api']);

function element(id) {
	const value = document.getElementById(id);
	if (!value) throw new Error(`필수 UI 누락: ${id}`);
	return value;
}

let canvas = null;
let labelLayer = null;
let loadingState = null;
let loadingDetail = null;
let errorState = null;
let errorTitle = null;
let errorDetail = null;
let backendLabel = null;
let visibleCount = null;
let scopeLabel = null;
let selectionPanel = null;
let selectionKicker = null;
let selectionTitle = null;
let selectionFacts = null;
let drillButton = null;
let backButton = null;
let labelsButton = null;
let edgesButton = null;

let camera = null;
const tileCache = new Map();
const sceneHistory = [];
let renderer = null;
let manifest = null;
let overviewScene = null;
let currentScene = { nodes: [], edges: [], label: '전체 우주' };
let selectedNode = null;
let showLabels = true;
let showEdges = true;
let frameRequestId = null;
let bootController = null;
let cleanupCallbacks = [];

function bindElements() {
	canvas = element('universe-canvas');
	labelLayer = element('label-layer');
	loadingState = element('loading-state');
	loadingDetail = element('loading-detail');
	errorState = element('error-state');
	errorTitle = element('error-title');
	errorDetail = element('error-detail');
	backendLabel = element('backend-label');
	visibleCount = element('visible-count');
	scopeLabel = element('scope-label');
	selectionPanel = element('selection-panel');
	selectionKicker = element('selection-kicker');
	selectionTitle = element('selection-title');
	selectionFacts = element('selection-facts');
	drillButton = element('drill-button');
	backButton = element('back-button');
	labelsButton = element('labels-button');
	edgesButton = element('edges-button');

	camera = new OrbitCamera();
	tileCache.clear();
	sceneHistory.length = 0;
	manifest = null;
	overviewScene = null;
	currentScene = { nodes: [], edges: [], label: '전체 우주' };
	selectedNode = null;
	showLabels = true;
	showEdges = true;
	frameRequestId = null;
	cleanupCallbacks = [];
}

function releaseElements() {
	canvas = null;
	labelLayer = null;
	loadingState = null;
	loadingDetail = null;
	errorState = null;
	errorTitle = null;
	errorDetail = null;
	backendLabel = null;
	visibleCount = null;
	scopeLabel = null;
	selectionPanel = null;
	selectionKicker = null;
	selectionTitle = null;
	selectionFacts = null;
	drillButton = null;
	backButton = null;
	labelsButton = null;
	edgesButton = null;
	camera = null;
}

function abortError() {
	return new DOMException('Universe 연결 중단', 'AbortError');
}

function assertActive(signal) {
	if (signal.aborted) throw abortError();
}

function listen(target, type, listener, options) {
	target.addEventListener(type, listener, options);
	cleanupCallbacks.push(() => target.removeEventListener(type, listener, options));
}

function loopbackApiBase(raw) {
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

function apiBaseFromFragment() {
	const params = new URLSearchParams(location.hash.slice(1));
	const sanitized = new URLSearchParams();
	for (const key of ALLOWED_FRAGMENT_KEYS) {
		const value = params.get(key);
		if (value) sanitized.set(key, value);
	}
	const nextHash = sanitized.toString();
	if (nextHash !== location.hash.slice(1)) {
		const nextUrl = `${location.pathname}${location.search}${nextHash ? `#${nextHash}` : ''}`;
		window.history.replaceState(window.history.state, '', nextUrl);
	}

	const rawApiBase = sanitized.get('api') || '';
	if (rawApiBase) return loopbackApiBase(rawApiBase);
	if (document.body.dataset.universeStandalone === 'true') {
		return loopbackApiBase(location.origin);
	}
	return ROUTE_RUNTIME_ORIGIN;
}

function pause(milliseconds, signal) {
	return new Promise((resolve, reject) => {
		if (signal.aborted) {
			reject(abortError());
			return;
		}
		const onAbort = () => {
			clearTimeout(timer);
			reject(abortError());
		};
		const timer = setTimeout(() => {
			signal.removeEventListener('abort', onAbort);
			resolve();
		}, milliseconds);
		signal.addEventListener('abort', onAbort, { once: true });
	});
}

async function discoverRouteSession(apiBase, signal) {
	const response = await fetch(`${apiBase}/api/session`, {
		method: 'GET',
		mode: 'cors',
		cache: 'no-store',
		credentials: 'omit',
		referrerPolicy: 'no-referrer',
		signal,
		targetAddressSpace: 'loopback',
		headers: { Accept: 'application/json' }
	});
	if (!response.ok) {
		throw new Error(`로컬 Universe 엔진 응답 ${response.status}`);
	}
	const payload = await response.json();
	if (payload?.schemaVersion !== ROUTE_SESSION_SCHEMA || typeof payload.token !== 'string' || payload.token.length < 32) {
		throw new Error('로컬 Universe session 계약이 잘못됨');
	}
	return {
		token: payload.token,
		apiBase
	};
}

function showRouteWaiting(apiBase) {
	loadingState.hidden = true;
	errorTitle.textContent = '로컬 지식 엔진 연결 대기 중';
	errorDetail.textContent =
		`DartLab Universe 엔진을 ${new URL(apiBase).host}에서 찾고 있습니다. ` +
		'엔진을 실행하고 브라우저가 로컬 네트워크 접근을 물으면 허용하세요. 권한이 열리면 자동으로 연결됩니다.';
	errorState.dataset.kind = 'waiting';
	errorState.hidden = false;
	backendLabel.textContent = '엔진 대기 중';
}

async function resolveSession(signal) {
	if (
		document.body.dataset.universeRoute !== 'true'
		&& document.body.dataset.universeStandalone !== 'true'
	) {
		throw new Error('Universe 실행 표면이 아님');
	}
	const apiBase = apiBaseFromFragment();

	setLoading('로컬 지식 엔진에 연결하고 있습니다', `${new URL(apiBase).host} 보안 session 확인 중`);
	let waitingVisible = false;
	while (!signal.aborted) {
		try {
			const session = await discoverRouteSession(apiBase, signal);
			errorState.hidden = true;
			delete errorState.dataset.kind;
			return session;
		} catch (error) {
			if (error?.name === 'AbortError') throw error;
			if (!waitingVisible) {
				showRouteWaiting(apiBase);
				waitingVisible = true;
			}
			await pause(ROUTE_RETRY_INTERVAL_MS, signal);
		}
	}
	throw abortError();
}

function setLoading(title, detail) {
	element('loading-title').textContent = title;
	loadingDetail.textContent = detail;
	errorState.hidden = true;
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

async function cachedTile(tileId, token, apiBase, signal) {
	assertActive(signal);
	if (!tileCache.has(tileId)) {
		tileCache.set(tileId, loadTile(tileId, token, manifest.scene.projectionDigest, apiBase, signal));
	}
	const tile = await tileCache.get(tileId);
	assertActive(signal);
	return tile;
}

async function initializeOverview(token, apiBase, signal) {
	const root = await cachedTile(manifest.rootTileId, token, apiBase, signal);
	const overviewId = root.header.childTileIds[0];
	if (!overviewId) throw new Error('overview tile이 없음');
	const overview = await cachedTile(overviewId, token, apiBase, signal);
	const pageIds = overview.header.childTileIds;
	const pages = [];
	for (let offset = 0; offset < pageIds.length; offset += 4) {
		assertActive(signal);
		loadingDetail.textContent = `은하계 ${Math.min(offset + 4, pageIds.length)} / ${pageIds.length}`;
		pages.push(...await Promise.all(
			pageIds.slice(offset, offset + 4).map((tileId) => cachedTile(tileId, token, apiBase, signal))
		));
	}
	assertActive(signal);
	overviewScene = mergeTiles([overview, ...pages], '전체 우주');
	setScene(overviewScene, { resetCamera: true, clearHistory: true });
}

async function initializeRenderer(signal) {
	try {
		const gpu = await WebGpuUniverseRenderer.create(canvas, () => showFatal('WebGPU device 연결이 끊어졌습니다. 화면을 다시 열어 WebGL2로 전환하세요.'));
		if (signal.aborted) {
			gpu.dispose();
			throw abortError();
		}
		backendLabel.textContent = 'WebGPU 가속';
		return gpu;
	} catch (error) {
		if (signal.aborted || error?.name === 'AbortError') throw abortError();
		backendLabel.dataset.webgpuFailure = error instanceof Error ? error.message : 'unknown';
		const replacement = canvas.cloneNode(false);
		canvas.replaceWith(replacement);
		canvas = replacement;
		assertActive(signal);
		const gl = new WebGlUniverseRenderer(canvas, () => showFatal('WebGL2 context 연결이 끊어졌습니다.'));
		backendLabel.textContent = 'WebGL2 가속';
		return gl;
	}
}

async function verifyRendererFrame(signal) {
	if (typeof renderer.probeFrame !== 'function') return;
	let frameValid = false;
	try {
		frameValid = await renderer.probeFrame(camera, { edges: showEdges });
	} catch (_error) {
		frameValid = false;
	}
	assertActive(signal);
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
	if (clearHistory) sceneHistory.length = 0;
	backButton.disabled = sceneHistory.length === 0;
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
	if (frameRequestId !== null || !renderer || !camera || !canvas) return;
	frameRequestId = requestAnimationFrame(() => {
		frameRequestId = null;
		if (!renderer || !camera || !canvas) return;
		const size = renderer.resize();
		camera.aspect = size.width / Math.max(1, size.height);
		camera.update();
		renderer.render(camera, { edges: showEdges });
		updateLabels();
	});
}

function visibleCandidates(limit = 40) {
	const labelSafeTop = canvas.clientWidth <= 360 ? 116 : canvas.clientWidth <= 720 ? 78 : 58;
	return currentScene.nodes
		.map((node) => ({ node, screen: renderer.project(node.position, camera) }))
		.filter((item) => item.screen && item.screen.x > -80 && item.screen.x < canvas.clientWidth + 80 && item.screen.y > labelSafeTop && item.screen.y < canvas.clientHeight + 30)
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

async function drillSelected(token, apiBase, signal) {
	const tileId = selectedNode?.metadata.drillTargetTileId;
	if (!tileId) return;
	const label = selectedNode.metadata.label;
	setLoading('은하계로 진입하고 있습니다', selectedNode.metadata.label);
	try {
		const tile = await cachedTile(tileId, token, apiBase, signal);
		assertActive(signal);
		sceneHistory.push(currentScene);
		const scene = mergeTiles([tile], label);
		setScene(scene, { resetCamera: true });
		backButton.disabled = false;
	} finally {
		if (!signal.aborted && loadingState) loadingState.hidden = true;
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
	if (!loadingState || !errorTitle || !errorDetail || !errorState) return;
	loadingState.hidden = true;
	errorTitle.textContent = '우주를 열지 못했습니다';
	errorDetail.textContent = message;
	errorState.dataset.kind = 'fatal';
	errorState.hidden = false;
}

async function main(signal) {
	const { token, apiBase } = await resolveSession(signal);
	assertActive(signal);
	setLoading('지식 우주를 구성하고 있습니다', '검증된 manifest를 확인하는 중');
	const loadedManifest = await loadManifest(token, apiBase, signal);
	assertActive(signal);
	manifest = loadedManifest;
	renderLegend(manifest.styleKeys);
	const initializedRenderer = await initializeRenderer(signal);
	assertActive(signal);
	renderer = initializedRenderer;
	await initializeOverview(token, apiBase, signal);
	await verifyRendererFrame(signal);
	assertActive(signal);
	const unbindCamera = bindCameraControls(canvas, camera, scheduleFrame, pickNode);
	if (typeof unbindCamera === 'function') cleanupCallbacks.push(unbindCamera);
	const resizeObserver = new ResizeObserver(scheduleFrame);
	resizeObserver.observe(canvas);
	cleanupCallbacks.push(() => resizeObserver.disconnect());
	loadingState.hidden = true;

	listen(element('home-button'), 'click', () => setScene(overviewScene, { resetCamera: true, clearHistory: true }));
	listen(backButton, 'click', () => {
		const previous = sceneHistory.pop();
		if (previous) setScene(previous, { resetCamera: true });
	});
	listen(labelsButton, 'click', () => {
		showLabels = !showLabels;
		labelsButton.setAttribute('aria-pressed', String(showLabels));
		scheduleFrame();
	});
	listen(edgesButton, 'click', () => {
		showEdges = !showEdges;
		edgesButton.setAttribute('aria-pressed', String(showEdges));
		scheduleFrame();
	});
	listen(element('close-selection'), 'click', () => selectNode(null));
	const onDrill = () => {
		void drillSelected(token, apiBase, signal).catch((error) => {
			if (!signal.aborted && error?.name !== 'AbortError') {
				showFatal(error instanceof Error ? error.message : '은하계 진입 실패');
			}
		});
	};
	listen(drillButton, 'click', onDrill);
	listen(canvas, 'dblclick', onDrill);
	listen(canvas, 'pointerdown', () => {
		const hint = document.getElementById('interaction-hint');
		if (hint) hint.hidden = true;
	}, { once: true });
	const onVisibilityChange = () => { if (!document.hidden) scheduleFrame(); };
	listen(document, 'visibilitychange', onVisibilityChange);
}

let bootPromise = null;

export function bootUniverse() {
	if (!bootPromise) {
		bindElements();
		bootController = new AbortController();
		const signal = bootController.signal;
		bootPromise = main(signal).catch((error) => {
			if (!signal.aborted && error?.name !== 'AbortError') {
				showFatal(error instanceof Error ? error.message : '알 수 없는 오류');
			}
		});
	}
	return bootPromise;
}

export function disposeUniverse() {
	bootController?.abort();
	bootController = null;
	if (frameRequestId !== null) {
		cancelAnimationFrame(frameRequestId);
		frameRequestId = null;
	}
	for (const cleanup of cleanupCallbacks.splice(0)) cleanup();
	renderer?.dispose();
	renderer = null;
	manifest = null;
	overviewScene = null;
	tileCache.clear();
	sceneHistory.length = 0;
	currentScene = { nodes: [], edges: [], label: '전체 우주' };
	selectedNode = null;
	releaseElements();
	bootPromise = null;
}

if (document.body.dataset.universeStandalone === 'true') {
	void bootUniverse();
}
