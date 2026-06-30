// scan surface 의 viz 전용 얇은 진입점 · 무거운 ./scan 배럴(DuckDB·codemirror)을 끌지 않고
// 순수 SVG primitive 만 노출한다. 외부 소비(landing /lab/compare)가 ./scan/runtime 와 동일한
// 얇은 sub-export 패턴으로 import 한다. scan 내부 소비(Grid·CellTooltip)는 상대경로 그대로.
export { default as Sparkline } from './Sparkline.svelte';
