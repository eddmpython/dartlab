// landing 셸이 TerminalSurface 에 주입하는 부품 · /terminal · /lab/terminal-dev 공용.
// hosts = 뷰어 컴포넌트 lazy 로더(동적 import 리터럴은 셸 소유 → 청크 분리 유지, terminal→viewer 역의존 제거).
// links = dartlab 공통 브랜드·후원 SSOT(DARTLAB_BRAND_LINKS) 그대로 주입 · local 셸과 동일 정본.
import { DARTLAB_BRAND_LINKS, type TerminalHosts } from '@dartlab/ui-surfaces/terminal';

export const terminalHosts: TerminalHosts = {
	viewerStudio: () => import('@dartlab/ui-surfaces/viewer').then((m) => ({ default: m.ViewerStudio })),
	financeDialog: () => import('@dartlab/ui-surfaces/viewer').then((m) => ({ default: m.FinanceDialog }))
};

// SNS·후원 링크 = dartlab SSOT 공통 주입(landing·local 동일). 변경은 brandLinks.ts 한 곳.
export const terminalLinks = DARTLAB_BRAND_LINKS;
