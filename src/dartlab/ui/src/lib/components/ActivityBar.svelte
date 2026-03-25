<!--
	ActivityBar — 좌측 48px 수직 아이콘 바.
	3 Activity (Chat / Viewer / Dashboard) + 하단 설정/Room.
-->
<script>
	import { MessageSquare, BookOpen, BarChart3, Settings, Users } from "lucide-svelte";

	let {
		activeView = "chat",
		onSwitch,
		onOpenSettings,
		isMobile = false,
		// Room
		roomAvailable = false,
		roomJoined = false,
		roomUnread = 0,
		onRoomClick = null,
		// Provider
		providerLabel = null,
		providerAvailable = false,
		statusLoading = false,
	} = $props();

	const items = [
		{ id: "chat", icon: MessageSquare, label: "Chat", key: "1" },
		{ id: "viewer", icon: BookOpen, label: "Viewer", key: "2" },
		{ id: "dashboard", icon: BarChart3, label: "Dashboard", key: "3" },
	];

	let providerStatus = $derived(
		statusLoading ? "loading" : !providerAvailable ? "warning" : "ok"
	);
	let providerTitle = $derived(
		statusLoading ? "연결 확인 중" : !providerAvailable ? "AI 연결 불가" : "AI 연결됨"
	);
</script>

{#if !isMobile}
	<aside class="activity-bar" role="navigation" aria-label="메인 탐색">
		<div class="activity-bar-top">
			<img src="/avatar.png" alt="DartLab" class="activity-bar-logo" />
			{#each items as item}
				<button
					class="activity-bar-btn {activeView === item.id ? 'active' : ''}"
					onclick={() => onSwitch(item.id)}
					title="{item.label} ({item.key})"
					aria-current={activeView === item.id ? "page" : undefined}
				>
					<svelte:component this={item.icon} size={18} />
					<span class="activity-bar-label">{item.label}</span>
				</button>
			{/each}
		</div>
		<div class="activity-bar-bottom">
			{#if roomAvailable || roomJoined}
				<button
					class="activity-bar-btn {roomJoined ? 'active-accent' : ''}"
					onclick={onRoomClick}
					title="Room"
				>
					<div class="relative">
						<Users size={18} />
						{#if roomUnread > 0}
							<span class="activity-bar-badge">{roomUnread > 9 ? "9+" : roomUnread}</span>
						{/if}
					</div>
				</button>
			{/if}
			<button
				class="activity-bar-btn"
				onclick={onOpenSettings}
				title="설정 — {providerTitle}"
				aria-label="설정 ({providerTitle})"
			>
				<div class="activity-bar-dot {providerStatus}" title={providerTitle}></div>
				<Settings size={18} />
			</button>
		</div>
	</aside>
{/if}
