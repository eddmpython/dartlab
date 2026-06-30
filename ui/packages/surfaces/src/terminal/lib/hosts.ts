// 뷰어 컴포넌트 주입 계약 · terminal → viewer 역의존 제거 (4a-3 주입 역전).
// 셸이 lazy 로더를 주입한다: landing = `$lib/components/viewer/*` 동적 import(청크 분리 유지),
// ui/web = null. null = "이 셸은 임베드 미지원" 명시 선언 · 패널이 직접 열화 안내를 렌더하므로
// silent fallback 이 아니다 (열화 티어 UX: 숨김 금지 + 안내, 03 §1).
import type { Component } from 'svelte';

export interface ViewerStudioHostProps {
	code: string;
	vs: string[];
	embedded: boolean;
	basePath?: string; // 셸 base 경로(에셋 · 임베드 뷰어 아바타) · ViewerOverlay 가 runtime.env.basePath 주입.
	repoUrl?: string; // 이슈 링크 repo URL · 셸 brand(links.repo)에서 ViewerOverlay 가 주입(임베드 경로도 관통).
	tier?: 'public' | 'local'; // export tier 라벨(03 §7) · ViewerOverlay 가 runtime.env.kind 로 주입.
	onNavigate: (code: string, vs: string[]) => void;
	onclose: () => void;
}

export interface FinanceDialogHostProps {
	code: string;
	corpName: string;
	open: boolean;
	onclose: () => void;
}

export interface TerminalHosts {
	/** 공시뷰어 본체(ViewerStudio) lazy 로더 · null 이면 ViewerOverlay 는 URL(iframe) 경로만 지원. */
	viewerStudio: (() => Promise<{ default: Component<ViewerStudioHostProps> }>) | null;
	/** 정량 재무제표 모달(FinanceDialog) lazy 로더 · null 이면 열화 안내 모달. */
	financeDialog: (() => Promise<{ default: Component<FinanceDialogHostProps> }>) | null;
}

/** 후원·기여 센터에 표시할 사람. kind = 뱃지(♦영감/♥후원/♣기여). image 없으면 모노그램.
 * 영감·후원 = 큐레이션(SSOT), 기여 = GitHub contributors 자동(런타임). */
export interface SupportPerson {
	handle: string;
	url: string;
	image?: string;
	kind: 'insp' | 'support' | 'contrib';
	postUrl?: string; // 영감 인물의 "스레드 보기" 링크
}

/** 후원해주신 분(BMC 등) · 동의분만. */
export interface SupportDonor {
	name: string;
	url?: string;
}

/** 셸 식별 외부 링크 · 헤더 SNS·이슈·후원 칩. 셸(landing·ui/web·local)이 주입한다.
 * surface 가 brand 정체성을 소유하지 않게 하는 주입 계약(역의존 제거, 단계-4b). 값은 공개 URL.
 * 정본 = `brandLinks.ts` 의 DARTLAB_BRAND_LINKS · 셸들이 그 상수를 공통 주입(SSOT). */
export interface TerminalBrandLinks {
	repo: string;
	coffee: string;
	youtube: string;
	threads: string;
	instagram: string;
	/** GitHub Sponsors 후원 URL · 미설정이면 후원 박스에서 해당 줄 숨김. */
	sponsors?: string;
	/** 계좌 후원 · 미설정이면 후원 박스에서 해당 줄 숨김. 값은 공개 후원 계좌. */
	account?: { bank: string; number: string; holder: string };
	/** 영감·후원 큐레이션 인물 · 미설정이면 빈 목록. 기여(♣)는 런타임 GitHub 자동이라 여기 없음. */
	people?: SupportPerson[];
	/** 후원해주신 분 · 미설정/빈 목록이면 섹션 숨김. */
	donors?: SupportDonor[];
}
