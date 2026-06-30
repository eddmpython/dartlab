<script lang="ts">
	// 리스크 경고등 · "무엇을 점검하고 이 회사는 어디에 걸렸나" 설명 다이얼로그.
	// 글랜스 패널(RISK FLAGS)은 *점등(red/yellow)만* 보이는 반면, 여기선 점검 차원 *전체*(통과·판정불가 포함)와
	// 켜지는 조건·임계·데이터 소스를 한 카탈로그로 가르친다. ★신규 능력 0: co.riskCatalog 는 엔진 산물(riskRules SSOT).
	// 정직: 결정론 · 임계초과만(글랜스) · 완결성 점검 아님 · 매수/매도 신호 아님 · 인과 단정 금지 · "·"=공시 부재.
	// 등급 *산식 자체*는 '스캔 등급' 다이얼로그 소관 · 여기선 복제하지 않고 참조만(GRADE_GUIDE SSOT 단일소스).
	import type { Company, Lang } from '../lib/types';

	interface Props {
		co: Company;
		lang: Lang;
		onClose: () => void;
	}
	let { co, lang, onClose }: Props = $props();

	const cat = $derived(co.riskCatalog ?? []);
	const redN = $derived(cat.filter((r) => r.status === 'red').length);
	const yellowN = $derived(cat.filter((r) => r.status === 'yellow').length);

	// 현상태 표기 · red/yellow 점등 · clear 통과 · na 판정불가. 톤은 터미널 기존 토큰만.
	const statusMeta: Record<string, { dot: string; cls: string; kr: string; en: string }> = {
		red: { dot: '●', cls: 'tDn', kr: '위험', en: 'RED' },
		yellow: { dot: '●', cls: 'tWarn', kr: '주의', en: 'WATCH' },
		clear: { dot: '○', cls: 'dim', kr: '통과', en: 'clear' },
		na: { dot: '·', cls: 'dimmer', kr: '판정불가', en: 'n/a' }
	};

	$effect(() => {
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') onClose();
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});
</script>

<div class="scrimWrap" role="presentation" onclick={onClose}>
	<div
		class="scrModal rfModal"
		role="dialog"
		aria-modal="true"
		aria-label={lang === 'en' ? 'Risk flags · dimensions checked' : '리스크 경고등 · 점검 차원'}
		onclick={(e) => e.stopPropagation()}
	>
		<div class="scrHead">
			<span class="scrTitle">{lang === 'en' ? 'RISK FLAGS · dimensions checked' : '리스크 경고등 · 점검 차원'}</span>
			<span class="rfSummary"><b class="tDn">{redN}</b> {lang === 'en' ? 'red' : '위험'} · <b class="tWarn">{yellowN}</b> {lang === 'en' ? 'watch' : '주의'} <span class="dim">/ {cat.length} {lang === 'en' ? 'checked' : '점검'}</span></span>
			<button class="scrClose" onclick={onClose} aria-label="close">✕</button>
		</div>

		<div class="rfBody">
			<div class="rfHd">
				<span class="rfHDim">{lang === 'en' ? 'DIMENSION' : '차원'}</span>
				<span class="rfHWhat">{lang === 'en' ? 'WHAT IT WATCHES' : '무엇을 보나'}</span>
				<span class="rfHCond">{lang === 'en' ? 'TRIGGER · SOURCE' : '켜지는 조건 · 소스'}</span>
				<span class="rfHNow">{lang === 'en' ? 'THIS COMPANY' : '이 회사'}</span>
			</div>
			{#each cat as r (r.id)}
				{@const sm = statusMeta[r.status]}
				<div class={'rfRow rf-' + r.status}>
					<span class="rfDim"><b>{lang === 'en' ? r.en : r.kr}</b></span>
					<span class="rfWhat">{lang === 'en' ? r.whatEn : r.whatKr}</span>
					<span class="rfCond">
						<span class="rfCondT">{lang === 'en' ? r.thresholdEn : r.thresholdKr}</span>
						<span class="rfSrc mono">{r.source}{#if r.axis} · {lang === 'en' ? 'grade basis → SCAN GRADE dialog' : '등급 산식 → 스캔 등급 다이얼로그'}{/if}</span>
					</span>
					<span class="rfNow">
						<span class={'rfDot ' + sm.cls}>{sm.dot}</span>
						<b class={sm.cls}>{lang === 'en' ? sm.en : sm.kr}</b>
						{#if r.d}<span class="rfVal mono">{r.d}</span>{/if}
					</span>
				</div>
			{/each}

			<div class="rfCohab">
				{lang === 'en'
					? 'RISK FLAGS = scan-ecosystem grades & ratios. FORENSIC FLAGS (separate panel) = audit-fee independence & near-term debt wall from the annual report · different source, so a separate panel.'
					: 'RISK FLAGS = scan ecosystem 등급·비율. FORENSIC FLAGS(별도 패널) = 정기보고서 감사보수 독립성·단기 상환벽 비율 · 출처가 달라 별 패널.'}
			</div>
			<div class="rfNote">
				{lang === 'en'
					? '※ Deterministic threshold checks. The glance panel shows breached flags only · this is NOT a completeness check, NOT a buy/sell signal, and asserts no causation. "·" means the figure is absent from filings (not filled with 0). A grade is an assessment with criteria.'
					: '※ 결정론 임계 점검. 글랜스 패널은 초과한 것만 표시 · 완결성 점검이 아니며, 매수/매도 신호가 아니고, 인과를 단정하지 않는다. "·" 는 해당 수치가 공시에 없다는 뜻(0으로 채우지 않음). 등급은 기준에 따른 판정이다.'}
			</div>
		</div>
	</div>
</div>

<style>
	.rfModal {
		width: min(860px, 96vw);
	}
	.rfSummary {
		font-size: 10.5px;
		color: var(--dim, #8b919e);
		white-space: nowrap;
	}
	.rfSummary b {
		font-weight: 700;
	}
	.rfBody {
		padding: 10px 14px 14px;
		overflow-y: auto;
		min-height: 0;
	}
	.rfHd,
	.rfRow {
		display: grid;
		grid-template-columns: 116px 1fr 1.35fr 132px;
		gap: 10px;
		align-items: start;
		padding: 7px 6px;
	}
	.rfHd {
		font-size: 8.5px;
		font-weight: 700;
		letter-spacing: 0.06em;
		color: var(--dimmer, #6b7280);
		border-bottom: 1px solid var(--bd, #1b2130);
		padding-bottom: 5px;
	}
	.rfRow {
		border-bottom: 1px solid var(--bd, rgba(48, 58, 78, 0.4));
	}
	/* 점등 행만 미세 배경 · 통과/판정불가는 무채색(글랜스의 '초과만' 정신을 다이얼로그에서도 톤으로 유지) */
	.rfRow.rf-red {
		background: rgba(240, 97, 111, 0.06);
	}
	.rfRow.rf-yellow {
		background: rgba(251, 191, 36, 0.05);
	}
	.rfDim b {
		font-size: 11px;
		font-weight: 700;
		color: var(--txt, #cfd3dc);
	}
	.rfWhat {
		font-size: 10px;
		line-height: 1.4;
		color: var(--dim, #8b919e);
	}
	.rfCond {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.rfCondT {
		font-size: 9.5px;
		line-height: 1.4;
		color: var(--dim, #8b919e);
	}
	.rfSrc {
		font-size: 8px;
		color: var(--dimmer, #6b7280);
	}
	.rfNow {
		display: flex;
		align-items: baseline;
		flex-wrap: wrap;
		gap: 4px;
		font-size: 10px;
	}
	.rfDot {
		font-size: 9px;
		line-height: 1;
	}
	.rfNow b {
		font-weight: 700;
		font-size: 10px;
	}
	.rfVal {
		font-size: 9px;
		color: var(--dim, #8b919e);
		font-variant-numeric: tabular-nums;
	}
	.dimmer {
		color: var(--dimmer, #6b7280);
	}
	.rfCohab {
		margin-top: 12px;
		padding: 8px 10px;
		border: 1px solid var(--bd, #1b2130);
		border-radius: 4px;
		background: rgba(255, 255, 255, 0.012);
		font-size: 9.5px;
		line-height: 1.5;
		color: var(--dim, #8b919e);
	}
	.rfNote {
		margin-top: 10px;
		font-size: 9.5px;
		line-height: 1.55;
		color: var(--dimmer, #6b7280);
	}
</style>
