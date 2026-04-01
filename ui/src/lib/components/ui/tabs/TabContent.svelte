<script>
	import { Tabs } from "bits-ui";
	import { cn } from "$lib/utils.js";

	let { value, class: className, children, ...restProps } = $props();
</script>

<Tabs.Content
	{value}
	class={cn("mt-2 outline-none", className)}
	{...restProps}
>
	{@render children()}
</Tabs.Content>
