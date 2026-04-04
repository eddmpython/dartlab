<!--
	PanelResizer — 패널 경계 드래그 리사이저.
	드래그 핸들을 렌더링하고, 마우스 이벤트로 부모에 delta를 전달.
-->
<script>
	let {
		direction = "horizontal",  // "horizontal" | "vertical"
		onResize,                  // (delta: number) => void
		class: className = "",
	} = $props();

	let isDragging = $state(false);
	let startPos = 0;

	function handlePointerDown(e) {
		e.preventDefault();
		isDragging = true;
		startPos = direction === "horizontal" ? e.clientX : e.clientY;

		const handlePointerMove = (ev) => {
			if (!isDragging) return;
			const current = direction === "horizontal" ? ev.clientX : ev.clientY;
			const delta = current - startPos;
			if (delta !== 0) {
				onResize?.(delta);
				startPos = current;
			}
		};

		const handlePointerUp = () => {
			isDragging = false;
			window.removeEventListener("pointermove", handlePointerMove);
			window.removeEventListener("pointerup", handlePointerUp);
		};

		window.addEventListener("pointermove", handlePointerMove);
		window.addEventListener("pointerup", handlePointerUp);
	}
</script>

<div
	class="panel-resizer {direction} {isDragging ? 'active' : ''} {className}"
	onpointerdown={handlePointerDown}
	role="separator"
	aria-orientation={direction}
	tabindex="-1"
></div>

<style>
	.panel-resizer {
		position: relative;
		flex-shrink: 0;
		z-index: 10;
		touch-action: none;
		user-select: none;
	}
	.panel-resizer.horizontal {
		width: 5px;
		cursor: col-resize;
		margin: 0 -2px;
	}
	.panel-resizer.vertical {
		height: 5px;
		cursor: row-resize;
		margin: -2px 0;
	}
	/* 시각적 핸들 라인 */
	.panel-resizer::after {
		content: "";
		position: absolute;
		border-radius: 2px;
		background: var(--color-dl-border);
		opacity: 0;
		transition: opacity 0.15s ease;
	}
	.panel-resizer.horizontal::after {
		top: 50%;
		left: 50%;
		width: 2px;
		height: 32px;
		transform: translate(-50%, -50%);
	}
	.panel-resizer.vertical::after {
		top: 50%;
		left: 50%;
		width: 32px;
		height: 2px;
		transform: translate(-50%, -50%);
	}
	.panel-resizer:hover::after,
	.panel-resizer.active::after {
		opacity: 0.6;
	}
	.panel-resizer.active::after {
		background: var(--color-dl-accent);
		opacity: 0.8;
	}
	.panel-resizer.active {
		will-change: transform;
	}
</style>
