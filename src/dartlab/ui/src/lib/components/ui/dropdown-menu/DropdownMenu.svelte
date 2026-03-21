<script>
	import { DropdownMenu } from "bits-ui";
	import { cn } from "$lib/utils.js";

	let {
		open = $bindable(false),
		side = "bottom",
		align = "start",
		class: className,
		trigger,
		children,
		...restProps
	} = $props();
</script>

<DropdownMenu.Root bind:open {...restProps}>
	<DropdownMenu.Trigger asChild>
		{@render trigger()}
	</DropdownMenu.Trigger>
	<DropdownMenu.Portal>
		<DropdownMenu.Content
			{side}
			{align}
			sideOffset={4}
			class={cn(
				"z-50 min-w-[8rem] overflow-hidden rounded-xl border border-dl-border p-1",
				"bg-dl-bg-sidebar shadow-[var(--shadow-raised,0_10px_30px_rgba(0,0,0,0.16))]",
				"data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95",
				"data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95",
				className
			)}
		>
			{@render children()}
		</DropdownMenu.Content>
	</DropdownMenu.Portal>
</DropdownMenu.Root>
