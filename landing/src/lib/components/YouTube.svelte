<script lang="ts">
	interface Props {
		id: string;
		title?: string;
		shorts?: boolean;
	}

	let { id, title = '', shorts = false }: Props = $props();
</script>

<div class="yt-wrap" class:yt-shorts={shorts}>
	<iframe
		src="https://www.youtube.com/embed/{id}"
		{title}
		frameborder="0"
		allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
		allowfullscreen
	></iframe>
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

	.yt-wrap iframe {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		border: none;
	}
</style>
