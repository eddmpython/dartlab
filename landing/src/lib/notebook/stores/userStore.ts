import { writable, get } from 'svelte/store';

export interface NotebookUser {
	email: string;
	name: string;
	picture: string;
}

export const currentUser = writable<NotebookUser | null>(null);
export const authChecked = writable<boolean>(false);

export async function checkAuth(): Promise<void> {
	try {
		const res = await fetch('/api/user', { credentials: 'include' });
		if (!res.ok) {
			currentUser.set(null);
			return;
		}
		const data = await res.json();
		if (data.authenticated && data.user) {
			currentUser.set({
				email: data.user.email,
				name: data.user.name,
				picture: data.user.picture,
			});
		} else {
			currentUser.set(null);
		}
	} catch {
		currentUser.set(null);
	} finally {
		authChecked.set(true);
	}
}

export function isLoggedIn(): boolean {
	return get(currentUser) !== null;
}
