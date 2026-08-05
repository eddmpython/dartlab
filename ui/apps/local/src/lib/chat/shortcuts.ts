// 단축키 한 곳. 표시 라벨과 실제 바인딩이 같은 자리에서 나온다.
//
// 왜 표로 두나. 라벨을 손으로 적으면 실제 동작과 어긋나고, 어긋난 안내는 없느니만 못하다.
// 여기서 정의한 것으로 판정도 하고 도움말도 그린다.

export type ShortcutAction = 'newChat' | 'focusComposer' | 'toggleSidebar' | 'focusSearch' | 'showHelp';

export interface ShortcutSpec {
	action: ShortcutAction;
	/** 조합의 주 키. 소문자 비교한다. */
	key: string;
	/** mac 은 Command, 그 외는 Control. 두 이름을 따로 두지 않는다. */
	mod: boolean;
	shift?: boolean;
	label: string;
}

export const SHORTCUTS: readonly ShortcutSpec[] = [
	{ action: 'newChat', key: 'j', mod: true, label: '새 대화' },
	{ action: 'focusComposer', key: 'l', mod: true, label: '입력칸으로' },
	{ action: 'focusSearch', key: 'k', mod: true, label: '대화 검색' },
	{ action: 'toggleSidebar', key: 'b', mod: true, label: '사이드바 접기' },
	{ action: 'showHelp', key: '/', mod: true, label: '단축키 보기' }
];

/** 이 플랫폼에서 mod 키를 무엇이라 부르는가. 라벨과 판정이 같은 곳에서 나와야 한다. */
export function modLabel(platform: string = typeof navigator === 'undefined' ? '' : navigator.platform): string {
	return /mac|iphone|ipad/i.test(platform) ? 'Cmd' : 'Ctrl';
}

/** 사람이 읽는 조합 표기. */
export function shortcutLabel(spec: ShortcutSpec, platform?: string): string {
	const parts = [modLabel(platform)];
	if (spec.shift) parts.push('Shift');
	parts.push(spec.key === '/' ? '/' : spec.key.toUpperCase());
	return parts.join('+');
}

export interface KeyLike {
	key: string;
	ctrlKey: boolean;
	metaKey: boolean;
	shiftKey: boolean;
	altKey: boolean;
}

/**
 * 이 키 입력이 어떤 동작인가. 해당 없으면 null 이다.
 *
 * mac 은 Command, 그 외는 Control 로 본다. Alt 가 눌린 조합은 우리 것이 아니다.
 */
export function actionForEvent(event: KeyLike, platform?: string): ShortcutAction | null {
	if (event.altKey) return null;
	const isMac = /mac|iphone|ipad/i.test(
		platform ?? (typeof navigator === 'undefined' ? '' : navigator.platform)
	);
	const mod = isMac ? event.metaKey : event.ctrlKey;
	const key = event.key.toLowerCase();
	for (const spec of SHORTCUTS) {
		if (spec.mod !== mod) continue;
		if (Boolean(spec.shift) !== event.shiftKey) continue;
		if (spec.key !== key) continue;
		return spec.action;
	}
	return null;
}

/** 입력 중인 곳에서 눌렀는가. 글자를 치는 중에 단축키가 가로채면 안 된다. */
export function isTypingTarget(target: EventTarget | null): boolean {
	if (!(target instanceof HTMLElement)) return false;
	if (target.isContentEditable) return true;
	const tag = target.tagName.toLowerCase();
	return tag === 'input' || tag === 'textarea' || tag === 'select';
}
