export const brand = {
	name: 'DartLab',
	tagline: '종목코드 하나. 기업의 전체 이야기.',
	taglineEn: 'One stock code. Full company story.',
	description: '종목코드 하나로 DART·EDGAR 전자공시를 읽고 비교한다. Python 한 줄.',
	descriptionEn: 'One stock code → structured Korean DART & US SEC EDGAR filings, one line of Python.',
	version: __DARTLAB_VERSION__,
	url: 'https://eddmpython.github.io/dartlab/',
	repo: 'https://github.com/eddmpython/dartlab',
	pypi: 'https://pypi.org/project/dartlab/',
	coffee: 'https://buymeacoffee.com/eddmpython',
	desktop: 'https://github.com/eddmpython/dartlab-desktop/releases/latest/download/DartLab.exe',
	colab: 'https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/01_company.ipynb',
	molab: 'https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/01_company.py',
	youtube: 'https://www.youtube.com/@eddmpython',
	instagram: 'https://www.instagram.com/dartlab.ai/',
	threads: 'https://www.threads.net/@dartlab.ai',
	author: 'eddmpython',

	hfRepo: 'eddmpython/dartlab-data',

	data: {
		panel: { dir: 'dart/panel', label: 'DART 공시 panel 수평화 데이터' },
		finance: { dir: 'dart/finance', label: '재무 숫자 데이터' },
		report: { dir: 'dart/report', label: '정기보고서 데이터' },
		scan: { dir: 'dart/scan', label: '전종목 횡단분석 프리빌드 데이터' },
		edgarPanel: { dir: 'edgar/panel', label: 'SEC EDGAR 공시 panel 수평화 데이터' },
		edgar: { dir: 'edgar/finance', label: 'SEC EDGAR 재무 데이터' },
		edgarFinanceStmt: { dir: 'edgar/financeStmt', label: 'SEC EDGAR 터미널 재무 (파사드 표준화)' },
	},

	// ⛔ 색은 여기서 정의하지 않는다 · 색 SSOT = ui/packages/design/src/styles/tokens.css (--p-*/--dl-*).
	// Tailwind 유틸은 landing/src/app.css 의 @theme inline 이 var(--dl-*) 로 브리지한다.
	// (옛 color:{} 블록이 syncBrand.js 로 app.css 를 생성해 오렌지 accent #fb923c 발산 원인이었음 → 폐기.)
} as const;

export type Brand = typeof brand;
