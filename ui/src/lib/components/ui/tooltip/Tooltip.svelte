<script>
	import { Tooltip } from "bits-ui";
	import { cn } from "$lib/utils.js";

	let {
		text = "",
		side = "top",
		delayDuration = 200,
		class: className,
		children,
		...restProps
	} = $props();
</script>

<Tooltip.Provider {delayDuration}>
	<Tooltip.Root {...restProps}>
		<Tooltip.Trigger asChild>
			{@render children()}
		</Tooltip.Trigger>
		<Tooltip.Portal>
			<Tooltip.Content
				{side}
				sideOffset={4}
				class={cn(
					"z-50 max-w-xs rounded-lg px-3 py-1.5 text-xs",
					"bg-dl-bg-card text-dl-text border border-dl-border",
					"shadow-[var(--shadow-surface)]",
					"animate-in fade-in-0 zoom-in-95",
					className
				)}
			>
				{text}
				<Tooltip.Arrow class="fill-dl-bg-card stroke-dl-border" />
			</Tooltip.Content>
		</Tooltip.Portal>
	</Tooltip.Root>
</Tooltip.Provider>
