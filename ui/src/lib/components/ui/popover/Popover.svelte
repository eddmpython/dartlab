<script>
	import { Popover } from "bits-ui";
	import { cn } from "$lib/utils.js";

	let {
		open = $bindable(false),
		side = "bottom",
		align = "center",
		class: className,
		trigger,
		children,
		...restProps
	} = $props();
</script>

<Popover.Root bind:open {...restProps}>
	<Popover.Trigger asChild>
		{@render trigger()}
	</Popover.Trigger>
	<Popover.Portal>
		<Popover.Content
			{side}
			{align}
			sideOffset={4}
			class={cn(
				"z-50 w-72 rounded-xl border border-dl-border bg-dl-bg-sidebar p-4",
				"shadow-[var(--shadow-raised,0_10px_30px_rgba(0,0,0,0.16))] outline-none",
				"data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95",
				"data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95",
				className
			)}
		>
			{@render children()}
		</Popover.Content>
	</Popover.Portal>
</Popover.Root>
