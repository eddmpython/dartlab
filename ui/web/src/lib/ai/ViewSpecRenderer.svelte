<script>
	import { getWidgetComponent } from "$lib/ai/widgetRegistry.js";
	import { normalizeViewSpec } from "$lib/ai/viewSpec.js";
	import { Maximize2 } from "lucide-svelte";

	let { view = null, onOpenArtifact = null } = $props();

	let resolvedView = $derived(normalizeViewSpec(view));
</script>

{#if resolvedView}
	<div class="rounded-2xl border border-dl-border/35 bg-dl-bg-card/30 p-4 group/artifact">
		{#if resolvedView.title || resolvedView.subtitle || onOpenArtifact}
			<div class="mb-3 flex items-start justify-between gap-2">
				<div class="min-w-0">
					{#if resolvedView.title}
						<div class="text-[12px] font-semibold text-dl-text">{resolvedView.title}</div>
					{/if}
					{#if resolvedView.subtitle}
						<div class="mt-1 text-[11px] text-dl-text-dim">{resolvedView.subtitle}</div>
					{/if}
				</div>
				{#if onOpenArtifact}
					<button
						class="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] text-dl-text-dim opacity-0 group-hover/artifact:opacity-100 hover:text-dl-text hover:bg-white/5 transition-all border border-dl-border/30 flex-shrink-0"
						onclick={() => onOpenArtifact(view)}
						title="패널에서 열기"
					>
						<Maximize2 size={10} />
						<span>열기</span>
					</button>
				{/if}
			</div>
		{/if}

		<div class="space-y-3" data-layout={resolvedView.layout}>
			{#each resolvedView.widgets as widget}
				{@const Component = getWidgetComponent(widget.widget)}
				<section class="rounded-xl border border-dl-border/25 bg-dl-bg-card/35 p-3">
					{#if widget.title || widget.description}
						<div class="mb-2">
							{#if widget.title}
								<div class="text-[11px] font-medium text-dl-text">{widget.title}</div>
							{/if}
							{#if widget.description}
								<div class="mt-1 text-[10px] text-dl-text-dim">{widget.description}</div>
							{/if}
						</div>
					{/if}
					{#if Component}
						<Component {...(widget.props || {})} />
					{:else}
						<div class="text-[12px] text-dl-text-dim">지원되지 않는 widget: {widget.widget}</div>
					{/if}
				</section>
			{/each}
		</div>
	</div>
{/if}
