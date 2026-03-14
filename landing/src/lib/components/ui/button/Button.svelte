<script lang="ts">
	import { cn } from '$lib/utils';
	import type { Snippet } from 'svelte';
	import type { HTMLAnchorAttributes, HTMLButtonAttributes } from 'svelte/elements';

	type Variant = 'default' | 'secondary' | 'ghost' | 'outline' | 'coffee' | 'link';
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
		default: 'bg-dl-primary text-white shadow-sm hover:bg-dl-primary/90',
		secondary: 'bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover',
		ghost: 'text-dl-text-muted hover:text-dl-text hover:bg-white/5',
		outline: 'border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50',
		coffee: 'bg-[#ffdd00] text-dl-bg-dark font-semibold shadow-sm hover:bg-[#ffdd00]/90',
		link: 'text-dl-primary underline-offset-4 hover:underline p-0 h-auto'
	};

	const sizes: Record<Size, string> = {
		default: 'px-5 py-2 text-sm h-9',
		sm: 'px-3.5 py-1.5 text-xs h-8',
		lg: 'px-6 py-2.5 text-sm h-10',
		icon: 'w-9 h-9'
	};

	function getClasses() {
		return cn(
			'inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors duration-150 cursor-pointer no-underline whitespace-nowrap',
			variants[variant],
			variant !== 'link' && sizes[size],
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
