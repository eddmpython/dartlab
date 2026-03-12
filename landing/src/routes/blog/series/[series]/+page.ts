import { error } from '@sveltejs/kit';
import { getSeries, getSeriesPosts, seriesDefinitions, type CategoryId } from '$lib/blog/posts';

export const prerender = true;

// SvelteKit prerender entries need static values, so resolve from source map here.
const seriesIds = Object.keys(seriesDefinitions);

export function entries() {
	return seriesIds.map((series) => ({ series }));
}

export function load({ params }) {
	const series = getSeries(params.series);
	if (!series) {
		throw error(404, 'Series not found');
	}

	const posts = getSeriesPosts(series.id);
	const categories = [...new Set(posts.map((post) => post.category))];
	const currentCategory = categories.length === 1 ? (categories[0] as CategoryId) : null;

	return {
		series: series.id,
		currentCategory
	};
}
