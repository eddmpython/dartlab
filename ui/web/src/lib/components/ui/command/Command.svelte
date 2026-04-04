<script>
	import { Command, Dialog } from "bits-ui";
	import { cn } from "$lib/utils.js";
	import { Search } from "lucide-svelte";

	let {
		open = $bindable(false),
		placeholder = "검색...",
		emptyText = "결과가 없습니다.",
		class: className,
		children,
		...restProps
	} = $props();
</script>

<Dialog.Root bind:open>
	<Dialog.Portal>
		<Dialog.Overlay
			class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm
				data-[state=open]:animate-in data-[state=open]:fade-in-0
				data-[state=closed]:animate-out data-[state=closed]:fade-out-0"
		/>
		<Dialog.Content
			class={cn(
				"fixed left-1/2 top-[20%] z-50 w-full max-w-lg -translate-x-1/2",
				"rounded-xl border border-dl-border bg-dl-bg-sidebar",
				"shadow-[var(--shadow-overlay,0_24px_64px_rgba(0,0,0,0.34))] outline-none",
				"data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95",
				"data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95",
				className
			)}
		>
			<Command.Root class="flex h-full w-full flex-col overflow-hidden" {...restProps}>
				<div class="flex items-center gap-2 border-b border-dl-border px-3">
					<Search size={16} class="shrink-0 text-dl-text-dim" />
					<Command.Input
						{placeholder}
						class="flex h-11 w-full bg-transparent text-sm text-dl-text
							placeholder:text-dl-text-dim outline-none disabled:opacity-50"
					/>
				</div>
				<Command.List class="max-h-[300px] overflow-y-auto p-1">
					<Command.Empty class="py-6 text-center text-sm text-dl-text-dim">
						{emptyText}
					</Command.Empty>
					{@render children()}
				</Command.List>
			</Command.Root>
		</Dialog.Content>
	</Dialog.Portal>
</Dialog.Root>
