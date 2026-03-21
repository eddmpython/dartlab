<!--
	CitationPopover — 인용 [1] 호버 시 소스 텍스트 프리뷰 팝오버.
	300ms hover-in 딜레이, 200ms hover-out 딜레이.
-->
<script>
	let { contexts = [], containerEl = null } = $props();

	let popover = $state({ visible: false, x: 0, y: 0, context: null });
	let hoverInTimer = null;
	let hoverOutTimer = null;

	function showPopover(el, ctx) {
		clearTimeout(hoverOutTimer);
		hoverOutTimer = null;
		if (popover.visible && popover.context === ctx) return;
		clearTimeout(hoverInTimer);
		hoverInTimer = setTimeout(() => {
			const rect = el.getBoundingClientRect();
			const containerRect = containerEl?.getBoundingClientRect() || { left: 0, top: 0 };
			popover = {
				visible: true,
				x: rect.left - containerRect.left + rect.width / 2,
				y: rect.top - containerRect.top - 4,
				context: ctx,
			};
		}, 300);
	}

	function hidePopover() {
		clearTimeout(hoverInTimer);
		hoverInTimer = null;
		hoverOutTimer = setTimeout(() => {
			popover = { ...popover, visible: false, context: null };
		}, 200);
	}

	function keepPopover() {
		clearTimeout(hoverOutTimer);
		hoverOutTimer = null;
	}

	$effect(() => {
		if (!containerEl || !contexts?.length) return;

		function onEnter(e) {
			const citeEl = e.target.closest?.(".cite-ref");
			if (!citeEl) return;
			const idx = parseInt(citeEl.dataset.cite, 10);
			if (isNaN(idx) || idx < 1 || idx > contexts.length) return;
			showPopover(citeEl, contexts[idx - 1]);
		}
		function onLeave(e) {
			const citeEl = e.target.closest?.(".cite-ref");
			if (!citeEl) return;
			hidePopover();
		}

		containerEl.addEventListener("mouseenter", onEnter, true);
		containerEl.addEventListener("mouseleave", onLeave, true);
		return () => {
			containerEl.removeEventListener("mouseenter", onEnter, true);
			containerEl.removeEventListener("mouseleave", onLeave, true);
			clearTimeout(hoverInTimer);
			clearTimeout(hoverOutTimer);
		};
	});

	let previewText = $derived.by(() => {
		if (!popover.context) return "";
		const text = popover.context.text || popover.context.content || "";
		return text.length > 150 ? text.slice(0, 150) + "…" : text;
	});
</script>

{#if popover.visible && popover.context}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="absolute z-50 w-72 rounded-xl border border-dl-border bg-dl-bg-sidebar p-3 shadow-lg shadow-black/30 text-[12px] leading-relaxed animate-fadeIn"
		style="left: {popover.x}px; top: {popover.y}px; transform: translate(-50%, -100%)"
		role="tooltip"
		onmouseenter={keepPopover}
		onmouseleave={hidePopover}
	>
		<div class="text-[10px] font-medium text-dl-accent mb-1.5 truncate">
			{popover.context.label || popover.context.module || "소스"}
		</div>
		<div class="text-dl-text-muted leading-[1.6]">{previewText}</div>
		<div class="text-[9px] text-dl-text-dim mt-1.5">클릭하면 전체 보기</div>
	</div>
{/if}
