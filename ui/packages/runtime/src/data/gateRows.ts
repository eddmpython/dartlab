// 펀더게이트 행 로더 · SSR 안전 subpath(@dartlab/ui-runtime/data/gateRows). gateSource 재노출.
// terminal-strategy-lab W2: PriceChart 가 (code)=>rows 로 로드 → buildGateSeries 로 봉별 PIT 계단화.
export { loadGateRows, type FundamentalGateRow } from '../adapters/public/sources/gateSource';
