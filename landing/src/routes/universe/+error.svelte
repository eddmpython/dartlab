<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/state';

	function retry(): void {
		window.location.reload();
	}
</script>

<svelte:head>
	<title>Universe를 불러오지 못했습니다 · DartLab</title>
	<meta name="robots" content="noindex,nofollow" />
</svelte:head>

<main>
	<span>UNIVERSE RECOVERY</span>
	<h1>데이터 무결성을 확인하지 못했습니다.</h1>
	<p>불완전한 장면을 표시하지 않고 안전하게 중단했습니다. 잠시 뒤 다시 시도하거나 정상 운영 중인 시장 지도를 이용해 주세요.</p>
	<div class="actions">
		<button onclick={retry}>다시 불러오기</button>
		<a href={`${base}/map`}>시장 지도 열기</a>
		<a href={`${base}/`}>홈으로</a>
	</div>
	<small>오류 코드 {page.status}</small>
</main>

<style>
	main { min-height: 100vh; display: grid; align-content: center; justify-items: start; padding: 70px clamp(24px, 8vw, 140px); color: #dce5f2; background: radial-gradient(circle at 72% 20%, rgba(177,73,73,.13), transparent 32%), #070a11; font-family: 'Pretendard Variable', Pretendard, system-ui, sans-serif; }
	main > span { color: #e18a8a; font: 600 9px/1 ui-monospace, monospace; letter-spacing: .14em; }
	h1 { max-width: 760px; margin: 18px 0 12px; font-size: clamp(34px, 5vw, 64px); line-height: 1.05; }
	p { max-width: 640px; color: #8191a7; line-height: 1.7; }
	.actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 20px; }
	button, a { border: 1px solid #2b3c54; border-radius: 8px; padding: 10px 14px; color: #cbd7e5; background: #101925; font: inherit; font-size: 12px; text-decoration: none; cursor: pointer; }
	button { border-color: #46658d; background: #17263a; }
	small { margin-top: 30px; color: #596a80; font: 500 9px/1 ui-monospace, monospace; }
</style>
