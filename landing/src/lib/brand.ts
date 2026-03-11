export const brand = {
	name: 'DartLab',
	tagline: 'Read Beyond the Numbers',
	description: 'A Python library for comprehensive DART disclosure analysis',
	version: '0.4.0',
	url: 'https://eddmpython.github.io/dartlab/',
	repo: 'https://github.com/eddmpython/dartlab',
	pypi: 'https://pypi.org/project/dartlab/',
	coffee: 'https://buymeacoffee.com/eddmpython',
	desktop: 'https://github.com/eddmpython/dartlab-desktop/releases/latest/download/DartLab.exe',
	author: 'eddmpython',

	data: {
		docs: { tag: 'data-docs', dir: 'dart/docs', label: 'DART 공시 문서 데이터' },
		finance: {
			dir: 'dart/finance',
			label: '재무 숫자 데이터',
			shards: ['data-finance-1', 'data-finance-2', 'data-finance-3', 'data-finance-4'],
		},
		report: {
			dir: 'dart/report',
			label: '정기보고서 데이터',
			shards: ['data-report-1', 'data-report-2', 'data-report-3', 'data-report-4'],
		},
		edgar: { dir: 'edgar/finance', label: 'SEC EDGAR 재무 데이터' },
	},

	color: {
		primary: '#ea4647',
		primaryDark: '#c83232',
		primaryLight: '#f87171',
		accent: '#fb923c',
		accentLight: '#fdba74',
		bgDark: '#050811',
		bgDarker: '#030509',
		bgCard: '#0f1219',
		bgCardHover: '#1a1f2b',
		text: '#f1f5f9',
		textMuted: '#94a3b8',
		textDim: '#64748b',
		border: '#1e2433',
		success: '#34d399',
		warning: '#fbbf24',
		coffee: '#ffdd00'
	}
} as const;

export type Brand = typeof brand;
