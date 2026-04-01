<script>
	import { DropdownMenu } from "bits-ui";
	import { cn } from "$lib/utils.js";

	let { class: className } = $props();
</script>

<DropdownMenu.Separator
	class={cn("-mx-1 my-1 h-px bg-dl-border", className)}
/>
