declare const __DARTLAB_VERSION__: string;
declare const __PYPROC_VERSION__: string;

// vite.config.ts blogIndexPlugin 이 빌드 시점에 만드는 블로그 목록 색인(frontmatter 일부만).
declare module 'virtual:dartlab-blog-index' {
	const entries: Array<{
		categoryFolder: string;
		order: number;
		slug: string;
		metadata: Record<string, unknown>;
		readingMinutes: number;
		previewAsset?: string;
	}>;
	export default entries;
}
