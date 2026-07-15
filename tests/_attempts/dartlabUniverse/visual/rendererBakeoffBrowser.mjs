import {
	buildRendererFixture,
	coreActions,
	rendererDefinitions
} from './rendererBakeoffProbe.mjs';

const root = document.querySelector('#renderer-root');
const output = document.querySelector('#renderer-output');
const query = new URLSearchParams(location.search);
const profile = query.get('profile') === 'mobile' ? 'mobile' : 'desktop';
const repeatCount = 3;
const fixture = buildRendererFixture({
	nodeCount: profile === 'mobile' ? 250 : 500,
	edgeCount: profile === 'mobile' ? 500 : 1000
});
const width = profile === 'mobile' ? 360 : 800;
const height = 500;

function svgElement(name) {
	return document.createElementNS('http://www.w3.org/2000/svg', name);
}

function createTaskBridge(rendererId) {
	const bridge = document.createElement('nav');
	bridge.className = 'task-bridge';
	bridge.setAttribute('aria-label', `${rendererId} 핵심 작업`);
	const completed = new Set();
	for (const action of coreActions) {
		const button = document.createElement('button');
		button.type = 'button';
		button.dataset.action = action.id;
		button.textContent = action.label;
		button.setAttribute('aria-label', action.screenReaderSummary);
		button.addEventListener('click', () => completed.add(action.id));
		bridge.append(button);
	}
	return Object.freeze({ bridge, completed });
}

function nodePixels(node) {
	return Object.freeze({ x: node.x * width, y: node.y * height });
}

function createSvgAdapter() {
	let svg;
	let selected;
	return {
		async mount(container, data) {
			svg = svgElement('svg');
			svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
			svg.setAttribute('role', 'img');
			svg.setAttribute('aria-label', 'SVG bounded graph');
			const fragment = document.createDocumentFragment();
			const byId = new Map(data.nodes.map((node) => [node.id, nodePixels(node)]));
			for (const edge of data.edges) {
				const source = byId.get(edge.source);
				const target = byId.get(edge.target);
				const line = svgElement('line');
				line.setAttribute('x1', source.x);
				line.setAttribute('y1', source.y);
				line.setAttribute('x2', target.x);
				line.setAttribute('y2', target.y);
				line.setAttribute('class', 'edge');
				fragment.append(line);
			}
			for (const node of data.nodes) {
				const point = byId.get(node.id);
				const circle = svgElement('circle');
				circle.setAttribute('cx', point.x);
				circle.setAttribute('cy', point.y);
				circle.setAttribute('r', '3');
				circle.setAttribute('class', `node status-${node.status}`);
				circle.dataset.nodeId = node.id;
				fragment.append(circle);
			}
			svg.append(fragment);
			container.append(svg);
		},
		selectNode(id) {
			selected?.classList.remove('selected');
			selected = svg.querySelector(`[data-node-id="${id}"]`);
			selected?.classList.add('selected');
		},
		destroy() { svg?.remove(); }
	};
}

function createDomAdapter() {
	let table;
	let selected;
	return {
		async mount(container, data) {
			table = document.createElement('table');
			table.className = 'relation-table';
			const caption = document.createElement('caption');
			caption.textContent = `${data.nodeCount}개 node와 ${data.edgeCount}개 relation`;
			table.append(caption);
			const body = document.createElement('tbody');
			const fragment = document.createDocumentFragment();
			for (const node of data.nodes) {
				const row = document.createElement('tr');
				row.dataset.nodeId = node.id;
				row.innerHTML = `<th scope="row">${node.label}</th><td>${node.id}</td><td>status ${node.status}</td>`;
				fragment.append(row);
			}
			for (const edge of data.edges) {
				const row = document.createElement('tr');
				row.innerHTML = `<th scope="row">${edge.id}</th><td>${edge.source}</td><td>${edge.target}</td>`;
				fragment.append(row);
			}
			body.append(fragment);
			table.append(body);
			container.append(table);
		},
		selectNode(id) {
			selected?.removeAttribute('aria-selected');
			selected = table.querySelector(`[data-node-id="${id}"]`);
			selected?.setAttribute('aria-selected', 'true');
		},
		destroy() { table?.remove(); }
	};
}

function createCanvasAdapter() {
	let canvas;
	let context;
	let data;
	let selectedId;
	function draw() {
		context.clearRect(0, 0, width, height);
		const byId = new Map(data.nodes.map((node) => [node.id, nodePixels(node)]));
		context.strokeStyle = 'rgba(148, 163, 184, 0.24)';
		context.lineWidth = 1;
		context.beginPath();
		for (const edge of data.edges) {
			const source = byId.get(edge.source);
			const target = byId.get(edge.target);
			context.moveTo(source.x, source.y);
			context.lineTo(target.x, target.y);
		}
		context.stroke();
		context.fillStyle = '#60a5fa';
		for (const node of data.nodes) {
			const point = byId.get(node.id);
			context.beginPath();
			context.arc(point.x, point.y, 3, 0, Math.PI * 2);
			context.fill();
		}
		if (selectedId) {
			const point = byId.get(selectedId);
			context.strokeStyle = '#fbbf24';
			context.lineWidth = 3;
			context.beginPath();
			context.arc(point.x, point.y, 7, 0, Math.PI * 2);
			context.stroke();
		}
	}
	return {
		async mount(container, nextData) {
			data = nextData;
			canvas = document.createElement('canvas');
			canvas.width = width;
			canvas.height = height;
			canvas.setAttribute('role', 'img');
			canvas.setAttribute('aria-label', 'Canvas 2D bounded graph');
			context = canvas.getContext('2d');
			container.append(canvas);
			draw();
		},
		selectNode(id) { selectedId = id; draw(); },
		destroy() { canvas?.remove(); }
	};
}

let cosmosLoading;
async function ensureCosmos() {
	if (globalThis.Cosmos?.Graph) return;
	if (!cosmosLoading) {
		cosmosLoading = new Promise((resolve, reject) => {
			const script = document.createElement('script');
			script.src = './.renderer-bakeoff/node_modules/@cosmograph/cosmos/dist/index.min.js';
			script.onload = resolve;
			script.onerror = () => reject(new Error('failed to load locked Cosmos bundle'));
			document.head.append(script);
		});
	}
	await cosmosLoading;
}

function createCosmosAdapter() {
	let canvas;
	let graph;
	return {
		async mount(container, data) {
			await ensureCosmos();
			canvas = document.createElement('canvas');
			canvas.style.width = `${width}px`;
			canvas.style.height = `${height}px`;
			canvas.setAttribute('role', 'img');
			canvas.setAttribute('aria-label', 'Current Cosmos bounded graph');
			container.append(canvas);
			graph = new globalThis.Cosmos.Graph(canvas, {
				backgroundColor: '#08111f',
				disableSimulation: true,
				fitViewOnInit: false,
				initialZoomLevel: 1,
				pixelRatio: 1,
				randomSeed: 'universe-renderer-bakeoff',
				renderLinks: true,
				scaleNodesOnZoom: false,
				spaceSize: 1024,
				nodeSize: 4,
				nodeColor: '#60a5fa',
				linkColor: '#64748b',
				linkWidth: 1
			});
			const nodes = data.nodes.map((node) => ({
				id: node.id,
				x: (node.x - 0.5) * 900,
				y: (node.y - 0.5) * 600
			}));
			const links = data.edges.map((edge) => ({ source: edge.source, target: edge.target }));
			graph.setData(nodes, links, false);
		},
		selectNode(id) { graph.selectNodeById(id); },
		destroy() { graph?.destroy(); canvas?.remove(); }
	};
}

const factories = Object.freeze({
	svgReference: createSvgAdapter,
	currentCosmos: createCosmosAdapter,
	domReference: createDomAdapter,
	canvas2dCandidate: createCanvasAdapter
});

function animationFrame() {
	return new Promise((resolve) => requestAnimationFrame(resolve));
}

function percentile(values, fraction) {
	const ordered = [...values].sort((a, b) => a - b);
	return ordered[Math.min(ordered.length - 1, Math.ceil(ordered.length * fraction) - 1)];
}

async function measureRenderer(definition) {
	root.replaceChildren();
	const host = document.createElement('section');
	host.className = 'renderer-host';
	host.dataset.renderer = definition.id;
	const stage = document.createElement('div');
	stage.className = 'renderer-stage';
	const taskBridge = createTaskBridge(definition.id);
	host.append(stage, taskBridge.bridge);
	root.append(host);
	const adapter = factories[definition.id]();
	const heapBeforeBytes = performance.memory?.usedJSHeapSize ?? 0;
	const mountStart = performance.now();
	await adapter.mount(stage, fixture);
	const mountMs = performance.now() - mountStart;
	await animationFrame();
	await animationFrame();
	for (const button of taskBridge.bridge.querySelectorAll('button')) button.click();
	const frameStamps = [];
	for (let index = 0; index < 72; index += 1) {
		await new Promise((resolve) => requestAnimationFrame((stamp) => {
			frameStamps.push(stamp);
			adapter.selectNode(fixture.nodes[index % fixture.nodes.length].id);
			resolve();
		}));
	}
	const intervals = frameStamps.slice(1).map((stamp, index) => stamp - frameStamps[index]);
	const frameP95Ms = percentile(intervals, 0.95);
	const heapUsedAfterBytes = performance.memory?.usedJSHeapSize ?? heapBeforeBytes;
	const adapterImplementationBytes = new TextEncoder().encode(factories[definition.id].toString()).length;
	const dependencyRawBytes = definition.dependencyRawBytes ?? 0;
	const measurement = Object.freeze({
		rendererId: definition.id,
		available: true,
		mountMs: Number(mountMs.toFixed(3)),
		frameP95Ms: Number(frameP95Ms.toFixed(3)),
		frameP95Fps: Number((1000 / frameP95Ms).toFixed(3)),
		heapBeforeBytes,
		heapUsedAfterBytes,
		heapDeltaBytes: Math.max(0, heapUsedAfterBytes - heapBeforeBytes),
		bundleRawBytes: dependencyRawBytes + adapterImplementationBytes,
		bundleGzipBytes: definition.dependencyGzipBytes ?? 0,
		adapterImplementationBytes,
		taskCount: coreActions.length,
		taskCompletedCount: taskBridge.completed.size,
		renderedNodeCount: fixture.nodeCount,
		renderedEdgeCount: fixture.edgeCount,
		domElementCount: host.querySelectorAll('*').length
	});
	adapter.destroy();
	root.replaceChildren();
	await animationFrame();
	return measurement;
}

function aggregateTrials(rendererId, trials) {
	const worstFrameP95Ms = Math.max(...trials.map((trial) => trial.frameP95Ms));
	return Object.freeze({
		rendererId,
		available: trials.every((trial) => trial.available),
		trialCount: trials.length,
		mountMs: percentile(trials.map((trial) => trial.mountMs), 0.95),
		frameP95Ms: worstFrameP95Ms,
		frameP95Fps: Number((1000 / worstFrameP95Ms).toFixed(3)),
		heapBeforeBytes: Math.min(...trials.map((trial) => trial.heapBeforeBytes)),
		heapUsedAfterBytes: Math.max(...trials.map((trial) => trial.heapUsedAfterBytes)),
		heapDeltaBytes: Math.max(...trials.map((trial) => trial.heapDeltaBytes)),
		bundleRawBytes: trials[0].bundleRawBytes,
		bundleGzipBytes: trials[0].bundleGzipBytes,
		adapterImplementationBytes: trials[0].adapterImplementationBytes,
		taskCount: trials[0].taskCount,
		taskCompletedCount: Math.min(...trials.map((trial) => trial.taskCompletedCount)),
		renderedNodeCount: trials[0].renderedNodeCount,
		renderedEdgeCount: trials[0].renderedEdgeCount,
		domElementCount: Math.max(...trials.map((trial) => trial.domElementCount)),
		trials: Object.freeze(trials)
	});
}

export async function runRendererBakeoff() {
	const measurements = [];
	for (const definition of rendererDefinitions) {
		const trials = [];
		for (let index = 0; index < repeatCount; index += 1) trials.push(await measureRenderer(definition));
		measurements.push(aggregateTrials(definition.id, trials));
	}
	const receipt = Object.freeze({
		schemaVersion: 'rendererBakeoffReceipt.v1',
		profile,
		measuredAt: new Date().toISOString(),
		measurementEnvironment: Object.freeze({
			userAgent: navigator.userAgent,
			viewport: Object.freeze({ width: innerWidth, height: innerHeight }),
			devicePixelRatio,
			performanceMemoryAvailable: Boolean(performance.memory)
		}),
		fixture: Object.freeze({ nodeCount: fixture.nodeCount, edgeCount: fixture.edgeCount }),
		measurements: Object.freeze(measurements)
	});
	output.textContent = JSON.stringify(receipt, null, 2);
	return receipt;
}

globalThis.rendererBakeoffReady = runRendererBakeoff();
