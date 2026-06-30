<script lang="ts">
	interface Props {
		id: string;
		title?: string;
		shorts?: boolean;
		/** 큰 미리보기(히어로용) · max-width·테두리·그림자 확대 */
		wide?: boolean;
		/** 포스터 썸네일 표시 후 클릭 시 iframe 로드 (히어로 LCP 보호) */
		facade?: boolean;
	}

	let { id, title = '', shorts = false, wide = false, facade = false }: Props = $props();

	let loaded = $state(false);
	const poster = $derived(`https://img.youtube.com/vi/${id}/maxresdefault.jpg`);
</script>

<div class="yt-wrap" class:yt-shorts={shorts} class:yt-wide={wide}>
	{#if facade && !loaded}
		<button class="yt-facade" type="button" aria-label={title || 'Play video'} onclick={() => (loaded = true)}>
			<img class="yt-poster" src={poster} alt={title} loading="lazy" />
			<span class="yt-play" aria-hidden="true">
				<svg viewBox="0 0 68 48" width="72" height="50">
					<path
						d="M66.5 7.7c-.8-2.9-2.5-5.4-5.4-6.2C55.8.1 34 0 34 0S12.2.1 6.9 1.5C4 2.3 2.3 4.8 1.5 7.7.1 13 0 24 0 24s.1 11 1.5 16.3c.8 2.9 2.5 5.4 5.4 6.2C12.2 47.9 34 48 34 48s21.8-.1 27.1-1.5c2.9-.8 4.6-3.3 5.4-6.2C66.9 35 67 24 67 24s-.1-11-1.5-16.3z"
						fill="#ea4647"
					/>
					<path d="M45 24 27 14v20z" fill="#fff" />
				</svg>
			</span>
		</button>
	{:else}
		<iframe
			src={`https://www.youtube.com/embed/${id}${facade ? '?autoplay=1' : ''}`}
			{title}
			frameborder="0"
			allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
			allowfullscreen
		></iframe>
	{/if}
</div>

<style>
	.yt-wrap {
		position: relative;
		width: 100%;
		max-width: 720px;
		margin: 1.5rem auto;
		aspect-ratio: 16 / 9;
		border-radius: 12px;
		overflow: hidden;
		background: #0a0e17;
	}

	.yt-wrap.yt-shorts {
		max-width: 360px;
		aspect-ratio: 9 / 16;
	}

	.yt-wrap.yt-wide {
		max-width: 960px;
		margin: 0 auto;
		border: 1px solid #1e2433;
		box-shadow: 0 30px 80px rgba(0, 0, 0, 0.45);
	}

	.yt-wrap iframe {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		border: none;
	}

	.yt-facade {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		padding: 0;
		border: none;
		cursor: pointer;
		background: #0a0e17;
	}

	.yt-poster {
		width: 100%;
		height: 100%;
		object-fit: cover;
		display: block;
		transition: transform 0.4s ease, opacity 0.2s ease;
	}

	.yt-facade:hover .yt-poster {
		transform: scale(1.03);
		opacity: 0.92;
	}

	.yt-play {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		pointer-events: none;
	}

	.yt-play svg {
		filter: drop-shadow(0 6px 20px rgba(0, 0, 0, 0.45));
		transition: transform 0.15s ease;
	}

	.yt-facade:hover .yt-play svg {
		transform: scale(1.08);
	}
</style>
