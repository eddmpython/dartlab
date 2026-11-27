<script lang="ts">
	// 첫 화면에서 왼쪽으로 천천히 흐르는 기업이야기 표지 줄. 커서를 올리면 멈추고, 마우스로 끌어 넘기고,
	// 휴대폰은 손가락으로 넘긴다. 움직임 줄이기 설정이면 흐르지 않고 화면 밖에 있으면 멈춘다.
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { ArrowRight } from 'lucide-svelte';
	import CardThumb from '$lib/blog/CardThumb.svelte';
	import type { FeedItem } from '$lib/blog/posts';

	let {
		items,
		title = '기업이야기',
		subtitle = '공시 숫자로 읽은 회사 이야기',
		moreHref = `${base}/blog/category/company-story`
	}: { items: FeedItem[]; title?: string; subtitle?: string; moreHref?: string } = $props();

	const SPEED = 28; // px/s

	let track = $state<HTMLDivElement | null>(null);
	let animate = $state(false);

	function assetUrl(path: string) {
		return /^https?:\/\//i.test(path) ? path : `${base}${path}`;
	}

	onMount(() => {
		const el = track;
		if (!el || items.length < 2) return;
		const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
		if (reduce.matches) return;
		animate = true;

		let pos = 0;
		let last = 0;
		let frame = 0;
		let hovering = false;
		let visible = true;
		let touchHold = 0;
		let drag: { id: number; x: number; start: number; moved: boolean } | null = null;
		let suppressClick = false;

		// 한 바퀴 길이 = 사본 첫 표지와 원본 첫 표지 사이 거리. 이만큼 넘기면 처음과 같은 그림이다.
		const half = () => {
			const row = el.firstElementChild;
			const first = row?.children[0] as HTMLElement | undefined;
			const copy = row?.children[items.length] as HTMLElement | undefined;
			return first && copy ? copy.offsetLeft - first.offsetLeft : el.scrollWidth / 2;
		};
		const wrap = (value: number) => {
			const h = half();
			if (h <= 0) return value;
			return ((value % h) + h) % h;
		};
		const paused = () => hovering || !visible || drag !== null || Date.now() < touchHold || document.hidden;

		const tick = (now: number) => {
			const dt = last ? Math.min(now - last, 64) / 1000 : 0;
			last = now;
			if (!paused()) {
				pos = wrap(pos + SPEED * dt);
				el.scrollLeft = pos;
			} else {
				pos = wrap(el.scrollLeft);
			}
			frame = requestAnimationFrame(tick);
		};
		frame = requestAnimationFrame(tick);

		const observer = new IntersectionObserver(([entry]) => {
			visible = entry?.isIntersecting ?? true;
		});
		observer.observe(el);

		const onEnter = (event: PointerEvent) => {
			if (event.pointerType === 'mouse') hovering = true;
		};
		const onLeave = (event: PointerEvent) => {
			if (event.pointerType === 'mouse') hovering = false;
		};
		const onDown = (event: PointerEvent) => {
			if (event.pointerType !== 'mouse' || event.button !== 0) return;
			drag = { id: event.pointerId, x: event.clientX, start: el.scrollLeft, moved: false };
		};
		const onMove = (event: PointerEvent) => {
			if (!drag || event.pointerId !== drag.id) return;
			const dx = event.clientX - drag.x;
			if (!drag.moved && Math.abs(dx) > 5) {
				drag.moved = true;
				el.setPointerCapture(event.pointerId);
				el.classList.add('dragging');
			}
			if (drag.moved) {
				pos = wrap(drag.start - dx);
				el.scrollLeft = pos;
			}
		};
		const onUp = (event: PointerEvent) => {
			if (!drag || event.pointerId !== drag.id) return;
			suppressClick = drag.moved;
			if (el.hasPointerCapture(event.pointerId)) el.releasePointerCapture(event.pointerId);
			el.classList.remove('dragging');
			drag = null;
		};
		const onClick = (event: MouseEvent) => {
			if (suppressClick) {
				event.preventDefault();
				event.stopPropagation();
				suppressClick = false;
			}
		};
		const onTouch = () => {
			touchHold = Date.now() + 2500;
		};
		const onScroll = () => {
			// 손가락이나 휠로 넘기다 앞뒤 끝에 닿으면 같은 그림이 이어지도록 반 바퀴 옮긴다.
			const h = half();
			if (el.scrollLeft >= h) el.scrollLeft -= h;
		};

		el.addEventListener('pointerenter', onEnter);
		el.addEventListener('pointerleave', onLeave);
		el.addEventListener('pointerdown', onDown);
		el.addEventListener('pointermove', onMove);
		el.addEventListener('pointerup', onUp);
		el.addEventListener('pointercancel', onUp);
		el.addEventListener('click', onClick, true);
		el.addEventListener('touchstart', onTouch, { passive: true });
		el.addEventListener('touchmove', onTouch, { passive: true });
		el.addEventListener('wheel', onTouch, { passive: true });
		el.addEventListener('scroll', onScroll, { passive: true });

		return () => {
			cancelAnimationFrame(frame);
			observer.disconnect();
			el.removeEventListener('pointerenter', onEnter);
			el.removeEventListener('pointerleave', onLeave);
			el.removeEventListener('pointerdown', onDown);
			el.removeEventListener('pointermove', onMove);
			el.removeEventListener('pointerup', onUp);
			el.removeEventListener('pointercancel', onUp);
			el.removeEventListener('click', onClick, true);
			el.removeEventListener('touchstart', onTouch);
			el.removeEventListener('touchmove', onTouch);
			el.removeEventListener('wheel', onTouch);
			el.removeEventListener('scroll', onScroll);
		};
	});
</script>

{#snippet card(item: FeedItem, copy: boolean)}
	<!-- 표지 글씨가 글의 요점이라 아래에 제목 줄을 두지 않는다(제목은 커서를 올리면 보인다). -->
	<a
		class="strip-card"
		href="{base}/blog/{item.slug}"
		title={item.title}
		draggable="false"
		tabindex={copy ? -1 : undefined}
		aria-hidden={copy ? 'true' : undefined}
	>
		<div class="strip-thumb">
			<CardThumb
				image={assetUrl(item.cardPreview)}
				imageWebp={item.cardPreviewWebp ? assetUrl(item.cardPreviewWebp) : undefined}
				keyword={item.cardKeyword}
				kicker={item.corpName ?? item.categoryLabel}
				alt={copy ? '' : item.title}
			/>
		</div>
	</a>
{/snippet}

{#if items.length > 0}
	<section class="story-strip" aria-label={title}>
		<div class="strip-head">
			<div>
				<h2 class="strip-heading">{title}</h2>
				<p class="strip-sub">{subtitle}</p>
			</div>
			<a class="strip-more" href={moreHref}>전체 보기 <ArrowRight size={14} /></a>
		</div>
		<div class="strip-track" class:animate bind:this={track}>
			<div class="strip-row">
				{#each items as item (item.slug)}{@render card(item, false)}{/each}
				{#if animate}
					{#each items as item (`copy-${item.slug}`)}{@render card(item, true)}{/each}
				{/if}
			</div>
		</div>
	</section>
{/if}

<style>
	.story-strip {
		padding: 1rem 0 1.5rem;
	}
	.strip-head {
		max-width: 72rem;
		margin: 0 auto 0.9rem;
		padding: 0 1.5rem;
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		gap: 1rem;
	}
	.strip-heading {
		margin: 0;
		font-size: 1.25rem;
		font-weight: 800;
		color: var(--dl-ink);
	}
	.strip-sub {
		margin: 0.2rem 0 0;
		font-size: 0.85rem;
		color: var(--dl-ink-dim);
	}
	.strip-more {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--dl-ink-mute);
		text-decoration: none;
		white-space: nowrap;
	}
	.strip-more:hover {
		color: var(--dl-red);
	}
	.strip-track {
		overflow-x: auto;
		scrollbar-width: none;
		-webkit-overflow-scrolling: touch;
		mask-image: linear-gradient(90deg, transparent 0, #000 3%, #000 97%, transparent 100%);
	}
	.strip-track::-webkit-scrollbar {
		display: none;
	}
	.strip-track.animate {
		cursor: grab;
	}
	.strip-track:global(.dragging) {
		cursor: grabbing;
		user-select: none;
	}
	.strip-row {
		display: flex;
		gap: 1rem;
		width: max-content;
		padding: 0.25rem 1.5rem;
	}
	.strip-track.animate .strip-row {
		padding-right: 0;
	}
	.strip-card {
		display: block;
		width: 300px;
		flex-shrink: 0;
		color: inherit;
		text-decoration: none;
		user-select: none;
		-webkit-user-drag: none;
	}
	.strip-thumb {
		aspect-ratio: 1200 / 630;
		transition: transform 0.2s ease;
	}
	.strip-card:hover .strip-thumb {
		transform: translateY(-3px);
	}
	.strip-thumb :global(img) {
		pointer-events: none;
	}
	@media (max-width: 640px) {
		.strip-head {
			padding: 0 1rem;
		}
		.strip-row {
			padding: 0.25rem 1rem;
			gap: 0.75rem;
		}
		.strip-card {
			width: 240px;
		}
	}
</style>
