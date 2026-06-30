// terminal dev 격리 표면 · /lab/terminal-dev 전용 (본진 ./terminal 과 export 경로 분리, 단계-4b).
// 본진 번들은 이 subpath 를 import 하지 않는다 (checkDevIsolation 기계 강제, feedback_ui_rules #10).
export { default as DevTerminal } from './DevTerminal.svelte';
