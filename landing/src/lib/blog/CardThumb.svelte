<script lang="ts">
	// 블로그 리스트 썸네일 · 카드뉴스(CardSlide editorial) 그대로. 흑백 이미지 위에 HTML 텍스트(굽지 않음):
	// 좌하단 kicker(● 카테고리) + 핵심키워드(숫자=테마색 accent). 모든 리스트(홈·카테고리·시리즈) 공통.
	let {
		image,
		imageWebp,
		keyword,
		kicker,
		alt = ''
	}: { image: string; imageWebp?: string; keyword: string; kicker?: string; alt?: string } = $props();

	// 숫자(+한글/기호 단위) = accent 강조 (카드뉴스 [[구절]] 근사).
	const NUM = /([0-9][0-9,.]*\s*(?:%|곳|조|억|배|위|년|개사|개월|개|만|천|건|p)?)/g;
	type Seg = { t: string; hl: boolean };
	const segs = $derived.by((): Seg[] => {
		const out: Seg[] = [];
		let last = 0;
		const re = new RegExp(NUM);
		let m: RegExpExecArray | null;
		while ((m = re.exec(keyword))) {
			if (m.index > last) out.push({ t: keyword.slice(last, m.index), hl: false });
			out.push({ t: m[0], hl: true });
			last = m.index + m[0].length;
		}
		if (last < keyword.length) out.push({ t: keyword.slice(last), hl: false });
		return out;
	});
</script>

<div class="card-thumb">
	<picture>
		{#if imageWebp}<source srcset={imageWebp} type="image/webp" />{/if}
		<img src={image} {alt} loading="lazy" decoding="async" />
	</picture>
	<div class="ct-scrim"></div>
	<div class="ct-overlay">
		{#if kicker}<span class="ct-kicker"><i></i>{kicker}</span>{/if}
		<p class="ct-kw">{#each segs as p}<span class:hl={p.hl}>{p.t}</span>{/each}</p>
	</div>
</div>

<style>
	.card-thumb {
		position: relative;
		width: 100%;
		height: 100%;
		border-radius: 10px;
		overflow: hidden;
		background: var(--dl-mkt-card);
		border: 1px solid var(--dl-mkt-border);
	}
	.card-thumb img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: cover;
		object-position: center;
	}
	/* 하단만 어둡게 · 사진은 위·중단 노출, 글씨는 아래에서 읽힘(CardSlide editorial scrim). */
	.ct-scrim {
		position: absolute;
		inset: 0;
		background: linear-gradient(180deg, rgba(3, 5, 9, 0.12) 0%, rgba(3, 5, 9, 0.34) 46%, rgba(3, 5, 9, 0.9) 100%);
	}
	.ct-overlay {
		position: absolute;
		inset: 0;
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
		padding: 0.85rem 0.95rem;
	}
	.ct-kicker {
		display: inline-flex;
		align-items: center;
		gap: 0.4em;
		font-size: 0.6rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--dl-red);
		margin-bottom: 0.5em;
	}
	.ct-kicker i {
		width: 0.45em;
		height: 0.45em;
		border-radius: 999px;
		background: var(--dl-red);
	}
	.ct-kw {
		margin: 0;
		font-size: 1rem;
		font-weight: 800;
		line-height: 1.28;
		letter-spacing: -0.01em;
		color: #f6f8fb;
		word-break: keep-all;
		display: -webkit-box;
		-webkit-box-orient: vertical;
		-webkit-line-clamp: 3;
		overflow: hidden;
	}
	.ct-kw .hl {
		color: var(--dl-red);
	}
</style>
