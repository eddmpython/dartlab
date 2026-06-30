// 라이브 카드 캐러셀 디자인 토큰 · 기존 SNS 캐러셀 파이프라인(sns/remotion-sns/src/lib/colors.ts)의
// 색감을 그대로 가져온다(새로 짓지 않음·SSOT 동기화). 규격 = 인스타 4:5(1080×1350). 폰트 = Pretendard
// Variable(landing 전역 --font-sans 이미 배선). 브랜드 마크 = 공통 아바타(landing/static/avatar.webp).

/** 캐러셀 팔레트 · 원본 렌더러(renderEditorialCarouselPng.py ACCENT=#ff3f6f)·계약 accentColor=#fb3f6c
 *  기준. 단일 강조 = 로즈(엠버 아님). colors.ts 의 orange accent 는 Remotion 내부용이라 카드엔 미사용. */
export const CARD = {
	primary: '#ff3f6f', // 헤드라인 한 구절 강조(rose, stop-the-scroll)
	primaryDark: '#c83232',
	accent: '#ff3f6f', // 키커 점·라벨 = 로즈(원본 카드엔 엠버/주황 없음)
	accentImpact: '#fb3f6c',
	text: '#f6f8fb', // 원본 WHITE
	textMuted: '#d8e2f0', // 원본 MUTED
	textDim: '#9aa3ad', // 원본 SOFT
	bgDark: '#050811',
	bgDarker: '#030509',
	bgCard: '#0f1219',
	border: '#1e2433'
} as const;

/** 차트 시리즈 색 · 첫 시리즈(강조) = 테마색(var(--dl-accent)·SVG stroke/fill 에서 해석), 나머지는 중립(라이트·슬레이트).
 *  하드코딩 로즈 제거 → 테마 따라감. 다행 표(최대 6 시리즈) 색충돌 방지 7색. */
export const CARD_SERIES = ['var(--dl-accent)', '#f6f8fb', 'var(--dl-accent-light)', '#9aa7c0', '#d8e2f0', '#c77d92', '#7f8aa3'] as const;

/** 인스타 캐러셀 규격(1080×1350 = 4:5). 카드는 이 비율로 반응형. */
export const CARD_ASPECT = '1080 / 1350';

/** 캐러셀 카피 톤 · 줄 끝 마침표 제거(단정한 구절·문장부호 최소). 소수점(29.5)·천단위는 줄 중간이라
 *  보존, 쉼표는 유지. SNS 카드는 문장이 아니라 한 호흡 구절이라 종지부를 찍지 않는다. */
export function stripDots(text: string): string {
	return String(text ?? '')
		.split('\n')
		.map((ln) => ln.replace(/[.。]+\s*$/u, '').trimEnd())
		.join('\n');
}

/** AccentText · `[[구절]]` 을 강조색으로 쪼갠 토막 목록. 기존 AccentText.tsx 와 동일 규약(순수·테스트 가능). */
export function accentParts(text: string): { text: string; accent: boolean }[] {
	return String(text ?? '')
		.split(/(\[\[[^\]]+\]\])/g)
		.filter((p) => p !== '')
		.map((p) => {
			const m = p.match(/^\[\[([^\]]+)\]\]$/);
			return m ? { text: m[1], accent: true } : { text: p, accent: false };
		});
}
