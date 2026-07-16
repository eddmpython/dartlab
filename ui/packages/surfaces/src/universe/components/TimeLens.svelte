<script lang="ts">
	interface Props {
		validAt: string | null;
		knownAt: string | null;
		onChange: (validAt: string | null, knownAt: string | null) => void;
	}

	let { validAt, knownAt, onChange }: Props = $props();

	function value(event: Event): string | null {
		return (event.currentTarget as HTMLInputElement).value || null;
	}
</script>

<section class="timeLens" aria-label="시간 렌즈">
	<div class="title"><span>TIME LENS</span><p>사건의 유효 시점과 당시 알 수 있었던 시점을 독립적으로 자릅니다.</p></div>
	<label><span>VALID AT</span><input type="date" value={validAt ?? ''} onchange={(event) => onChange(value(event), knownAt)} /></label>
	<label><span>KNOWN AT</span><input type="date" value={knownAt ?? ''} onchange={(event) => onChange(validAt, value(event))} /></label>
	{#if validAt && knownAt && validAt !== knownAt}<b title="유효 시점과 인지 시점이 다릅니다">REVISION</b>{/if}
	<button onclick={() => onChange(null, null)}>초기화</button>
</section>

<style>
	.timeLens { display: grid; grid-template-columns: minmax(180px, 1fr) auto auto auto auto; gap: 9px; align-items: end; padding: 12px 14px; border-top: 1px solid #172231; background: #090e16; }
	.title span, label span { display: block; color: #53657d; font: 600 7px/1 ui-monospace, monospace; letter-spacing: .1em; }
	.title p { margin: 5px 0 0; color: #68798f; font-size: 9px; }
	label input { margin-top: 5px; border: 1px solid #213047; border-radius: 6px; padding: 6px 7px; color: #aebbd0; background: #0c131e; color-scheme: dark; font-size: 9px; }
	b { align-self: center; padding: 5px 7px; border: 1px solid rgba(115,173,244,.28); border-radius: 999px; color: #73adf4; font: 600 7px/1 ui-monospace, monospace; }
	button { border: 0; padding: 7px; color: #718198; background: none; font-size: 9px; cursor: pointer; }
	@media (max-width: 700px) { .timeLens { grid-template-columns: 1fr 1fr; } .title { grid-column: 1 / -1; } }
</style>
