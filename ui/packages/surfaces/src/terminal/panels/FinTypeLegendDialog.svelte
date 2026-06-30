<script lang="ts">
	// 재무 유형 라벨 범례 · "이 유형 칩은 무슨 뜻인가". 좌측 레일 스크리너 TYPE 컬럼(유형 ⓘ)에서 연다.
	// 라벨이 실제 보이는 곳(좌측 레일) 옆에 범례를 두는 게 직관적 · 옛 위치(데이터 출처 모달)에서 분리해 옮김.
	// ★신규 능력 0: 기준은 전부 finType SSOT(FIN_TYPES)에서 라이브 렌더 · 손코딩 문안·이름 목록 금지(드리프트 0).
	//   모달 크롬은 전역 .scrimWrap/.scrModal/.scrHead/.scrClose 재사용(GradeExplainDialog 와 동일 패턴).
	import type { Lang } from '../lib/types';
	import { FIN_TYPES } from '../lib/finType';

	interface Props {
		lang: Lang;
		onClose: () => void;
	}
	let { lang, onClose }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);

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
		class="scrModal ftModal"
		role="dialog"
		aria-modal="true"
		aria-label={T('재무 유형 라벨 기준', 'Financial type label criteria')}
		onclick={(e) => e.stopPropagation()}
	>
		<div class="scrHead">
			<span class="scrTitle">{T('재무 유형 라벨 · 기준', 'FINANCIAL TYPE LABELS · CRITERIA')}</span>
			<button class="scrClose" onclick={onClose} aria-label="close">✕</button>
		</div>
		<div class="ftBody">
			<p class="ftIntro">
				{T(
					'좌측 스크리너 유형 칩은 DART 공시 기반 dartlab scan 지표(최신 사업연도 연결 기준 · 분기 갱신, 일부 라벨의 부채비율·순현금만 최신 연간 재무제표) 위에서 아래 고정 임계값을 기계 판정한 결정론 파생 라벨입니다. 추정·예측·점수화가 아니며 아래 기준식이 전부입니다. 여러 라벨을 동시에 만족하면 아래 표시 순서(위 > 아래)가 우선순위이며, 스크리너는 음(주의)축·양축 각 1개씩 표시합니다. 기준에 필요한 값이 결측이면 그 라벨은 부여하지 않습니다 · 무라벨은 해당 없음(중립)이지 부정 신호가 아닙니다. 금융업 등 일부 업종은 영업이익률·유동성 지표가 구조적으로 산출되지 않아 라벨이 제한적이며, ROE 등 수치는 최신 보고기간 기준이라 통상의 연간 지표보다 낮게 보일 수 있습니다. 본 라벨은 정보 제공 목적이며 투자 권유가 아닙니다.',
					'The type chips in the left screener are deterministic, fixed-threshold labels over dartlab scan metrics from DART filings (latest consolidated fiscal year · quarterly refresh; only a few labels’ debt ratio / net cash use the latest annual statements) · not estimates, predictions, or scores. The criteria below are exhaustive. When several match, the display order below (top > bottom) is the priority, and the screener shows one negative (caution) and one positive label. Missing inputs mean the label is not assigned · no label is "not applicable" (neutral), not a negative signal. Some sectors (e.g. financials) produce operating-margin / liquidity metrics only partially, so labels are limited there, and figures like ROE are as of the latest reporting period and can look lower than usual annual measures. Informational only · not investment advice.'
				)}
			</p>
			<div class="ftRows">
				{#each FIN_TYPES as t (t.name)}
					<div class="ftRow">
						<b class={'ft-' + t.tone}>{t.name}</b>
						<span>{T(t.criteriaKr, t.criteriaEn)}</span>
					</div>
				{/each}
			</div>
		</div>
	</div>
</div>

<style>
	.ftModal {
		width: min(640px, 96vw);
	}
	.ftBody {
		padding: 12px 14px 14px;
		max-height: min(70vh, 620px);
		overflow-y: auto;
	}
	.ftIntro {
		margin: 0 0 10px;
		font-size: 10.5px;
		line-height: 1.55;
		color: var(--dl-ink-mute, #8a93a3);
	}
	.ftRows {
		display: flex;
		flex-direction: column;
		gap: 5px;
	}
	.ftRow {
		display: flex;
		gap: 9px;
		font-size: 11px;
		line-height: 1.45;
		align-items: baseline;
	}
	.ftRow b {
		flex: 0 0 52px;
		font-weight: 700;
	}
	.ftRow span {
		color: var(--dl-ink-mute, #8a93a3);
		min-width: 0;
	}
	/* 톤 색 · 터미널 라벨 칩과 동일 팔레트(신규 색 금지) */
	.ftRow .ft-down {
		color: #f0616f;
	}
	.ftRow .ft-warn {
		color: #fbbf24;
	}
	.ftRow .ft-up {
		color: #34d399;
	}
	.ftRow .ft-good {
		color: #60a5fa;
	}
	.ftRow .ft-neutral {
		color: #cbd5e1;
	}
</style>
