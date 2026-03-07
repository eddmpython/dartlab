<script lang="ts">
	import { cn } from '$lib/utils';
	import type { Snippet } from 'svelte';
	import type { HTMLAnchorAttributes, HTMLButtonAttributes } from 'svelte/elements';

	type Variant = 'default' | 'secondary' | 'ghost' | 'outline' | 'coffee';
	type Size = 'default' | 'sm' | 'lg' | 'icon';

	interface BaseProps {
		variant?: Variant;
		size?: Size;
		class?: string;
		children: Snippet;
	}

	type ButtonProps = BaseProps & HTMLButtonAttributes & { href?: undefined };
	type AnchorProps = BaseProps & HTMLAnchorAttributes & { href: string };
	type Props = ButtonProps | AnchorProps;

	let { variant = 'default', size = 'default', class: className, children, ...restProps }: Props = $props();

	const variants: Record<Variant, string> = {
		default: 'bg-gradient-to-r from-dl-primary to-dl-primary-dark text-dl-bg-dark shadow-lg shadow-dl-primary/30 hover:shadow-dl-primary/40 hover:-translate-y-0.5',
		secondary: 'bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover hover:-translate-y-0.5',
		ghost: 'text-dl-text-muted hover:text-dl-text hover:bg-white/5',
		outline: 'border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary',
		coffee: 'bg-[#ffdd00] text-dl-bg-dark font-semibold shadow-lg shadow-[#ffdd00]/30 hover:shadow-[#ffdd00]/40 hover:-translate-y-0.5'
	};

	const sizes: Record<Size, string> = {
		default: 'px-6 py-2.5 text-sm',
		sm: 'px-4 py-2 text-xs',
		lg: 'px-8 py-3 text-base',
		icon: 'w-10 h-10'
	};

	function getClasses() {
		return cn(
			'inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline',
			variants[variant],
			sizes[size],
			className
		);
	}
</script>

{#if 'href' in restProps && restProps.href}
	<a class={getClasses()} {...restProps as HTMLAnchorAttributes}>
		{@render children()}
	</a>
{:else}
	<button class={getClasses()} {...restProps as HTMLButtonAttributes}>
		{@render children()}
	</button>
{/if}
