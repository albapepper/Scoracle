<script lang="ts">
  /**
   * Compact Widget variant - smaller, for lists
   * Migrated from React Widget.tsx WidgetCompact
   */
  import { IconUser, IconUsers } from '@tabler/icons-svelte';
  import type { WidgetData } from '$lib/data/entityApi';

  export let data: WidgetData | null = null;
  export let loading = false;

  $: isPlayer = data?.type === 'player';
  $: photoUrl = isPlayer ? data?.photo_url : data?.logo_url;
</script>

{#if loading}
  <div class="flex items-center gap-3">
    <div class="w-8 h-8 rounded-full skeleton" />
    <div class="h-4 w-24 skeleton rounded" />
  </div>
{:else if data}
  <div class="flex items-center gap-3">
    {#if photoUrl}
      <img
        src={photoUrl}
        alt={data.display_name}
        class="w-8 h-8 rounded-full object-cover"
      />
    {:else}
      <div
        class="w-8 h-8 rounded-full flex items-center justify-center"
        class:bg-blue-500={isPlayer}
        class:bg-green-500={!isPlayer}
      >
        {#if isPlayer}
          <IconUser size={14} class="text-white" />
        {:else}
          <IconUsers size={14} class="text-white" />
        {/if}
      </div>
    {/if}
    <span class="text-sm font-medium truncate text-surface-900 dark:text-surface-50">
      {data.display_name}
    </span>
  </div>
{/if}

