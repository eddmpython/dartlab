export const brand = {
	name: 'DartLab',
	tagline: '공시의 숫자 너머를 읽다',
	taglineEn: 'Read Beyond the Numbers',
	description: 'DART 공시 문서를 완벽하게 분석하는 Python 라이브러리',
	version: '0.1.0',
	url: 'https://eddmpython.github.io/dartlab/',
	repo: 'https://github.com/eddmpython/dartlab',
	pypi: 'https://pypi.org/project/dartlab/',
	coffee: 'https://buymeacoffee.com/eddmpython',
	author: 'eddmpython',

	color: {
		primary: '#f59e0b',
		primaryDark: '#d97706',
		primaryLight: '#fbbf24',
		accent: '#3b82f6',
		accentLight: '#60a5fa',
		bgDark: '#0c0a09',
		bgDarker: '#050403',
		bgCard: '#1c1917',
		bgCardHover: '#292524',
		text: '#fafaf9',
		textMuted: '#a8a29e',
		textDim: '#78716c',
		border: '#292524',
		success: '#10b981',
		warning: '#ef4444',
		coffee: '#ffdd00'
	}
} as const;

export type Brand = typeof brand;
