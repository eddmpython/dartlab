/**
 * 블로그급 마크다운 렌더러. 노트북 마크다운셀과 블로그가 같은 시각을 갖게 한다.
 *
 * 두 가지를 한다.
 *   1. 안전. 마크다운셀 내용은 사용자 입력(untrusted)이고, 공유 노트북(.ipynb) 임포트로 남의
 *      악성 마크다운이 들어올 수 있다. marked 로 HTML 을 만든 뒤 DOMPurify 로 반드시 정화한다.
 *      정적 호스트라 CSP 헤더가 없으므로 이 정화가 유일한 신뢰경계다.
 *   2. 리치. 유튜브(@[youtube](id|url))·영상(@[video](url))·반응형 이미지 임베드를 붙인다.
 *      유튜브는 youtube-nocookie + sandbox 로만 허용한다.
 *
 * 렌더는 저장이 아니라 렌더 시점에 매번 정화한다. 오염된 저장 출력도 재렌더마다 재정화된다.
 */
import { Marked } from 'marked';
import DOMPurify from 'dompurify';

const YT_ID = /^[\w-]{11}$/;
const YT_URL = /(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([\w-]{11})/;

function youtubeId(input: string): string | null {
	const s = String(input || '').trim();
	if (YT_ID.test(s)) return s;
	const m = s.match(YT_URL);
	return m ? m[1] : null;
}

/** @[youtube](id|url) 와 @[video](url) 임베드. */
const embedExtension = {
	extensions: [
		{
			name: 'embed',
			level: 'inline' as const,
			start(src: string) {
				return src.indexOf('@[');
			},
			tokenizer(src: string) {
				const m = /^@\[(youtube|video)\]\(([^)]+)\)/.exec(src);
				if (!m) return undefined;
				return { type: 'embed', raw: m[0], kind: m[1], target: m[2].trim() };
			},
			renderer(token: { kind: string; target: string }) {
				if (token.kind === 'youtube') {
					const id = youtubeId(token.target);
					if (!id) return `<p class="rm-embed-err">유효하지 않은 유튜브: ${token.target}</p>`;
					return (
						`<div class="rm-embed rm-youtube"><iframe ` +
						`src="https://www.youtube-nocookie.com/embed/${id}" ` +
						`title="YouTube" loading="lazy" allowfullscreen ` +
						`referrerpolicy="no-referrer" ` +
						`sandbox="allow-scripts allow-same-origin allow-popups" ` +
						`allow="encrypted-media; fullscreen; picture-in-picture"></iframe></div>`
					);
				}
				return `<div class="rm-embed rm-video"><video controls preload="metadata" src="${encodeURI(token.target)}"></video></div>`;
			},
		},
	],
};

// marked 18 의 renderer 는 토큰 객체를 받는다(옛 위치인자 아님).
type ImageToken = { href: string; title: string | null; text: string };
type LinkToken = { href: string; title: string | null; text: string; tokens?: unknown[] };

/** 이미지는 반응형 + lazy (figure 로 감싸 캡션 여지). */
const imageRenderer = {
	renderer: {
		image({ href, title, text }: ImageToken) {
			const t = title ? ` title="${title}"` : '';
			const cap = text ? `<figcaption>${text}</figcaption>` : '';
			return `<figure class="rm-figure"><img class="rm-img" loading="lazy" src="${href}" alt="${text || ''}"${t} />${cap}</figure>`;
		},
		link(this: { parser: { parseInline: (t: unknown[]) => string } }, token: LinkToken) {
			const { href, title, text, tokens } = token;
			const inner = tokens && tokens.length ? this.parser.parseInline(tokens) : text;
			const t = title ? ` title="${title}"` : '';
			const rel = /^https?:\/\//.test(href) ? ' target="_blank" rel="noopener noreferrer nofollow"' : '';
			return `<a href="${href}"${t}${rel}>${inner}</a>`;
		},
	},
};

const marked = new Marked({ gfm: true, breaks: false });
marked.use(embedExtension);
marked.use(imageRenderer);

let hookInstalled = false;
function installHook() {
	if (hookInstalled) return;
	hookInstalled = true;
	DOMPurify.addHook('uponSanitizeElement', (node, data) => {
		const el = node as Element;
		if (data.tagName === 'iframe') {
			const src = el.getAttribute('src') || '';
			// youtube.com / youtu.be 는 nocookie 로 재작성, /embed/ 형태만 생존.
			const ok = /^https:\/\/www\.youtube-nocookie\.com\/embed\/[\w-]{11}/.test(src);
			if (!ok) {
				el.parentNode?.removeChild(el);
				return;
			}
			el.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-popups');
			el.setAttribute('referrerpolicy', 'no-referrer');
		}
		if (data.tagName === 'a') {
			const href = el.getAttribute('href') || '';
			if (/^https?:\/\//.test(href)) {
				el.setAttribute('target', '_blank');
				el.setAttribute('rel', 'noopener noreferrer nofollow');
			}
		}
	});
}

function sanitize(html: string): string {
	installHook();
	return DOMPurify.sanitize(html, {
		ADD_TAGS: ['iframe', 'video', 'source', 'figure', 'figcaption'],
		ADD_ATTR: ['allow', 'allowfullscreen', 'sandbox', 'referrerpolicy', 'loading', 'controls', 'preload', 'target'],
		ALLOW_UNKNOWN_PROTOCOLS: false,
		SANITIZE_NAMED_PROPS: true,
		FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover'],
	}) as unknown as string;
}

/** 마크다운 문자열을 안전한 리치 HTML 로. SSR(window 없음)에서는 정화 불가라 텍스트 이스케이프만. */
export function renderRichMarkdown(md: string): string {
	const raw = (marked.parse(md || '') as string) || '';
	if (typeof window === 'undefined' || !DOMPurify.isSupported) {
		return md ? (md.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[c] as string)) : '';
	}
	return sanitize(raw);
}
