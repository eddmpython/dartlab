// /terminal · DartLab Terminal 본진 라우트. 로더는 terminal-shell/routeLoad SSOT 공용 (격리 개발 라우트와 드리프트 0).
// UI 본체는 surface 패키지 @dartlab/ui-surfaces/terminal (TerminalSurface) · 단계-4b 승격.
import type { PageLoad } from './$types';
import { loadTerminalRaw } from '$lib/terminal-shell/routeLoad';

export const ssr = false;
export const prerender = true;

export const load: PageLoad = ({ fetch }) => loadTerminalRaw(fetch);
