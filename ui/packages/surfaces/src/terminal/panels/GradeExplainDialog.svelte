<script lang="ts">
	// 스캔 등급 설명 다이얼로그 · "왜 이 등급인가". 좌 스파이더 / 우 근거 / 아래 기준.
	// ★신규 능력 0: 데이터(co.radar·co.verdict·co.analysis.tracks·co.credit·co.grades)는 전부 엔진 산물(공동배선
	//   = 퍼블릭·로컬 동일). 모달 크롬은 전역 .scrimWrap/.scrModal/.scrHead/.scrClose 재사용. 레이더는 map RadarChart 재사용.
	// 정직: 매수/매도 신호·목표주가·인과 금지. 결손 축은 채우지 않고 뺀다(0대체 금지). 등급 = 판정(근거+기준 동반).
	import type { Company, Lang } from '../lib/types';
	import { GRADE_SCALE } from '../lib/engine';
	import { GRADE_GUIDE, CF_PATTERN_GUIDE, CF_PATTERN_SIGNS } from '../lib/gradeGuide';
	import { txc } from '../ui/helpers';
	import RadarChart from '../../map/components/RadarChart.svelte';

	interface Props {
		co: Company;
		lang: Lang;
		onClose: () => void;
	}
	let { co, lang, onClose }: Props = $props();

	const tcls = (t: string) =>
		(({ up: 'tUp', good: 'tGood', neutral: 'tNeu', warn: 'tWarn', down: 'tDn' }) as Record<string, string>)[t] || 'tNeu';
	// 등급 톤 → 막대 색. ★터미널 기존 토큰만 사용(신규 색 금지) · --up/good/warn/dn 은 .tUp 등과 동일 팔레트.
	const TONE_COL: Record<string, string> = { up: 'var(--up)', good: 'var(--good)', neutral: 'var(--dim)', warn: 'var(--warn)', down: 'var(--dn)' };
	// 신용 구성 점수(0~100) → 같은 터미널 토큰 색(높을수록 양호). credit.tone 임계(70/49)와 정합.
	const creditCol = (s: number): string => (s >= 70 ? 'var(--up)' : s >= 50 ? 'var(--good)' : s >= 30 ? 'var(--warn)' : 'var(--dn)');

	const vd = $derived(co.verdict);
	const pct = $derived(co.percentile);
	const hasPct = $derived(!!pct && pct.n >= 5);
	// 좌측 레이더 = 순서형 종합 축 스포크. s = *축 백분위*(피어 상대, 상위일수록 큼) · 등급을 매긴 근거를 시각화.
	// cf(분류)는 엔진에서 이미 제외. 결손 축(s=null)은 스포크 생략(0대체 금지). 짧은 라벨로 겹침 완화.
	const radarAxes = $derived(
		co.radar
			.filter((r) => r.s != null)
			.map((r) => ({ label: lang === 'en' ? r.en : r.short ?? r.kr, value: (r.s as number) * 100 }))
	);

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
		class="scrModal geModal"
		role="dialog"
		aria-modal="true"
		aria-label={lang === 'en' ? 'Why this scan grade' : '스캔 등급 근거'}
		onclick={(e) => e.stopPropagation()}
	>
		<div class="scrHead">
			<span class="scrTitle">{lang === 'en' ? 'SCAN GRADE · why this grade' : '스캔 등급 · 왜 이 등급인가'}</span>
			<span class={'geBand ' + tcls(vd.band.tone)}>{txc(vd.band, lang)} <b class="mono">{vd.composite}</b></span>
			<span class="geCredit"><i>{lang === 'en' ? 'credit' : '신용'}</i> <b class="tCredit mono">{co.credit.grade}</b></span>
			<button class="scrClose" onclick={onClose} aria-label="close">✕</button>
		</div>

		<div class="geBody">
			<!-- 좌: 스파이더(레이더) -->
			<div class="geRadar">
				{#if radarAxes.length >= 3}
					<RadarChart axes={radarAxes} size={208} />
				{:else}
					<div class="geRadarEmpty">{lang === 'en' ? 'not enough graded axes for a radar' : '레이더를 그릴 등급 축 부족'}</div>
				{/if}
			</div>

			<!-- 우: 왜 이 등급(근거) · 신용 + 강점/우려. 백분위·분포곡선은 아래 등급기준의 각 축으로 이동. -->
			<div class="geWhy">
				<div class="geCred">
					<span class="geCredK">{lang === 'en' ? 'credit' : '신용'}</span>
					<b class="tCredit mono">{co.credit.grade}</b>
					<span class="geCredX">{lang === 'en' ? 'health' : '건전도'} <b class="mono">{co.credit.healthScore}/100</b></span>
					<span class="geCredX">PD <b class="mono">{co.credit.pd}</b></span>
				</div>
				{#if vd.strengths.length}
					<div class="geGroup">
						<span class="geGl tUp">{lang === 'en' ? 'Strengths' : '강점'}</span>
						{#each vd.strengths as s}<span class="geTag up">{txc(s, lang)}</span>{/each}
					</div>
				{/if}
				{#if vd.concerns.length}
					<div class="geGroup">
						<span class="geGl tDn">{lang === 'en' ? 'Concerns' : '우려'}</span>
						{#each vd.concerns as c}<span class="geTag dn">{txc(c, lang)}</span>{/each}
					</div>
				{/if}
				<!-- 신용등급(dCR) 구성 · 레이더 우측 여백 채움 + 헤더 신용등급의 근거(5요소 0~100). -->
				{#if co.credit.tracks?.length}
					<div class="geCredTracks">
						<span class="geGl">{lang === 'en' ? 'Credit factors' : '신용 구성'}</span>
						{#each co.credit.tracks as t (t.en)}
							<div class="geCt">
								<span class="geCtL">{txc(t, lang)}</span>
								<div class="geCtTrack"><div class="geCtBar" style={`width:${Math.max(2, t.score)}%;background:${creditCol(t.score)}`}></div></div>
								<span class="geCtV mono">{t.score}</span>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>

		<!-- 아래: 등급 기준 · 각 종합 축의 동종업종 백분위(상위 N%) + 등급레벨 분포 막대 = 그 등급을 매긴 근거. -->
		<div class="geCriteria">
			<div class="geCrHead">
				{lang === 'en' ? 'Grade criteria' : '등급 기준'}{#if hasPct && pct} · {lang === 'en' ? `vs ${pct.n} peers` : `업종 ${pct.n}개사 내 위치`}{#if co.eco.industryRank != null} ({co.eco.industryRank}{lang === 'en' ? '' : '위'}){/if}{/if}
			</div>
			<div class="geCrGrid">
				{#each co.grades as g (g.key)}
					{@const isClass = g.kind === 'class'}
					{@const scale = GRADE_SCALE[g.key] || []}
					{@const guide = GRADE_GUIDE[g.key]}
					{@const cfg = isClass ? CF_PATTERN_GUIDE[g.v] : null}
					{@const hasDist = !isClass && (g.peerN ?? 0) >= 5 && !!(g.dist && g.dist.length)}
					<div class="geCr">
						<!-- 타이틀 = 종합 축명. 우측 = 등급 pill + "업종 상위 N%"(축 자체의 동종사 백분위 = 등급 근거). -->
						<div class="geCrTop">
							<span class="geCrTitle">{txc(g, lang)}</span>
							{#if isClass}
								<span class={'geCrPill ' + tcls(g.tone)}>{g.v}</span>
								{#if g.sameShare != null}<span class="geCrRank mono">{lang === 'en' ? `${g.sameShare}% of peers` : `같은 유형 ${g.sameShare}%`}</span>{/if}
							{:else if g.topPct != null}
								<span class="geCrRank mono">{lang === 'en' ? 'top ' : '업종 상위 '}{g.topPct}%</span>
							{/if}
						</div>
						{#if isClass}
							{@const signs = CF_PATTERN_SIGNS[g.v]}
							<!-- 영업·투자·재무 현금흐름 부호(+유입 / −유출) · 패턴을 정의하는 직관적 표기 -->
							{#if signs}
								<div class="geCfFlow">
									{#each [['영업', 'Op'], ['투자', 'Inv'], ['재무', 'Fin']] as lbl, i (i)}
										<div class={'geCfCell ' + (signs[i] === '+' ? 'pos' : 'neg')}>
											<span class="geCfL">{lang === 'en' ? lbl[1] : lbl[0]}</span>
											<span class="geCfS">{signs[i]}</span>
										</div>
									{/each}
								</div>
							{/if}
							<!-- C(분류): 순서 없음 → 사다리·순위 금지. 패턴 설명 + 유형 표기만(거짓 순서 방지). -->
							{#if cfg}<div class="geCrWhat">{lang === 'en' ? cfg.en : cfg.kr}</div>{/if}
							<div class="geCrType">{lang === 'en' ? `category · not a ranking${g.peerN ? ` · ${g.peerN} peers` : ''}` : `유형 · 순위 아님${g.peerN ? ` · 업종 ${g.peerN}개사` : ''}`}</div>
						{:else}
							{#if guide}<div class="geCrWhat">{lang === 'en' ? guide.en.what : guide.kr.what}</div>{/if}
							{#if hasDist}
								{@const maxShare = Math.max(...(g.dist ?? []).map((d) => d.share), 1)}
								<!-- 등급레벨별 동종사 분포 막대(최댓값 기준 정규화) + 회사 등급 칼럼 하이라이트 -->
								<div class="geDist">
									{#each g.dist ?? [] as d (d.step)}
										<div class={'geDc' + (d.step === g.v ? ' on' : '')} title={`${d.step} · 업종 ${d.share}%`}>
											<div class="geDcTrack"><div class="geDcBar" style={`height:${d.share === 0 ? 0 : Math.max(10, Math.round((d.share / maxShare) * 100))}%${d.step === g.v ? `;background:${TONE_COL[d.tone] ?? '#8b949e'}` : ''}`}></div></div>
											<span class="geDcStep">{d.step}</span>
											<span class="geDcPct mono">{d.share}%</span>
										</div>
									{/each}
								</div>
							{:else}
								<!-- 피어 부족(로컬 단일사 등) · 단순 사다리 폴백 -->
								<div class="geLadder">
									{#each scale as step}<span class={'geStep' + (step === g.v ? ' on' : '')}>{step}</span>{/each}
								</div>
							{/if}
						{/if}
					</div>
				{/each}
			</div>
			<div class="geNote">
				{lang === 'en'
					? '※ "·" means that figure is absent from this company’s filings (not filled with 0). The composite verdict uses 5 bands plus a continuous 0-100 score (top); credit dCR (14 bands) is a separate scale. Cash flow is a category (8 patterns), so it has no ladder or ranking. A grade is an assessment with criteria · not a buy/sell signal.'
					: '※ "·" 는 해당 수치가 이 회사 공시에 없다는 뜻(0으로 채우지 않음). 종합 판정은 5밴드 + 연속 0~100 점수(상단)·신용 dCR(14단)은 별도 스케일. 현금흐름은 8가지 유형(순서 없음)이라 등급 사다리·순위가 없다. 등급은 기준에 따른 판정이며 매수/매도 신호가 아니다.'}
			</div>
		</div>
	</div>
</div>

<style>
	.geModal {
		width: min(810px, 96vw);
	}
	.geBand {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.02em;
	}
	.geBand b {
		margin-left: 4px;
		font-size: 12px;
	}
	.geCredit {
		font-size: 10px;
		color: var(--dl-ink-dim, #5b6473);
	}
	.geCredit i {
		font-style: normal;
		margin-right: 3px;
	}
	.geBody {
		display: flex;
		gap: 16px;
		padding: 14px 14px 6px;
		align-items: flex-start;
		flex: 0 0 auto; /* 헤더·레이더·신용 구성은 고정 · 아래 등급기준만 스크롤 */
	}
	.geRadar {
		flex: 0 0 224px;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 6px;
	}
	.geRadarEmpty {
		width: 208px;
		height: 208px;
		display: flex;
		align-items: center;
		justify-content: center;
		text-align: center;
		font-size: 11px;
		color: var(--dl-ink-dim, #5b6473);
		border: 1px dashed var(--dl-line, #1b2130);
		border-radius: 6px;
	}
	.geWhy {
		flex: 1 1 auto;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 9px;
	}
	.geGroup {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 5px;
	}
	.geGl {
		font-size: 10px;
		font-weight: 700;
		margin-right: 2px;
	}
	.geTag {
		font-size: 11px;
		padding: 2px 7px;
		border-radius: 10px;
		border: 1px solid var(--dl-line, #1b2130);
		background: rgba(255, 255, 255, 0.02);
	}
	.geTag.up {
		border-color: rgba(52, 211, 153, 0.35);
	}
	.geTag.dn {
		border-color: rgba(234, 70, 71, 0.35);
	}
	.geCriteria {
		border-top: 1px solid var(--dl-line, #1b2130);
		padding: 10px 14px 14px;
		background: rgba(255, 255, 255, 0.012);
		flex: 1 1 auto; /* 남은 높이 차지 + 넘치면 스크롤(모달 잘림 방지) */
		min-height: 0;
		overflow-y: auto;
	}
	.geCrHead {
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 0.04em;
		color: var(--dl-ink-dim, #5b6473);
		margin-bottom: 8px;
	}
	.geCrGrid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(176px, 1fr));
		gap: 12px 14px;
		align-items: start;
	}
	.geCr {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.geCrWhat {
		font-size: 10px;
		color: var(--dl-ink-dim, #5b6473);
		line-height: 1.4;
	}
	.geLadder {
		display: flex;
		flex-wrap: wrap;
		gap: 3px;
		margin-top: 1px;
	}
	.geStep {
		font-size: 9px;
		padding: 1px 5px;
		border-radius: 7px;
		color: var(--dl-ink-dim, #5b6473);
		background: rgba(255, 255, 255, 0.03);
	}
	.geStep.on {
		color: var(--dl-bg-raised, #0e141f);
		background: var(--color-dl-primary, #ea4647);
		font-weight: 700;
	}
	.geNote {
		font-size: 9.5px;
		color: var(--dl-ink-dim, #5b6473);
		line-height: 1.5;
		margin-top: 10px;
	}
	/* 등급기준 · 종합 축 1개당 1블록(축명 · 등급 pill · 업종 상위 N% + 등급레벨 분포 막대) */
	.geCrTop {
		display: flex;
		align-items: baseline;
		gap: 6px;
	}
	.geCrTitle {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.02em;
	}
	.geCrRank {
		font-size: 10px;
		color: var(--dl-ink-dim, #5b6473);
		font-variant-numeric: tabular-nums;
	}
	/* 등급 pill · 축의 현재 등급(톤 색). 우측 정렬(상위% 가 뒤따름) */
	.geCrPill {
		margin-left: auto;
		font-size: 10.5px;
		font-weight: 700;
		padding: 1px 7px;
		border-radius: 9px;
		border: 1px solid var(--dl-line, #1b2130);
		background: rgba(255, 255, 255, 0.03);
		white-space: nowrap;
	}
	.geCrType {
		font-size: 9px;
		font-style: italic;
		color: var(--dl-ink-dim, #5b6473);
	}
	/* 현금흐름 부호 행 · 영업/투자/재무 +유입(--up)/−유출(--dn) 직관 표기(터미널 토큰) */
	.geCfFlow {
		display: flex;
		gap: 5px;
		margin-top: 3px;
	}
	.geCfCell {
		flex: 1 1 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1px;
		padding: 4px 0;
		border-radius: 4px;
		background: rgba(139, 148, 158, 0.1);
		border: 1px solid var(--dl-line, #1b2130);
	}
	.geCfL {
		font-size: 8.5px;
		color: var(--dl-ink-dim, #5b6473);
	}
	.geCfS {
		font-size: 15px;
		font-weight: 700;
		line-height: 1;
	}
	.geCfCell.pos .geCfS {
		color: var(--up);
	}
	.geCfCell.neg .geCfS {
		color: var(--dn);
	}
	/* 등급레벨별 동종사 분포 막대 · 막대높이 = 동종사 비중%, 회사 등급 칼럼 하이라이트 */
	.geDist {
		display: flex;
		align-items: flex-end;
		gap: 3px;
		margin-top: 2px;
	}
	.geDc {
		flex: 1 1 0;
		min-width: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
	}
	.geDcTrack {
		width: 100%;
		height: 44px;
		display: flex;
		align-items: flex-end;
		border-bottom: 1px solid var(--dl-line, #1b2130);
	}
	.geDcBar {
		width: 100%;
		min-width: 0;
		background: rgba(139, 148, 158, 0.26); /* 기본 = 회색(분포 형태만) · 회사 칼럼만 톤색(인라인)으로 구분 */
		border-radius: 2px 2px 0 0;
		transition: height 0.2s;
	}
	.geDcStep {
		font-size: 9px;
		color: var(--dl-ink-dim, #5b6473);
		max-width: 100%;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.geDc.on .geDcStep {
		color: var(--dl-ink, #c8cfdb);
		font-weight: 700;
	}
	.geDcPct {
		font-size: 9px;
		color: var(--dl-ink-dim, #5b6473);
		font-variant-numeric: tabular-nums;
	}
	.geDc.on .geDcPct {
		color: var(--dl-ink, #c8cfdb);
		font-weight: 700;
	}
	.geCred {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 10.5px;
		padding-top: 2px;
		border-top: 1px dashed var(--dl-line, #1b2130);
	}
	.geCredK {
		font-size: 10px;
		color: var(--dl-ink-dim, #5b6473);
	}
	.geCredX {
		font-size: 10px;
		color: var(--dl-ink-dim, #5b6473);
		font-variant-numeric: tabular-nums;
	}
	.geCredX b {
		color: var(--dl-ink, #c8cfdb);
	}
	/* 신용 구성 · 레이더 우측 여백 채움(dCR 등급 근거 5요소 0~100) */
	.geCredTracks {
		display: flex;
		flex-direction: column;
		gap: 3px;
		margin-top: 2px;
		padding-top: 6px;
		border-top: 1px dashed var(--dl-line, #1b2130);
	}
	.geCt {
		display: flex;
		align-items: center;
		gap: 7px;
	}
	.geCtL {
		flex: 0 0 64px;
		font-size: 10px;
		color: var(--dl-ink-dim, #5b6473);
	}
	.geCtTrack {
		flex: 1 1 auto;
		height: 7px;
		border-radius: 4px;
		background: rgba(139, 148, 158, 0.14);
		overflow: hidden;
	}
	.geCtBar {
		height: 100%;
		border-radius: 4px; /* 색은 점수 톤(인라인, 터미널 토큰) */
	}
	.geCtV {
		flex: 0 0 22px;
		text-align: right;
		font-size: 10px;
		color: var(--dl-ink, #c8cfdb);
		font-variant-numeric: tabular-nums;
	}
</style>
