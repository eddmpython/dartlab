// 첫 화면 글 목록의 다음 쪽. 빌드할 때 쪽마다 정적 JSON 하나로 굽는다(1쪽은 첫 화면 HTML 에 이미 있다).
import { error, json } from '@sveltejs/kit';
import { getFeedPage, getFeedPageCount } from '$lib/blog/posts';
import type { EntryGenerator, RequestHandler } from './$types';

export const prerender = true;

export const entries: EntryGenerator = () => {
	const pages = getFeedPageCount();
	return Array.from({ length: pages }, (_, index) => ({ page: String(index + 1) }));
};

export const GET: RequestHandler = ({ params }) => {
	const page = Number(params.page);
	const pages = getFeedPageCount();
	if (!Number.isInteger(page) || page < 1 || page > pages) error(404, 'no such page');
	return json({ page, pages, items: getFeedPage(page) });
};
