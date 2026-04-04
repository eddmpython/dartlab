<script>
	import { ScrollArea } from "bits-ui";
	import { cn } from "$lib/utils.js";

	let {
		orientation = "vertical",
		class: className,
		children,
		...restProps
	} = $props();
</script>

<ScrollArea.Root
	class={cn("relative overflow-hidden", className)}
	{...restProps}
>
	<ScrollArea.Viewport class="h-full w-full rounded-[inherit]">
		{@render children()}
	</ScrollArea.Viewport>
	<ScrollArea.Scrollbar
		{orientation}
		class={cn(
			"flex touch-none select-none transition-colors duration-150",
			orientation === "vertical" ? "h-full w-2 border-l border-l-transparent p-px" : "h-2 flex-col border-t border-t-transparent p-px",
		)}
	>
		<ScrollArea.Thumb
			class="relative flex-1 rounded-full bg-dl-text-dim/30 hover:bg-dl-text-dim/50 transition-colors"
		/>
	</ScrollArea.Scrollbar>
	<ScrollArea.Corner />
</ScrollArea.Root>
