<script>
	import { Command } from "bits-ui";
	import { cn } from "$lib/utils.js";

	let { heading = "", class: className, children, ...restProps } = $props();
</script>

<Command.Group class={cn("overflow-hidden p-1", className)} {...restProps}>
	{#if heading}
		<Command.GroupHeading class="px-2 py-1.5 text-xs font-medium text-dl-text-dim">
			{heading}
		</Command.GroupHeading>
	{/if}
	<Command.GroupItems>
		{@render children()}
	</Command.GroupItems>
</Command.Group>
