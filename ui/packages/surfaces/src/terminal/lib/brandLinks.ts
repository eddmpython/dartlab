// dartlab 공개 브랜드·후원 SSOT · 헤더 우측 SNS + 후원·기여 다이얼로그의 단일 정본.
// landing(GitHub Pages) · ui/apps/local 셸이 *이 상수 하나*를 TerminalSurface `links` 로 공통 주입한다.
// (컴포넌트는 여전히 prop 으로만 받아 brand-무지 = 단계-4b 유지. 본 상수는 셸들의 중복 제거용 공통 정의.)
// 변경은 여기 한 곳 → 모든 셸 반영. 영감/후원 인물은 큐레이션(가짜 금지), 기여(♣)는 런타임 GitHub 자동.
import type { TerminalBrandLinks } from './hosts';

export const DARTLAB_BRAND_LINKS: TerminalBrandLinks = {
	repo: 'https://github.com/eddmpython/dartlab',
	coffee: 'https://buymeacoffee.com/eddmpython',
	youtube: 'https://www.youtube.com/@eddmpython',
	threads: 'https://www.threads.net/@dartlab.ai',
	instagram: 'https://www.instagram.com/dartlab.ai/',
	sponsors: 'https://github.com/sponsors/eddmpython',
	account: { bank: '토스뱅크', number: '1002-0421-4626', holder: '김주현' },
	people: [
		{ handle: '@youngchangjo', url: 'https://www.threads.com/@youngchangjo', kind: 'insp', postUrl: 'https://www.threads.com/@youngchangjo/post/DZC_jobCfO6' },
		{ handle: '@wannabewrit', url: 'https://www.threads.com/@wannabewrit', kind: 'support' },
		{ handle: '@ryusw007', url: 'https://www.threads.com/@ryusw007', kind: 'support' }
	],
	donors: [] // 운영자: 동의받은 Buy Me a Coffee 후원자 · { name: '닉네임', url?: '...' }
};
