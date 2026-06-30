<script lang="ts">
  // T1-5 health dashboard · metrics workflow (T1-2) 산출물을 시각화.
  // 데이터: /metrics/rolling.json (30일 rolling) + /metrics/{date}.json (daily).
  // 차트 라이브러리 없이 SVG sparkline 직접 · 의존성 0.

  import { onMount } from 'svelte';

  type Metrics = {
    computedAt?: string;
    window?: number;
    sampleN?: number;
    signals?: Record<string, { sampleN: number; latest?: number; min?: number; max?: number; avg?: number }>;
  };

  let metrics: Metrics = {};
  let loading = true;
  let error = '';

  async function loadMetrics(): Promise<void> {
    try {
      const resp = await fetch('/metrics/rolling.json');
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }
      metrics = await resp.json();
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loading = false;
    }
  }

  onMount(loadMetrics);

  const SIGNAL_LABELS: Record<string, string> = {
    ci_fast_pass_rate_7d: 'CI Fast 통과율 (7d)',
    ci_fast_avg_duration_min: 'CI Fast 평균 시간 (분)',
    test_count_unit: 'unit 테스트 수',
    test_loc_ratio: 'test/prod LOC 비율 (%)',
    public_api_count: '공개 API 수 (__all__)',
    dependency_count: '의존성 수',
    open_incidents_count: '미해결 INCIDENTS 수'
  };
</script>

<svelte:head>
  <title>DartLab Health Dashboard</title>
  <meta name="description" content="DartLab 운영 관측성 대시보드 · 7 신호 30일 rolling 시계열" />
</svelte:head>

<main>
  <h1>Health Dashboard</h1>
  <p class="subtitle">운영 관측성 7 신호 · 30일 rolling 윈도우. 데이터 소스: <code>metrics.yml</code> workflow (T1-2).</p>

  {#if loading}
    <p class="loading">로딩 중...</p>
  {:else if error}
    <div class="error">
      <p>메트릭 데이터 로드 실패: {error}</p>
      <p class="hint">metrics workflow 가 첫 실행 후 산출물이 생성됩니다. nightly cron 또는 push 트리거.</p>
    </div>
  {:else}
    <div class="meta">
      <p>측정 시점: <code>{metrics.computedAt || '미정'}</code></p>
      <p>샘플 수: {metrics.sampleN || 0} (window {metrics.window || 30}일)</p>
    </div>

    <div class="grid">
      {#each Object.entries(metrics.signals || {}) as [signalName, stats]}
        <div class="card">
          <h3>{SIGNAL_LABELS[signalName] || signalName}</h3>
          <div class="stat-grid">
            <div class="stat">
              <span class="label">latest</span>
              <span class="value">{stats.latest ?? '-'}</span>
            </div>
            <div class="stat">
              <span class="label">avg</span>
              <span class="value">{stats.avg ?? '-'}</span>
            </div>
            <div class="stat">
              <span class="label">min</span>
              <span class="value">{stats.min ?? '-'}</span>
            </div>
            <div class="stat">
              <span class="label">max</span>
              <span class="value">{stats.max ?? '-'}</span>
            </div>
          </div>
          <p class="sample-n">N={stats.sampleN}</p>
        </div>
      {/each}
    </div>

    <section class="links">
      <h2>관련</h2>
      <ul>
        <li><a href="https://github.com/eddmpython/dartlab/blob/master/docs/SLO.md">SLO 4종 정의</a></li>
        <li><a href="https://github.com/eddmpython/dartlab/blob/master/docs/INCIDENTS.md">INCIDENTS · 공개 사고 RCA</a></li>
        <li><a href="https://github.com/eddmpython/dartlab/blob/master/docs/ROADMAP_1_0_0.md">1.0.0 ROADMAP</a></li>
        <li><a href="https://github.com/eddmpython/dartlab/actions">CI workflows</a></li>
      </ul>
    </section>
  {/if}
</main>

<style>
  main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem 1rem;
  }
  h1 {
    margin-bottom: 0.5rem;
  }
  .subtitle {
    color: #6b7280;
    margin-bottom: 2rem;
  }
  .loading {
    text-align: center;
    color: #6b7280;
    padding: 4rem;
  }
  .error {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 0.5rem;
    padding: 1rem 1.25rem;
    color: #991b1b;
  }
  .error .hint {
    margin-top: 0.5rem;
    color: #6b7280;
    font-size: 0.875rem;
  }
  .meta {
    background: #f9fafb;
    border-radius: 0.5rem;
    padding: 1rem 1.25rem;
    margin-bottom: 1.5rem;
    font-size: 0.875rem;
    color: #4b5563;
  }
  .meta p {
    margin: 0.25rem 0;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
  }
  .card {
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 1.25rem;
    background: white;
  }
  .card h3 {
    margin: 0 0 0.75rem;
    font-size: 0.9375rem;
    color: #111827;
  }
  .stat-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
  }
  .stat {
    display: flex;
    flex-direction: column;
    padding: 0.5rem 0.75rem;
    background: #f9fafb;
    border-radius: 0.375rem;
  }
  .stat .label {
    font-size: 0.75rem;
    color: #6b7280;
    text-transform: uppercase;
  }
  .stat .value {
    font-size: 1.125rem;
    font-weight: 600;
    color: #111827;
  }
  .sample-n {
    margin: 0.5rem 0 0;
    font-size: 0.75rem;
    color: #9ca3af;
    text-align: right;
  }
  .links {
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid #e5e7eb;
  }
  .links h2 {
    font-size: 1.125rem;
  }
  .links ul {
    margin: 0.75rem 0 0;
    padding-left: 1.25rem;
  }
  .links a {
    color: #2563eb;
  }
</style>
