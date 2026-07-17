import type { Handle } from '@sveltejs/kit';

const SERIALIZED_PUBLIC_SOURCE_HEADERS = new Set([
	'content-length',
	'etag',
	'x-repo-commit'
]);

export const handle: Handle = async ({ event, resolve }) => {
	return resolve(event, {
		filterSerializedResponseHeaders: (name) => SERIALIZED_PUBLIC_SOURCE_HEADERS.has(name.toLowerCase())
	});
};
