<script>
	import { Select } from "bits-ui";
	import { cn } from "$lib/utils.js";
	import { ChevronDown, Check } from "lucide-svelte";

	let {
		value = $bindable(""),
		items = [],
		placeholder = "선택...",
		class: className,
		...restProps
	} = $props();
</script>

<Select.Root bind:value type="single" {...restProps}>
	<Select.Trigger
		class={cn(
			"flex h-9 w-full items-center justify-between rounded-lg border px-3 py-2 text-sm",
			"bg-dl-bg-card border-dl-border text-dl-text",
			"hover:bg-dl-bg-card-hover",
			"focus:border-dl-primary/50 focus:ring-2 focus:ring-dl-ring outline-none",
			"disabled:cursor-not-allowed disabled:opacity-50",
			"transition-all duration-[var(--motion-fast)]",
			className
		)}
	>
		{#snippet child({ selectedLabel })}
			<span class="truncate">{selectedLabel || placeholder}</span>
			<ChevronDown size={14} class="shrink-0 text-dl-text-dim" />
		{/snippet}
	</Select.Trigger>
	<Select.Portal>
		<Select.Content
			sideOffset={4}
			class={cn(
				"z-50 min-w-[8rem] overflow-hidden rounded-xl border border-dl-border",
				"bg-dl-bg-sidebar shadow-[var(--shadow-raised,0_10px_30px_rgba(0,0,0,0.16))]",
				"data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95",
				"data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95",
			)}
		>
			<Select.Viewport class="p-1">
				{#each items as item}
					<Select.Item
						value={item.value}
						label={item.label}
						class={cn(
							"relative flex w-full cursor-default items-center rounded-lg py-1.5 pl-8 pr-2 text-sm",
							"text-dl-text outline-none",
							"data-[highlighted]:bg-dl-bg-card-hover",
							"data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
						)}
					>
						{#snippet children({ selected })}
							{#if selected}
								<span class="absolute left-2 flex items-center">
									<Check size={14} class="text-dl-primary" />
								</span>
							{/if}
							{item.label}
						{/snippet}
					</Select.Item>
				{/each}
			</Select.Viewport>
		</Select.Content>
	</Select.Portal>
</Select.Root>
