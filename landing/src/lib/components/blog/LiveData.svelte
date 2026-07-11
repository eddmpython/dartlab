<script lang="ts">
	/**
	 * dartlab 이야기 본문의 라이브 데이터 표. 브라우저 안 dartlab(/pyapi)에서 최신 값을 읽는다.
	 * 빌드타임 스냅샷(CompanyFinancials)과 달리, 최신 분기·전상장사 횡단처럼 "지금 값" 이 요점일 때 쓴다.
	 *
	 * 저자는 .md 에서: <LiveData spec="company/005930/panel/IS" caption="삼성전자 손익" /> 로 쓴다.
	 * spec 은 공개 계약(엔진 축)만 통과한다(resolveEndpoint). 계약 밖이면 오류 박스만 뜬다.
	 */
	import { onMount } from 'svelte';
	import { fetchLive, renderLiveTable } from '$lib/pyapi/liveData';
	import '$lib/pyapi/liveData.css';

	let {
		spec,
		caption = undefined,
		max = 20
	}: { spec: string; caption?: string; max?: number } = $props();

	let html = $state('<div class="ld-box"><span class="ld-loading">라이브 데이터 로딩...</span></div>');

	onMount(() => {
		let alive = true;
		void fetchLive(spec).then((result) => {
			if (alive) html = renderLiveTable(result, { caption, max });
		});
		return () => {
			alive = false;
		};
	});
</script>

<!-- renderLiveTable 이 모든 셀을 이스케이프하므로 @html 안전. -->
<div class="ld-wrap">{@html html}</div>
