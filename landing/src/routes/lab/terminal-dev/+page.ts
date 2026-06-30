// /lab/terminal-dev · 터미널 격리 개발 라우트 (본진 /terminal 과 로더 SSOT 공유, UI 는 dev 셸).
import type { PageLoad } from './$types';
import { loadTerminalRaw } from '$lib/terminal-shell/routeLoad';

export const ssr = false;
export const prerender = true;

export const load: PageLoad = ({ fetch }) => loadTerminalRaw(fetch);
