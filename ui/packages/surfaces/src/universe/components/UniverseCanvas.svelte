<script lang="ts">
	import { onMount } from 'svelte';
	import type { UniverseScene, UniverseVisualStatus } from '@dartlab/ui-contracts';
	import { compileDeterministicLayout, projectAnchors, type UniverseAnchorLayout } from '../layout';
	import { createCanvas2dRenderer } from '../renderers/canvas2dRenderer';
	import type { UniverseRenderer } from '../renderers/UniverseRenderer';
	import { UNIVERSE_VISUAL_TOKENS } from '../visualGrammar';

	interface Props {
		scene: UniverseScene;
		selectedId?: string | null;
		highlightedIds?: ReadonlySet<string>;
		onSelect?: (nodeId: string) => void;
	}

	let { scene, selectedId = null, highlightedIds = new Set<string>(), onSelect }: Props = $props();
	let container: HTMLDivElement;
	let canvas: HTMLCanvasElement;
	let renderer: UniverseRenderer | null = null;
	let width = $state(0);
	let height = $state(0);
	let dpr = $state(1);
	let anchors = $state<UniverseAnchorLayout | null>(null);

	let nodeById = $derived(new Map(scene.nodes.map((node) => [node.nodeId, node])));
	let logicalLayout = $derived(compileDeterministicLayout(scene.nodes.map((node) => ({
		nodeId: node.nodeId,
		label: node.label,
		stage: node.presentation?.stage ?? 'unknown',
		status: (node.lane === 'fact' || node.lane === 'candidate' || node.lane === 'derived' || node.lane === 'scenario'
			? node.lane : 'unknown') as UniverseVisualStatus,
		validOrder: node.presentation?.validOrder ?? null
	})), scene.sceneHash));

	function updateFrame(): void {
		if (!renderer || width <= 0 || height <= 0) return;
		const nextAnchors = projectAnchors(logicalLayout, { width, height, dpr });
		anchors = nextAnchors;
		renderer.render({ scene, anchors: nextAnchors, viewport: { width, height, dpr }, selectedId, highlightedIds });
	}

	$effect(() => {
		void scene;
		void selectedId;
		void highlightedIds;
		void logicalLayout;
		void width;
		void height;
		void dpr;
		updateFrame();
	});

	onMount(() => {
		renderer = createCanvas2dRenderer(canvas);
		const observer = new ResizeObserver(([entry]) => {
			if (!entry) return;
			width = Math.max(320, Math.round(entry.contentRect.width));
			height = Math.max(390, Math.round(entry.contentRect.height));
			dpr = Math.min(2, window.devicePixelRatio || 1);
		});
		observer.observe(container);
		return () => {
			observer.disconnect();
			renderer?.destroy();
			renderer = null;
		};
	});

	function safeId(nodeId: string): string {
		return `universe-node-${nodeId.replace(/[^A-Za-z0-9_-]/g, '-')}`;
	}
</script>

<div class="universeCanvas" bind:this={container} aria-label="산업 관계 우주">
	<canvas bind:this={canvas} aria-hidden="true"></canvas>
	<div class="axisLabels" aria-hidden="true">
		<span>UPSTREAM</span><span>MIDSTREAM</span><span>DOWNSTREAM</span>
	</div>
	{#if anchors}
		<div class="hitLayer">
			{#each anchors.anchors as anchor (anchor.nodeId)}
				{@const node = nodeById.get(anchor.nodeId)}
				{#if node}
					<button
						id={safeId(node.nodeId)}
						class:selected={selectedId === node.nodeId}
						style:left={`${anchor.x}px`}
						style:top={`${anchor.y}px`}
						title={node.label}
						aria-label={`${node.label}. ${UNIVERSE_VISUAL_TOKENS[node.lane === 'candidate' ? 'candidate' : node.lane === 'derived' ? 'derived' : 'unknown'].ariaStatus}`}
						onclick={() => onSelect?.(node.nodeId)}
					></button>
				{/if}
			{/each}
		</div>
	{/if}
	<div class="layoutReceipt" title={logicalLayout.logicalHash}>force 0 · deterministic</div>
</div>

<style>
	.universeCanvas { position: relative; width: 100%; height: 100%; min-height: 460px; overflow: hidden; border-radius: 18px; background: #090d16; }
	canvas, .hitLayer { position: absolute; inset: 0; }
	.hitLayer { pointer-events: none; }
	.hitLayer button { position: absolute; width: 34px; height: 34px; margin: -17px; border: 0; border-radius: 999px; background: transparent; pointer-events: auto; cursor: pointer; }
	.hitLayer button:hover, .hitLayer button:focus-visible { outline: 2px solid #f7f9fc; outline-offset: 3px; background: rgba(255,255,255,.08); }
	.hitLayer button.selected { outline: 1px solid rgba(255,255,255,.35); outline-offset: 5px; }
	.axisLabels { position: absolute; top: 16px; left: 7%; right: 7%; display: grid; grid-template-columns: repeat(3, 1fr); color: #56657b; font: 600 9px/1 ui-monospace, monospace; letter-spacing: .14em; text-align: center; pointer-events: none; }
	.layoutReceipt { position: absolute; right: 14px; bottom: 12px; padding: 5px 8px; border: 1px solid rgba(132,151,180,.14); border-radius: 999px; color: #56657b; background: rgba(9,13,22,.78); font: 500 9px/1 ui-monospace, monospace; letter-spacing: .04em; }
	@media (max-width: 720px) { .universeCanvas { min-height: 520px; } .axisLabels { left: 3%; right: 3%; } }
</style>
