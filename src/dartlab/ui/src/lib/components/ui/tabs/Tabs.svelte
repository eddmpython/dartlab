<script>
	import { Tabs } from "bits-ui";
	import { cn } from "$lib/utils.js";

	let {
		value = $bindable(""),
		items = [],
		variant = "default",
		class: className,
		children,
		...restProps
	} = $props();

	const listVariants = {
		default: "bg-dl-bg-card rounded-lg p-1",
		underline: "border-b border-dl-border",
	};

	const triggerVariants = {
		default: "rounded-md data-[state=active]:bg-dl-bg-card-hover data-[state=active]:shadow-sm",
		underline: "border-b-2 border-transparent rounded-none data-[state=active]:border-dl-primary",
	};
</script>

<Tabs.Root bind:value {...restProps}>
	<Tabs.List
		class={cn(
			"flex items-center gap-1",
			listVariants[variant],
			className
		)}
	>
		{#each items as item}
			<Tabs.Trigger
				value={item.value}
				class={cn(
					"inline-flex items-center justify-center px-3 py-1.5 text-sm font-medium",
					"text-dl-text-dim transition-all duration-[var(--motion-fast)]",
					"hover:text-dl-text",
					"data-[state=active]:text-dl-text",
					"disabled:pointer-events-none disabled:opacity-50",
					"outline-none focus-visible:ring-2 focus-visible:ring-dl-ring",
					triggerVariants[variant],
				)}
			>
				{item.label}
			</Tabs.Trigger>
		{/each}
	</Tabs.List>

	{@render children()}
</Tabs.Root>
