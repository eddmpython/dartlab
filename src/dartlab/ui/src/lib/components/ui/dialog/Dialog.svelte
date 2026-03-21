<script>
	import { Dialog } from "bits-ui";
	import { cn } from "$lib/utils.js";
	import { X } from "lucide-svelte";

	let {
		open = $bindable(false),
		title = "",
		description = "",
		size = "default",
		class: className,
		children,
		...restProps
	} = $props();

	const sizes = {
		sm: "max-w-sm",
		default: "max-w-lg",
		lg: "max-w-2xl",
		xl: "max-w-4xl",
		full: "max-w-[calc(100vw-4rem)]",
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
				"fixed left-1/2 top-1/2 z-50 w-full -translate-x-1/2 -translate-y-1/2",
				"rounded-xl border border-dl-border bg-dl-bg-sidebar shadow-[var(--shadow-raised,0_10px_30px_rgba(0,0,0,0.16))]",
				"p-6 outline-none",
				"data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95",
				"data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95",
				sizes[size],
				className
			)}
		>
			{#if title}
				<Dialog.Title class="text-lg font-semibold text-dl-text">
					{title}
				</Dialog.Title>
			{/if}
			{#if description}
				<Dialog.Description class="mt-1.5 text-sm text-dl-text-dim">
					{description}
				</Dialog.Description>
			{/if}

			<div class="mt-4">
				{@render children()}
			</div>

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
