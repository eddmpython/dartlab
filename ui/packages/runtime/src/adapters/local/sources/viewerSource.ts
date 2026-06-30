// 로컬 viewer 포트 · external-url 모드. 터미널 overlay 가 iframe 으로 /analysis/[code]/viewer 라우트를 띄운다.
// 단계-6(viewer surface 추출) 전까지 URL-embed · 추출 시 embedded-component 승급 검토.
import type { ViewerPort } from '@dartlab/ui-contracts';

export function localViewerPort(): ViewerPort {
	return {
		mode: 'external-url',
		urlForCompany(code, options) {
			const qs = new URLSearchParams({ period: 'quarterly', terminalEmbed: '1' });
			if (options?.vs?.length) qs.set('vs', options.vs.join(','));
			return `/analysis/${encodeURIComponent(code)}/viewer?${qs.toString()}`;
		},
		async openCompany(code, options) {
			const url = this.urlForCompany(code, options);
			if (url && typeof window !== 'undefined') window.location.assign(url);
		},
		async openFiling(filing) {
			if (typeof window !== 'undefined') window.open(filing.url, '_blank', 'noopener');
		}
	};
}
