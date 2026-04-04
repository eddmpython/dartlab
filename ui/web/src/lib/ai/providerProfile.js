export function normalizeProvider(name) {
	if (!name) return name;
	return name;
}

export function applyProfileSnapshot(currentProviders = {}, profile = null) {
	if (!profile) return currentProviders;
	const merged = { ...currentProviders };
	for (const spec of profile.catalog || []) {
		const name = normalizeProvider(spec.id);
		const settings = profile.providers?.[name] || {};
		merged[name] = {
			...(merged[name] || {}),
			label: spec.label || name,
			desc: spec.description || "",
			auth: spec.authKind || "none",
			supportedRoles: Array.isArray(spec.supportedRoles) ? spec.supportedRoles : [],
			model: settings.model ?? merged[name]?.model ?? null,
			secretConfigured: !!settings.secretConfigured,
			selected: profile.defaultProvider === name,
		};
		if (spec.envKey) merged[name].envKey = spec.envKey;
	}
	return merged;
}

export function mergeProviderStatus(currentProviders = {}, nextProviders = {}) {
	const merged = { ...currentProviders };
	for (const [name, next] of Object.entries(nextProviders)) {
		const prev = merged[name] || {};
		if (next?.checked === false && prev?.checked) {
			merged[name] = {
				...prev,
				...next,
				checked: prev.checked,
				available: prev.available,
				model: prev.model,
			};
			continue;
		}
		merged[name] = { ...prev, ...next };
	}
	return merged;
}

export function mergeProviderDetail(currentDetail = {}, nextDetail = {}, { preserveChecked = false } = {}) {
	if (preserveChecked && nextDetail?.checked === false && currentDetail?.checked) {
		return currentDetail;
	}
	return { ...currentDetail, ...nextDetail };
}
