<script lang="ts">
  /**
   * EntityPage - displays entity profile with stats
   * Migrated from React EntityPage.tsx
   */
  import { _ } from 'svelte-i18n';
  import { IconChartBar, IconTable } from '@tabler/icons-svelte';
  import { activeSport } from '$lib/stores/sport';
  import { colorScheme, getThemeColors } from '$lib/stores/theme';
  import Widget from '$lib/components/Widget.svelte';
  import { buildEntityUrl } from '$lib/utils/entityName';
  import type { PageData } from './$types';

  export let data: PageData;

  $: colors = getThemeColors($colorScheme);

  // View modes for stat cards
  let viewModes: Record<string, 'graph' | 'table'> = {
    topLeft: 'graph',
    topRight: 'graph',
    bottomLeft: 'graph',
    bottomRight: 'graph',
  };

  // Card titles based on sport
  $: isFootball = $activeSport?.toUpperCase() === 'FOOTBALL';
  $: isNFL = $activeSport?.toLowerCase() === 'nfl';
  $: cardTitles = {
    topLeft: isFootball ? 'Attacking' : 'Offense',
    topRight: 'Defensive',
    bottomLeft: isNFL ? 'Special Teams' : 'Dead Ball',
    bottomRight: 'Discipline',
  };

  function toggleView(key: string) {
    viewModes = {
      ...viewModes,
      [key]: viewModes[key] === 'graph' ? 'table' : 'graph',
    };
  }
</script>

<svelte:head>
  <title>{data.entityName} - Scoracle</title>
</svelte:head>

<div class="container mx-auto px-4 py-8 max-w-6xl">
  <div class="grid lg:grid-cols-[320px_1fr] gap-6">
    <!-- Sidebar: Entity Info Card -->
    <div class="card p-6 rounded-xl" style="background-color: {colors.background.secondary};">
      <div class="space-y-6 text-center">
        <h1 class="text-2xl font-bold" style="color: {colors.text.primary};">
          {data.entityName}
        </h1>

        <div class="flex justify-center">
          <Widget
            data={data.entity?.widget}
            loading={!data.entity && !data.error}
            error={data.error}
          />
        </div>

        <a
          href={buildEntityUrl('/mentions', data.entityType, data.entityId, data.sport, data.entityName)}
          class="block w-full py-3 px-4 rounded-lg text-center font-medium text-white transition-colors"
          style="background-color: {colors.ui.primary};"
        >
          {$_('mentions.mentions', { default: 'Mentions' })}
        </a>
      </div>
    </div>

    <!-- Main: Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      {#each Object.entries(cardTitles) as [key, title]}
        {@const isGraph = viewModes[key] === 'graph'}
        <div class="entity-flip-card-shell" class:is-flipped={!isGraph}>
          <div class="entity-flip-card-inner relative" style="min-height: 200px;">
            <!-- Front (Graph) -->
            <div
              class="entity-flip-card-face entity-flip-card-front card p-6 rounded-xl absolute inset-0"
              style="background-color: {colors.background.secondary};"
            >
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold" style="color: {$colorScheme === 'dark' ? colors.text.accent : colors.text.primary};">
                  {title}
                </h3>
                <button
                  class="p-2 rounded-lg transition-colors hover:bg-surface-200 dark:hover:bg-surface-700"
                  on:click={() => toggleView(key)}
                  aria-label={$_('entityPage.switchToTable')}
                >
                  <IconTable size={18} style="color: {colors.text.secondary};" />
                </button>
              </div>
              <p style="color: {colors.text.secondary};">
                {$_('entityPage.graphComingSoon')}
              </p>
            </div>

            <!-- Back (Table) -->
            <div
              class="entity-flip-card-face entity-flip-card-back card p-6 rounded-xl absolute inset-0"
              style="background-color: {colors.background.secondary};"
            >
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold" style="color: {$colorScheme === 'dark' ? colors.text.accent : colors.text.primary};">
                  {title}
                </h3>
                <button
                  class="p-2 rounded-lg transition-colors hover:bg-surface-200 dark:hover:bg-surface-700"
                  on:click={() => toggleView(key)}
                  aria-label={$_('entityPage.switchToGraph')}
                >
                  <IconChartBar size={18} style="color: {colors.text.secondary};" />
                </button>
              </div>
              <p style="color: {colors.text.secondary};">
                {$_('entityPage.tableComingSoon')}
              </p>
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
</div>

