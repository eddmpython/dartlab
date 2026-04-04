<script>
	import { Dialog } from "bits-ui";
	import { cn } from "$lib/utils.js";
	import { X } from "lucide-svelte";

	let {
		open = $bindable(false),
		side = "right",
		title = "",
		class: className,
		children,
		...restProps
	} = $props();

	const sides = {
		left: "inset-y-0 left-0 h-full w-3/4 max-w-sm border-r data-[state=open]:slide-in-from-left data-[state=closed]:slide-out-to-left",
		right: "inset-y-0 right-0 h-full w-3/4 max-w-sm border-l data-[state=open]:slide-in-from-right data-[state=closed]:slide-out-to-right",
		top: "inset-x-0 top-0 w-full border-b data-[state=open]:slide-in-from-top data-[state=closed]:slide-out-to-top",
		bottom: "inset-x-0 bottom-0 w-full border-t data-[state=open]:slide-in-from-bottom data-[state=closed]:slide-out-to-bottom",
	};
</script>

<Dialog.Root bind:open {...restProps}>
	<Dialog.Portal>
		<Dialog.Overlay
			class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm
				data-[state=open]:animate-in data-[state=open]:fade-in-0
				data-[state=closed]:animate-out data-[state=closed]:fade-out-0"
		/>
		<Dialog.Content
			class={cn(
				"fixed z-50 bg-dl-bg-sidebar border-dl-border p-6 shadow-[var(--shadow-overlay,0_24px_64px_rgba(0,0,0,0.34))]",
				"transition-transform duration-300 ease-out outline-none",
				"data-[state=open]:animate-in data-[state=closed]:animate-out",
				sides[side],
				className
			)}
		>
			{#if title}
				<Dialog.Title class="text-lg font-semibold text-dl-text mb-4">
					{title}
				</Dialog.Title>
			{/if}

			{@render children()}

			<Dialog.Close
				class="absolute right-4 top-4 rounded-md p-1 text-dl-text-dim
					hover:text-dl-text hover:bg-dl-bg-card-hover
					transition-colors duration-[var(--motion-fast)]"
			>
				<X size={16} />
			</Dialog.Close>
		</Dialog.Content>
	</Dialog.Portal>
</Dialog.Root>
