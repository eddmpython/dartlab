<script>
	import { Collapsible } from "bits-ui";
	import { cn } from "$lib/utils.js";
	import { ChevronRight } from "lucide-svelte";

	let {
		open = $bindable(false),
		title = "",
		class: className,
		trigger,
		children,
		...restProps
	} = $props();
</script>

<Collapsible.Root bind:open class={cn(className)} {...restProps}>
	<Collapsible.Trigger
		class="flex w-full items-center gap-2 py-1.5 text-sm font-medium text-dl-text
			hover:text-dl-text-bright transition-colors duration-[var(--motion-fast)]
			outline-none focus-visible:ring-2 focus-visible:ring-dl-ring rounded-md"
	>
		<ChevronRight
			size={14}
			class="shrink-0 text-dl-text-dim transition-transform duration-200
				{open ? 'rotate-90' : ''}"
		/>
		{#if trigger}
			{@render trigger()}
		{:else}
			{title}
		{/if}
	</Collapsible.Trigger>
	<Collapsible.Content class="overflow-hidden data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=closed]:animate-out data-[state=closed]:fade-out-0">
		<div class="pl-5 pt-1">
			{@render children()}
		</div>
	</Collapsible.Content>
</Collapsible.Root>
