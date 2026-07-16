import type { PageLoad } from './$types';
import { createUniverseBrowser } from '$lib/browser/universeBrowser';

export const prerender = true;
export const ssr = false;

export const load: PageLoad = async ({ fetch }) => {
	return await createUniverseBrowser({ fetchFn: fetch }).seed();
};
