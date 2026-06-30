// map surface 공개 표면 (§8.1 · 작업면 한 폴더, index.ts 하나가 공개 API).
// 산업/생태계 지도 컴포넌트 · landing 라우트(/map·/industry/[id]·/compare·/embed/company)가 마운트.
// 데이터(marketMap 번들)는 라우트가 createDartlabBrowser 로 준비해 prop 주입 · surface 는 dumb 컴포넌트.
// 결합: CompanyCard 의 basePath(블로그 링크 에셋)만 prop, $app/$lib 무결합(포터블). d3·cosmograph 는 외부 npm.
export { default as EcosystemMap } from './components/EcosystemMap.svelte';
export { default as IndustryAtlas } from './components/IndustryAtlas.svelte';
export { default as IndustryDrilldown } from './components/IndustryDrilldown.svelte';
export { default as CompanyCard } from './components/CompanyCard.svelte';
export { default as FloatingCard } from './components/FloatingCard.svelte';
export { default as TreemapView } from './components/TreemapView.svelte';
export { default as RadarChart } from './components/RadarChart.svelte';
export { default as Sparkline } from './components/Sparkline.svelte';
export { default as CompareTray } from './components/CompareTray.svelte';
export { default as MapCommandPalette } from './components/MapCommandPalette.svelte';
export { default as FreshnessBadge } from './components/FreshnessBadge.svelte';
export { default as SectorHealthCard } from './components/SectorHealthCard.svelte';
export { default as ShockSimulator } from './components/ShockSimulator.svelte';
export { default as TutorialTour } from './components/TutorialTour.svelte';
// profit-pool stage 롤업 (순수 데이터 변환 · industries/{id}.json → 격자, dual-source 표시층)
export { rollupProfitPool } from './industryPool';
export type { IndustryStageRollup, ProfitPoolStage, ProfitPoolNode } from './industryPool';
