<!--
  DartLab Embed — Snapshot 위젯.
  핵심 수치 + 7영역 등급 카드.
-->
<script>
  import { fetchCompany, fetchInsights } from "./api.js";

  let { baseUrl = "", code = "", token = "", theme = "auto" } = $props();

  let state = $state("loading"); // loading | ready | error
  let company = $state(null);
  let insights = $state(null);
  let errorMsg = $state("");

  const GRADE_LABELS = {
    profitability: "수익",
    stability: "안정",
    growth: "성장",
    dividend: "배당",
    valuation: "밸류",
    risk: "리스크",
    governance: "거버넌스",
  };

  const METRIC_DEFS = [
    { key: "marketCap", label: "시가총액", fmt: fmtKrw },
    { key: "per", label: "PER", fmt: fmtRatio },
    { key: "pbr", label: "PBR", fmt: fmtRatio },
    { key: "roe", label: "ROE", fmt: fmtPct },
    { key: "debtRatio", label: "부채비율", fmt: fmtPct },
    { key: "dividendYield", label: "배당수익률", fmt: fmtPct },
  ];

  function fmtKrw(v) {
    if (v == null) return "-";
    const t = v / 1e12;
    if (Math.abs(t) >= 1) return `${t.toFixed(1)}조`;
    const b = v / 1e8;
    return `${b.toFixed(0)}억`;
  }
  function fmtRatio(v) { return v == null ? "-" : `${v.toFixed(1)}x`; }
  function fmtPct(v) { return v == null ? "-" : `${v.toFixed(1)}%`; }

  function getProfile(ins) {
    if (!ins) return {};
    // insights 응답에서 profile/snapshot 추출
    return ins.profile || ins.snapshot || {};
  }

  function getGrades(ins) {
    if (!ins) return {};
    return ins.grades || {};
  }

  async function load() {
    try {
      state = "loading";
      const [comp, ins] = await Promise.all([
        fetchCompany(baseUrl, code, token),
        fetchInsights(baseUrl, code, token).catch(() => null),
      ]);
      company = comp;
      insights = ins;
      state = "ready";
    } catch (e) {
      errorMsg = e.message || "데이터를 불러올 수 없습니다";
      state = "error";
    }
  }

  function handleClick() {
    window.open(`${baseUrl}/?company=${code}`, "_blank");
  }

  $effect(() => {
    if (code && baseUrl) load();
  });
</script>

{#if state === "loading"}
  <div class="dl-card">
    <div class="dl-skeleton dl-skeleton-wide"></div>
    <hr class="dl-divider" />
    <div class="dl-skeleton dl-skeleton-med"></div>
    <div class="dl-skeleton dl-skeleton-short"></div>
    <div class="dl-skeleton dl-skeleton-med"></div>
    <hr class="dl-divider" />
    <div class="dl-skeleton dl-skeleton-wide"></div>
  </div>
{:else if state === "error"}
  <div class="dl-card">
    <div class="dl-error">{errorMsg}</div>
  </div>
{:else if company}
  {@const profile = getProfile(insights)}
  {@const grades = getGrades(insights)}

  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="dl-card" onclick={handleClick} title="DartLab에서 자세히 보기">
    <div class="dl-header">
      <div>
        <span class="dl-name">{company.corpName || company.name || code}</span>
        <span class="dl-code">({company.stockCode || code})</span>
      </div>
      {#if company.market}
        <span class="dl-market">{company.market}</span>
      {/if}
    </div>

    <hr class="dl-divider" />

    <div class="dl-metrics">
      {#each METRIC_DEFS as { key, label, fmt }}
        {@const val = profile[key]}
        {#if val != null}
          <div class="dl-metric">
            <span class="dl-metric-label">{label}</span>
            <span class="dl-metric-value">{fmt(val)}</span>
          </div>
        {/if}
      {/each}
    </div>

    {#if Object.keys(grades).length > 0}
      <hr class="dl-divider" />
      <div class="dl-grades">
        {#each Object.entries(grades) as [area, grade]}
          {@const label = GRADE_LABELS[area] || area}
          <div class="dl-grade">
            <span>{label}</span>
            <span class="dl-grade-pill dl-grade-{grade}">{grade}</span>
          </div>
        {/each}
      </div>
    {/if}

    <div class="dl-footer">
      <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener">
        Powered by DartLab
      </a>
    </div>
  </div>
{/if}
