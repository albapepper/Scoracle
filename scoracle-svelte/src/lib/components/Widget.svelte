<script lang="ts">
  /**
   * Widget component - displays entity info card.
   * Migrated from React Widget.tsx
   */
  import { IconUser, IconUsers, IconShirtSport } from '@tabler/icons-svelte';
  import type { WidgetData } from '$lib/data/entityApi';

  let { data = null, loading = false, error = null, showDetails = true }: {
    data: WidgetData | null;
    loading?: boolean;
    error?: string | null;
    showDetails?: boolean;
  } = $props();

  let isPlayer = $derived(data?.type === 'player');
  let photoUrl = $derived(isPlayer ? data?.photo_url : data?.logo_url);
  let hasPhoto = $derived(!!photoUrl);

  // Build detail badges
  let details = $derived(showDetails
    ? [
        data?.position,
        data?.age ? `Age ${data.age}` : null,
        data?.height,
        data?.conference,
        data?.division,
      ].filter(Boolean) as string[]
    : []);

  function handleImageError(event: Event) {
    const img = event.target as HTMLImageElement;
    img.style.display = 'none';
  }
</script>

{#if loading}
  <!-- Loading skeleton -->
  <div class="card p-6">
    <div class="flex items-center gap-4">
      <div class="w-16 h-16 rounded-full skeleton" />
      <div class="flex-1 space-y-2">
        <div class="h-5 w-3/4 skeleton rounded" />
        <div class="h-4 w-1/2 skeleton rounded" />
      </div>
    </div>
  </div>
{:else if error}
  <!-- Error state -->
  <div class="card p-6">
    <p class="text-center text-red-500 dark:text-red-400">{error}</p>
  </div>
{:else if data}
  <!-- Widget content -->
  <div class="card p-6">
    <div class="flex items-center gap-4">
      <!-- Photo/Avatar -->
      {#if hasPhoto}
        <img
          src={photoUrl}
          alt={data.display_name}
          class="w-16 h-16 rounded-full object-cover"
          style="background-color: var(--scoracle-bg-tertiary);"
          onerror={handleImageError}
        />
      {:else}
        <div
          class="w-16 h-16 rounded-full flex items-center justify-center"
          class:bg-blue-500={isPlayer}
          class:bg-green-500={!isPlayer}
        >
          {#if isPlayer}
            <IconUser size={24} class="text-white" />
          {:else}
            <IconUsers size={24} class="text-white" />
          {/if}
        </div>
      {/if}

      <!-- Info -->
      <div class="flex-1 min-w-0">
        <h3 class="text-lg font-semibold truncate" style="color: var(--scoracle-text-primary);">
          {data.display_name}
        </h3>

        <div class="flex items-center gap-2 mt-1 flex-wrap">
          <span
            class="px-2 py-0.5 text-xs font-medium rounded-full"
            class:bg-blue-100={isPlayer}
            class:text-blue-700={isPlayer}
            class:dark:bg-blue-900={isPlayer}
            class:dark:text-blue-300={isPlayer}
            class:bg-green-100={!isPlayer}
            class:text-green-700={!isPlayer}
            class:dark:bg-green-900={!isPlayer}
            class:dark:text-green-300={!isPlayer}
          >
            {isPlayer ? 'Player' : 'Team'}
          </span>
          {#if data.subtitle}
            <span class="text-sm" style="color: var(--scoracle-text-secondary);">
              {data.subtitle}
            </span>
          {/if}
        </div>

        {#if details.length > 0}
          <div class="flex flex-wrap gap-1.5 mt-2">
            {#each details as detail, i}
              <span
                class="px-2 py-0.5 text-xs rounded-full border flex items-center gap-1"
                style="border-color: var(--scoracle-ui-border); color: var(--scoracle-text-secondary);"
              >
                {#if i === 0 && data.position}
                  <IconShirtSport size={10} />
                {/if}
                {detail}
              </span>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

