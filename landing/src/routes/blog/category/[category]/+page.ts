import type { EntryGenerator } from './$types';
import { categoryDefinitions, getCategory } from '$lib/blog/posts';

export const prerender = true;

export const entries: EntryGenerator = () => {
	return categoryDefinitions.map((category) => ({ category: category.slug }));
};

export function load({ params }: { params: { category: string } }) {
	const category = getCategory(params.category);
	if (!category) {
		return { status: 404 };
	}
	return { category: category.slug, currentCategory: category.id };
}
