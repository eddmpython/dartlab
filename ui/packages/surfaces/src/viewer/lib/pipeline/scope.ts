// scope 파생 (Python scopeExpr) · readWide 파이프라인 1단계.

// xbrlClass 에 "_S" → standalone, else consolidated(null 포함).
export function scopeOf(xbrlClass: string | null): string {
	return xbrlClass != null && xbrlClass.includes('_S') ? 'standalone' : 'consolidated';
}
