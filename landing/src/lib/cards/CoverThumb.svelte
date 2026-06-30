<script lang="ts">
	// 피드 썸네일 = 편집 계약의 첫 슬라이드(표지)만. 인스타 피드처럼 한 장씩 보이고, 클릭하면 포스트 모달
	// (좌 캐러셀 + 우 캡션)이 열린다. 피드에서는 스와이프/네비 없음 · 첫장만. 가벼움(계약 JSON 1개만 fetch).
	import type { DartLabRuntime } from '@dartlab/ui-contracts';
	import CardSlide from './CardSlide.svelte';
	import { loadContract, contractToCards } from './contract';
	import { heroUrl } from './media';
	import type { CarouselCard, CarouselContract, MediaIndex } from './model';

	let {
		rt,
		code,
		slug,
		corpName,
		base = '',
		media,
		onOpen
	}: {
		rt: DartLabRuntime;
		code: string;
		slug: string;
		corpName: string;
		base?: string;
		media: MediaIndex | null;
		onOpen: () => void;
	} = $props();

	// 첫 슬라이드(표지) · 계약 로드 후(슬러그 키). media 갱신 시 배경 이미지 추종(reactive).
	let cover = $state<CarouselCard | null>(null);
	let contract = $state<CarouselContract | null>(null);
	$effect(() => {
		const m = media; // 동기 읽기로 media 로드 추적(로드 후 재실행 → 이미지 해석)
		loadContract(slug).then((c) => {
			contract = c;
			if (!c) return;
			const cov = contractToCards(c, m)[0] ?? null;
			// 표지 이미지가 안 풀리면(이름 불일치 등) 회사 hero 로 폴백 · 검정 카드 방지.
			if (cov && !cov.bg) cov.bg = heroUrl(m, code);
			cover = cov;
		});
	});
	// 회사명 = 계약명 우선(미디어 displayName 누락 시 코드만 뜨던 것 교정).
	const name = $derived(contract?.name ?? corpName);
</script>

<button class="thumb" onclick={onOpen} aria-label="{name} 카드 캐러셀 열기">
	<div class="frame">
		{#if cover}<CardSlide card={cover} {rt} />{/if}
		<div class="badge">{name}{code ? ` · ${code}` : ''}</div>
		<!-- dartlab 서명 · base 무관 항상 노출(dev=퍼블릭 기준). 아바타+dartlab 만 작게(부제 'COMPANY STORY BY
		     TICKER' 제거 · 상단 헤더에 이미 dartlab. 캡처·공유 대비 최소 서명만). avatar.webp=정적(/avatar.webp). -->
		<div class="brand">
			<img src="{base}/avatar.webp" alt="" width="22" height="22" />
			<b class="bName">dartlab</b>
		</div>
		<span class="hint">카드 열기</span>
	</div>
</button>

<style>
	.thumb {
		display: block;
		width: 100%;
		padding: 0;
		border: none;
		background: none;
		cursor: pointer;
	}
	.frame {
		position: relative;
		aspect-ratio: 1080 / 1350;
		width: 100%;
		border-radius: 16px;
		overflow: hidden;
		background: #050811;
		border: 1px solid #1e2433;
		transition:
			transform 0.18s ease,
			box-shadow 0.18s ease;
	}
	.thumb:hover .frame,
	.thumb:focus-visible .frame {
		transform: translateY(-3px);
		box-shadow: 0 14px 40px rgba(0, 0, 0, 0.5);
	}
	/* 표지 본문 하단에 dartlab 서명 띠(44px) 확보 · 헤드라인/설명이 좌하단 브랜드와 겹치지 않게(서명은 본문 아래로). */
	.frame :global(.content) {
		padding-bottom: 44px;
	}
	.badge {
		position: absolute;
		top: 14px;
		right: 16px;
		font-size: 13px;
		font-weight: 700;
		color: #f1f5f9;
		padding: 6px 13px;
		background: rgba(5, 8, 17, 0.78);
		border: 1px solid rgba(232, 234, 237, 0.12);
		border-radius: 999px;
		z-index: 3;
	}
	.brand {
		position: absolute;
		left: 16px;
		bottom: 14px;
		display: flex;
		align-items: center;
		gap: 6px;
		z-index: 3;
		filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.45));
	}
	.brand img {
		opacity: 0.92;
		border-radius: 50%;
	}
	.bName {
		font-size: 12.5px;
		font-weight: 800;
		color: #f6f8fb;
		letter-spacing: -0.01em;
	}
	.hint {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 14px;
		font-weight: 700;
		color: #fff;
		background: rgba(3, 5, 9, 0.42);
		opacity: 0;
		transition: opacity 0.18s ease;
		z-index: 4;
	}
	.thumb:hover .hint,
	.thumb:focus-visible .hint {
		opacity: 1;
	}
</style>
