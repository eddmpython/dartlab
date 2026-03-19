<!--
	InsightDashboard — 7영역 인사이트 등급 대시보드.
	등급 카드 그리드 + 이상치 경고 배너.
	카드 클릭 → details 펼침 (risks/opportunities).
-->
<script>
	import { AlertTriangle, TrendingUp, Shield, Wallet, Users, AlertCircle, Sparkles, ChevronDown, ChevronUp, Loader2, ExternalLink } from "lucide-svelte";
	import { insightToRadarSpec } from "$lib/chart/specs.js";

	let {
		data = null,       // insights API response
		loading = false,
		corpName = '',     // 기업명 (레이더 차트 제목용)
		onNavigateTopic = null,  // (topic) => void — P8: 관련 topic으로 이동
		toc = null,        // B4: toc 데이터 — topic 존재 여부 체크용
	} = $props();

	let expandedArea = $state(null);

	const AREA_META = {
		performance:   { label: "실적",   icon: TrendingUp },
		profitability: { label: "수익성", icon: Sparkles },
		health:        { label: "건전성", icon: Shield },
		cashflow:      { label: "현금흐름", icon: Wallet },
		governance:    { label: "지배구조", icon: Users },
		risk:          { label: "리스크", icon: AlertTriangle },
		opportunity:   { label: "기회",   icon: TrendingUp },
	};

	// P8: 등급 영역 → 관련 topics 매핑
	const RELATED_TOPICS = {
		performance:   ["salesOrder", "businessOverview"],
		profitability: ["IS", "CIS", "ratios"],
		health:        ["BS", "contingentLiability", "corporateBond"],
		cashflow:      ["CF", "ratios"],
		governance:    ["majorShareholder", "audit", "dividend"],
		risk:          ["contingentLiability", "riskFactors", "corporateBond"],
		opportunity:   ["businessOverview", "investmentOverview"],
	};

	function gradeColor(grade) {
		if (grade === "A") return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
		if (grade === "B") return "bg-blue-500/15 text-blue-400 border-blue-500/30";
		if (grade === "C") return "bg-amber-500/15 text-amber-400 border-amber-500/30";
		if (grade === "D") return "bg-orange-500/15 text-orange-400 border-orange-500/30";
		if (grade === "F") return "bg-red-500/15 text-red-400 border-red-500/30";
		return "bg-dl-border/10 text-dl-text-dim border-dl-border/20";
	}

	function gradeBadgeColor(grade) {
		if (grade === "A") return "bg-emerald-500 text-white";
		if (grade === "B") return "bg-blue-500 text-white";
		if (grade === "C") return "bg-amber-500 text-white";
		if (grade === "D") return "bg-orange-500 text-white";
		if (grade === "F") return "bg-red-500 text-white";
		return "bg-dl-border text-dl-text-dim";
	}

	function riskColor(level) {
		if (level === "danger") return "text-red-400";
		if (level === "warning") return "text-amber-400";
		return "text-dl-text-dim";
	}

	function oppColor(level) {
		if (level === "strong") return "text-emerald-400";
		return "text-blue-400";
	}

	function toggleArea(key) {
		expandedArea = expandedArea === key ? null : key;
	}

	// B4: toc에서 실제 존재하는 topic Set 구축
	let availableTopics = $derived.by(() => {
		if (!toc?.chapters) return null;
		const set = new Set();
		for (const ch of toc.chapters) {
			for (const t of ch.topics) set.add(t.topic);
		}
		return set;
	});

	let dangerAnomalies = $derived((data?.anomalies ?? []).filter(a => a.severity === "danger"));
	let warningAnomalies = $derived((data?.anomalies ?? []).filter(a => a.severity === "warning"));
	let areaKeys = $derived(data?.areas ? Object.keys(AREA_META).filter(k => data.areas[k]) : []);

	// 레이더 차트 스펙
	let radarSpec = $derived.by(() => {
		if (!data?.areas || areaKeys.length < 3) return null;
		const grades = {};
		for (const k of areaKeys) grades[k] = { grade: data.areas[k].grade };
		return insightToRadarSpec(grades, corpName);
	});
</script>

{#if loading}
	<!-- 로딩은 조용하게 — 빈 공간 차지 안 함 -->
{:else if data}
	<div class="space-y-2">
		<!-- Anomaly banners -->
		{#if dangerAnomalies.length > 0}
			<div class="flex items-start gap-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20">
				<AlertCircle size={14} class="text-red-400 mt-0.5 flex-shrink-0" />
				<div class="text-[11px] text-red-400/90 space-y-0.5">
					{#each dangerAnomalies as a}
						<div>{a.text}</div>
					{/each}
				</div>
			</div>
		{/if}
		{#if warningAnomalies.length > 0}
			<div class="flex items-start gap-2 px-3 py-2 rounded-lg bg-amber-500/8 border border-amber-500/20">
				<AlertTriangle size={14} class="text-amber-400 mt-0.5 flex-shrink-0" />
				<div class="text-[11px] text-amber-400/80 space-y-0.5">
					{#each warningAnomalies as a}
						<div>{a.text}</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Grade cards grid -->
		<div class="grid grid-cols-4 sm:grid-cols-7 gap-1.5">
			{#each areaKeys as key}
				{@const meta = AREA_META[key]}
				{@const area = data.areas[key]}
				{@const Icon = meta.icon}
				<button
					class="flex flex-col items-center gap-1 px-2 py-2 rounded-lg border transition-colors cursor-pointer {gradeColor(area.grade)} {expandedArea === key ? 'ring-1 ring-dl-accent/40' : 'hover:brightness-110'}"
					onclick={() => toggleArea(key)}
				>
					<Icon size={13} class="opacity-70" />
					<span class="text-[10px] opacity-80">{meta.label}</span>
					<span class="text-[14px] font-bold">{area.grade}</span>
				</button>
			{/each}
		</div>

		<!-- Radar chart -->
		{#if radarSpec}
			{#await import("$lib/chart/ChartRenderer.svelte") then { default: ChartRenderer }}
				<ChartRenderer spec={radarSpec} class="max-w-xs mx-auto" />
			{/await}
		{/if}

		<!-- Expanded detail -->
		{#if expandedArea && data.areas[expandedArea]}
			{@const area = data.areas[expandedArea]}
			{@const meta = AREA_META[expandedArea]}
			{@const relatedTopics = (RELATED_TOPICS[expandedArea] || []).filter(t => !availableTopics || availableTopics.has(t))}
			<div class="px-3 py-2 rounded-lg bg-dl-surface-card border border-dl-border/20 space-y-2 animate-fadeIn">
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-2">
						<span class="px-1.5 py-0.5 rounded text-[10px] font-bold {gradeBadgeColor(area.grade)}">{area.grade}</span>
						<span class="text-[12px] font-medium text-dl-text">{meta.label}</span>
						<span class="text-[11px] text-dl-text-muted">— {area.summary}</span>
					</div>
					<button class="p-0.5 text-dl-text-dim hover:text-dl-text" onclick={() => { expandedArea = null; }}>
						<ChevronUp size={14} />
					</button>
				</div>

				{#if area.details?.length > 0}
					<div class="text-[11px] text-dl-text-muted space-y-0.5">
						{#each area.details as d}
							<div class="flex items-start gap-1.5">
								<span class="w-1 h-1 rounded-full bg-dl-text-dim/40 mt-1.5 flex-shrink-0"></span>
								<span>{d}</span>
							</div>
						{/each}
					</div>
				{/if}

				{#if area.risks?.length > 0}
					<div class="text-[11px] space-y-0.5">
						{#each area.risks as r}
							<div class="flex items-start gap-1.5 {riskColor(r.level)}">
								<AlertTriangle size={10} class="mt-0.5 flex-shrink-0" />
								<span>{r.text}</span>
							</div>
						{/each}
					</div>
				{/if}

				{#if area.opportunities?.length > 0}
					<div class="text-[11px] space-y-0.5">
						{#each area.opportunities as o}
							<div class="flex items-start gap-1.5 {oppColor(o.level)}">
								<TrendingUp size={10} class="mt-0.5 flex-shrink-0" />
								<span>{o.text}</span>
							</div>
						{/each}
					</div>
				{/if}

				<!-- P8: Related topics -->
				{#if onNavigateTopic && relatedTopics.length > 0}
					<div class="flex flex-wrap gap-1 pt-1 border-t border-dl-border/10">
						<span class="text-[10px] text-dl-text-dim mr-1">원문 보기:</span>
						{#each relatedTopics as t}
							<button
								class="text-[10px] px-1.5 py-0.5 rounded bg-dl-accent/8 text-dl-accent-light border border-dl-accent/20 hover:bg-dl-accent/15 transition-colors"
								onclick={() => onNavigateTopic(t)}
							>
								{t}
							</button>
						{/each}
					</div>
				{/if}
			</div>
		{/if}

		<!-- Profile summary -->
		{#if data.profile}
			<div class="text-[10px] text-dl-text-dim px-1">
				{data.profile}
			</div>
		{/if}
	</div>
{/if}
