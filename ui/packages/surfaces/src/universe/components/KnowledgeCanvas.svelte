<script lang="ts">
	import { onMount } from 'svelte';
	import type { UniverseKnowledgeNode, UniverseKnowledgeScene } from '@dartlab/ui-contracts';
	import { knowledgeEdgeVisible, knowledgeLabelBudget, knowledgeLodLevel } from '../knowledgeLod';

	interface Props {
		scene: UniverseKnowledgeScene;
		selectedId?: string | null;
		focusNodeId?: string | null;
		filmActive?: boolean;
		filmBeatIndex?: number;
		onSelect?: (nodeId: string) => void;
		onOpen?: (nodeId: string) => void;
	}

	let { scene, selectedId = null, focusNodeId = null, filmActive = false, filmBeatIndex = 0, onSelect, onOpen }: Props = $props();
	let container: HTMLDivElement;
	let canvas: HTMLCanvasElement;
	let context: CanvasRenderingContext2D | null = null;
	let width = $state(900);
	let height = $state(640);
	let dpr = $state(1);
	let camera = $state({ scale: 1, offsetX: 0, offsetY: 0 });
	let lastFrameMs = $state(0);
	let dragging = $state(false);
	let dragX = 0;
	let dragY = 0;
	let frameId = 0;
	let cameraFrameId = 0;
	let semanticTarget = '';
	let reducedMotion = false;

	const domainColors: Readonly<Record<string, string>> = {
		sources: '#7f91aa',
		entities: '#76b8ff',
		securities: '#50d0be',
		filings: '#f0a66c',
		observations: '#f2cf6b',
		industry: '#7ed98a',
		marketData: '#58a9e8',
		macro: '#aa8cff',
		intelligence: '#e187b3',
		capabilities: '#ff786d',
		skills: '#b59cff',
		timeMedia: '#9aa8be'
	};

	let activeBeat = $derived(scene.film[Math.max(0, Math.min(scene.film.length - 1, filmBeatIndex))] ?? null);
	let visibleNodeIds = $derived(filmActive && activeBeat ? new Set(activeBeat.revealNodeIds) : new Set(scene.nodes.map((node) => node.nodeId)));
	let visibleEdgeIds = $derived(filmActive && activeBeat ? new Set(activeBeat.revealEdgeIds) : new Set(scene.edges.map((edge) => edge.edgeId)));
	let nodeById = $derived(new Map(scene.nodes.map((node) => [node.nodeId, node])));
	let worldRadius = $derived(Math.max(138, Math.min(width, height) * 0.43));
	let lodLevel = $derived(knowledgeLodLevel(camera.scale));

	function project(node: UniverseKnowledgeNode): { x: number; y: number } {
		return {
			x: width / 2 + (node.x * worldRadius + camera.offsetX) * camera.scale,
			y: height / 2 + (node.y * worldRadius + camera.offsetY) * camera.scale
		};
	}

	function requestDraw(): void {
		if (frameId) return;
		frameId = requestAnimationFrame(() => {
			frameId = 0;
			draw();
		});
	}

	function nodeRadius(node: UniverseKnowledgeNode): number {
		const base = Math.max(5, Math.min(22, 4 + node.weight * 0.43));
		return base * Math.min(1.4, Math.sqrt(camera.scale));
	}

	function nodeColor(node: UniverseKnowledgeNode): string {
		if (node.kind === 'root' || node.kind === 'query') return '#f3f7fc';
		return domainColors[node.domainId ?? 'sources'] ?? '#9aa8be';
	}

	function drawGrid(ctx: CanvasRenderingContext2D): void {
		const centerX = width / 2 + camera.offsetX * camera.scale;
		const centerY = height / 2 + camera.offsetY * camera.scale;
		ctx.save();
		ctx.strokeStyle = 'rgba(131, 151, 181, .08)';
		ctx.lineWidth = 1;
		for (const ratio of [0.42, 0.7, 0.91]) {
			ctx.beginPath();
			ctx.ellipse(centerX, centerY, worldRadius * ratio * camera.scale, worldRadius * ratio * 0.78 * camera.scale, 0, 0, Math.PI * 2);
			ctx.stroke();
		}
		ctx.beginPath();
		ctx.moveTo(0, centerY);
		ctx.lineTo(width, centerY);
		ctx.strokeStyle = 'rgba(131, 151, 181, .035)';
		ctx.stroke();
		ctx.restore();
	}

	function draw(): void {
		if (!context) return;
		const drawStartedAt = performance.now();
		canvas.width = Math.max(1, Math.round(width * dpr));
		canvas.height = Math.max(1, Math.round(height * dpr));
		canvas.style.width = `${width}px`;
		canvas.style.height = `${height}px`;
		context.setTransform(dpr, 0, 0, dpr, 0, 0);
		context.clearRect(0, 0, width, height);
		drawGrid(context);

		for (const edge of scene.edges) {
			if (!visibleEdgeIds.has(edge.edgeId)) continue;
			const source = nodeById.get(edge.sourceId);
			const target = nodeById.get(edge.targetId);
			if (!source || !target || !visibleNodeIds.has(source.nodeId) || !visibleNodeIds.has(target.nodeId)) continue;
			const start = project(source);
			const end = project(target);
			const selected = selectedId === source.nodeId || selectedId === target.nodeId;
			if (!knowledgeEdgeVisible(lodLevel, edge.lane, selected)) continue;
			const gradient = context.createLinearGradient(start.x, start.y, end.x, end.y);
			gradient.addColorStop(0, selected ? 'rgba(226, 235, 247, .64)' : 'rgba(116, 142, 179, .12)');
			gradient.addColorStop(1, selected ? 'rgba(137, 188, 255, .68)' : 'rgba(116, 142, 179, .28)');
			context.strokeStyle = gradient;
			context.lineWidth = selected ? 1.5 : 0.8;
			context.setLineDash(edge.lane === 'fact' ? [] : edge.lane === 'derived' ? [5, 4] : edge.lane === 'candidate' ? [2, 4] : [9, 5]);
			context.beginPath();
			context.moveTo(start.x, start.y);
			const curve = Math.min(52, Math.abs(end.x - start.x) * 0.16 + Math.abs(end.y - start.y) * 0.08);
			context.quadraticCurveTo((start.x + end.x) / 2 + curve, (start.y + end.y) / 2 - curve, end.x, end.y);
			context.stroke();
			context.setLineDash([]);
		}

		const labelAnchors: Array<{ x: number; y: number }> = [];
		const visibleNodes = scene.nodes.filter((node) => visibleNodeIds.has(node.nodeId));
		const labelBudget = knowledgeLabelBudget(lodLevel, visibleNodes.length);
		const labelCandidates = visibleNodes.length > 40 && camera.scale <= 1.6
			? visibleNodes.filter((node, index) => node.nodeId === scene.targetId || index % Math.max(1, Math.ceil(visibleNodes.length / labelBudget)) === 0).slice(0, labelBudget)
			: [...visibleNodes].sort((left, right) => right.weight - left.weight || left.nodeId.localeCompare(right.nodeId)).slice(0, labelBudget);
		const rankedIds = new Set(labelCandidates.map((node) => node.nodeId));

		for (const node of scene.nodes) {
			if (!visibleNodeIds.has(node.nodeId)) continue;
			const point = project(node);
			if (point.x < -80 || point.x > width + 80 || point.y < -80 || point.y > height + 80) continue;
			const radius = nodeRadius(node);
			const color = nodeColor(node);
			const selected = selectedId === node.nodeId || (filmActive && activeBeat?.targetNodeId === node.nodeId);
			if (selected) {
				context.fillStyle = color.replace(')', ', .12)').replace('rgb', 'rgba');
				context.globalAlpha = 0.14;
				context.beginPath();
				context.arc(point.x, point.y, radius + 15, 0, Math.PI * 2);
				context.fill();
				context.globalAlpha = 1;
			}
			const glow = context.createRadialGradient(point.x - radius * 0.28, point.y - radius * 0.3, 1, point.x, point.y, radius);
			glow.addColorStop(0, selected ? '#ffffff' : color);
			glow.addColorStop(0.28, color);
			glow.addColorStop(1, '#101827');
			context.fillStyle = glow;
			context.strokeStyle = selected ? '#f5f8fc' : color;
			context.lineWidth = selected ? 2.2 : node.kind === 'domain' ? 1.25 : 0.8;
			context.beginPath();
			context.arc(point.x, point.y, radius, 0, Math.PI * 2);
			context.fill();
			context.stroke();
			if (node.expandable) {
				context.strokeStyle = selected ? 'rgba(245, 248, 252, .52)' : 'rgba(137, 163, 197, .2)';
				context.lineWidth = 0.8;
				context.beginPath();
				context.arc(point.x, point.y, radius + 5, -0.75, 1.8);
				context.stroke();
			}
			if (node.lane !== 'fact') {
				context.strokeStyle = node.lane === 'derived' ? 'rgba(211, 158, 83, .48)' : 'rgba(151, 169, 194, .42)';
				context.lineWidth = 0.8;
				context.setLineDash(node.lane === 'derived' ? [4, 3] : [2, 3]);
				context.beginPath();
				context.arc(point.x, point.y, radius + 8, 0, Math.PI * 2);
				context.stroke();
				context.setLineDash([]);
			}

			if (selected || rankedIds.has(node.nodeId)) {
				const labelY = point.y + radius + 14;
				if (!selected && labelAnchors.some((label) => Math.abs(label.x - point.x) < 112 && Math.abs(label.y - labelY) < 24)) continue;
				context.textAlign = 'center';
				context.font = `${selected ? 600 : 500} ${selected ? 12 : 10}px Pretendard, system-ui, sans-serif`;
				context.fillStyle = selected ? '#f6f8fc' : 'rgba(197, 210, 228, .78)';
				context.fillText(node.label.length > 24 ? `${node.label.slice(0, 23)}…` : node.label, point.x, labelY);
				if (selected && node.secondaryLabel) {
					context.font = '500 8px ui-monospace, monospace';
					context.fillStyle = 'rgba(127, 146, 171, .86)';
					context.fillText(node.secondaryLabel.length > 42 ? `${node.secondaryLabel.slice(0, 41)}…` : node.secondaryLabel, point.x, labelY + 14);
				}
				labelAnchors.push({ x: point.x, y: labelY });
			}
		}
		const elapsed = performance.now() - drawStartedAt;
		if (Math.abs(lastFrameMs - elapsed) >= 0.2) lastFrameMs = elapsed;
	}

	function animateFocus(nodeId: string | null): void {
		if (!nodeId) return;
		const node = nodeById.get(nodeId);
		if (!node) return;
		if (cameraFrameId) cancelAnimationFrame(cameraFrameId);
		const start = { ...camera };
		const targetScale = node.kind === 'root' || node.kind === 'query' ? 1 : Math.max(1.12, Math.min(1.55, camera.scale));
		const target = { scale: targetScale, offsetX: -node.x * worldRadius, offsetY: -node.y * worldRadius };
		if (reducedMotion) {
			camera = target;
			requestDraw();
			return;
		}
		const startedAt = performance.now();
		const tick = (now: number) => {
			const progress = Math.min(1, (now - startedAt) / 520);
			const eased = 1 - Math.pow(1 - progress, 3);
			camera = {
				scale: start.scale + (target.scale - start.scale) * eased,
				offsetX: start.offsetX + (target.offsetX - start.offsetX) * eased,
				offsetY: start.offsetY + (target.offsetY - start.offsetY) * eased
			};
			requestDraw();
			if (progress < 1) cameraFrameId = requestAnimationFrame(tick);
			else cameraFrameId = 0;
		};
		cameraFrameId = requestAnimationFrame(tick);
	}

	function onWheel(event: WheelEvent): void {
		event.preventDefault();
		const rect = container.getBoundingClientRect();
		const pointerX = event.clientX - rect.left;
		const pointerY = event.clientY - rect.top;
		const oldScale = camera.scale;
		const nextScale = Math.max(0.62, Math.min(4.8, oldScale * Math.exp(-event.deltaY * 0.0013)));
		const worldX = (pointerX - width / 2) / oldScale - camera.offsetX;
		const worldY = (pointerY - height / 2) / oldScale - camera.offsetY;
		camera = {
			scale: nextScale,
			offsetX: (pointerX - width / 2) / nextScale - worldX,
			offsetY: (pointerY - height / 2) / nextScale - worldY
		};
		requestDraw();
		const selected = selectedId ? nodeById.get(selectedId) : null;
		if (event.deltaY < 0 && nextScale > 2.25 && selected?.expandable && semanticTarget !== selected.nodeId) {
			semanticTarget = selected.nodeId;
			onOpen?.(selected.nodeId);
		} else if (event.deltaY > 0 && nextScale <= 0.64 && scene.parentTargetId && semanticTarget !== scene.parentTargetId) {
			semanticTarget = scene.parentTargetId;
			onOpen?.(scene.parentTargetId);
		}
	}

	function onPointerDown(event: PointerEvent): void {
		dragging = true;
		dragX = event.clientX;
		dragY = event.clientY;
		container.setPointerCapture(event.pointerId);
	}

	function onPointerMove(event: PointerEvent): void {
		if (!dragging) return;
		const deltaX = (event.clientX - dragX) / camera.scale;
		const deltaY = (event.clientY - dragY) / camera.scale;
		dragX = event.clientX;
		dragY = event.clientY;
		camera = { ...camera, offsetX: camera.offsetX + deltaX, offsetY: camera.offsetY + deltaY };
		requestDraw();
	}

	function onPointerUp(event: PointerEvent): void {
		dragging = false;
		if (container.hasPointerCapture(event.pointerId)) container.releasePointerCapture(event.pointerId);
	}

	function resetCamera(): void {
		camera = { scale: 1, offsetX: 0, offsetY: 0 };
		semanticTarget = '';
		requestDraw();
	}

	$effect(() => {
		void scene.sceneId;
		resetCamera();
	});

	$effect(() => {
		void scene;
		void selectedId;
		void filmActive;
		void filmBeatIndex;
		void visibleNodeIds;
		void visibleEdgeIds;
		void width;
		void height;
		void dpr;
		requestDraw();
	});

	$effect(() => {
		animateFocus(focusNodeId);
	});

	onMount(() => {
		context = canvas.getContext('2d', { alpha: true });
		if (!context) throw new Error('Knowledge Universe Canvas 2D context is unavailable');
		reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
		const observer = new ResizeObserver(([entry]) => {
			if (!entry) return;
			width = Math.max(320, Math.round(entry.contentRect.width));
			height = Math.max(420, Math.round(entry.contentRect.height));
			dpr = Math.min(2, window.devicePixelRatio || 1);
			requestDraw();
		});
		observer.observe(container);
		requestDraw();
		return () => {
			observer.disconnect();
			if (frameId) cancelAnimationFrame(frameId);
			if (cameraFrameId) cancelAnimationFrame(cameraFrameId);
			context = null;
		};
	});
</script>

<div
	class="knowledgeCanvas"
	class:dragging
	bind:this={container}
	role="application"
	aria-label={`${scene.title}. 마우스 휠로 확대하거나 축소하고 노드를 두 번 눌러 더 깊이 탐색합니다.`}
	onwheel={onWheel}
	onpointerdown={onPointerDown}
	onpointermove={onPointerMove}
	onpointerup={onPointerUp}
	onpointercancel={onPointerUp}
>
	<canvas bind:this={canvas} aria-hidden="true"></canvas>
	<div class="hitLayer">
		{#each scene.nodes as node (node.nodeId)}
			{#if visibleNodeIds.has(node.nodeId)}
				{@const point = project(node)}
				<button
					type="button"
					class:selected={selectedId === node.nodeId}
					style:left={`${point.x}px`}
					style:top={`${point.y}px`}
					aria-label={`${node.label}. ${node.secondaryLabel}${node.expandable ? '. 확대 가능' : ''}`}
					onclick={(event) => { event.stopPropagation(); onSelect?.(node.nodeId); }}
					ondblclick={(event) => { event.stopPropagation(); if (node.expandable) onOpen?.(node.nodeId); }}
				></button>
			{/if}
		{/each}
	</div>
	<div class="cameraReadout" aria-hidden="true">
		<span>ZOOM {camera.scale.toFixed(2)}×</span>
		<span>LOD {lodLevel}</span>
		<span>{scene.receipt.outputNodeCount} NODES</span>
		<span>FRAME {lastFrameMs.toFixed(1)}MS</span>
		{#if scene.receipt.omittedNodeCount > 0}<span>OMITTED +{scene.receipt.omittedNodeCount}</span>{/if}
	</div>
	<button class="resetCamera" type="button" onclick={resetCamera}>전체 보기</button>
</div>

<style>
	.knowledgeCanvas { position: relative; width: 100%; height: 100%; min-height: 520px; overflow: hidden; cursor: grab; touch-action: none; background: radial-gradient(circle at 50% 48%, rgba(54, 77, 113, .11), transparent 48%); }
	.knowledgeCanvas.dragging { cursor: grabbing; }
	canvas, .hitLayer { position: absolute; inset: 0; }
	.hitLayer { pointer-events: none; }
	.hitLayer button { position: absolute; width: 44px; height: 44px; margin: -22px; border: 0; border-radius: 50%; outline-offset: 4px; background: transparent; pointer-events: auto; cursor: pointer; }
	.hitLayer button:hover { background: rgba(213, 228, 248, .07); }
	.hitLayer button:focus-visible, .hitLayer button.selected { outline: 1px solid rgba(231, 239, 249, .72); }
	.cameraReadout { position: absolute; left: 18px; bottom: 16px; display: flex; gap: 12px; color: #53637a; font: 600 8px/1 ui-monospace, monospace; letter-spacing: .08em; pointer-events: none; }
	.resetCamera { position: absolute; right: 18px; bottom: 10px; border: 1px solid rgba(105, 124, 151, .2); border-radius: 999px; padding: 7px 10px; color: #74869d; background: rgba(8, 12, 19, .72); font-size: 9px; cursor: pointer; backdrop-filter: blur(10px); }
	.resetCamera:hover { color: #d4deeb; border-color: rgba(142, 164, 196, .42); }
	@media (max-width: 720px) { .knowledgeCanvas { min-height: 460px; } .cameraReadout span:nth-child(n+4) { display: none; } }
</style>
