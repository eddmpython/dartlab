<script>
	import { DropdownMenu } from "bits-ui";
	import { cn } from "$lib/utils.js";

	let {
		variant = "default",
		class: className,
		children,
		...restProps
	} = $props();

	const variants = {
		default: "text-dl-text",
		destructive: "text-red-400 focus:text-red-300",
	};
</script>

<DropdownMenu.Item
	class={cn(
		"relative flex cursor-default items-center gap-2 rounded-lg px-2 py-1.5 text-sm outline-none",
		"transition-colors duration-[var(--motion-fast)]",
		"data-[highlighted]:bg-dl-bg-card-hover",
		"data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
		variants[variant],
		className
	)}
	{...restProps}
>
	{@render children()}
</DropdownMenu.Item>
