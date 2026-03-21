<script>
	import { Command } from "bits-ui";
	import { cn } from "$lib/utils.js";

	let { class: className, children, ...restProps } = $props();
</script>

<Command.Item
	class={cn(
		"relative flex cursor-default items-center gap-2 rounded-lg px-2 py-1.5 text-sm",
		"text-dl-text outline-none",
		"data-[highlighted]:bg-dl-bg-card-hover",
		"data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
		className
	)}
	{...restProps}
>
	{@render children()}
</Command.Item>
