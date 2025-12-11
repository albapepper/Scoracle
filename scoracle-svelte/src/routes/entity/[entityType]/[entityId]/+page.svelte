<script lang="ts">
  /**
   * EntityPage - displays entity profile with stats
   * Uses BeerCSS for styling
   */
  import { _ } from 'svelte-i18n';
  import { IconChartBar, IconTable } from '@tabler/icons-svelte';
  import { activeSport } from '$lib/stores/index';
  import Widget from '$lib/components/Widget.svelte';
  import { buildEntityUrl } from '$lib/utils/entityName';
  import type { PageData } from './$types';

  export let data: PageData;

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

<div class="page padding">
  <div class="grid large-space">
    <!-- Sidebar: Entity Info Card -->
    <article class="s12 m12 l4">
      <div class="center-align">
        <h4>{data.entityName}</h4>

        <div class="medium-padding">
          <Widget
            data={data.entity?.widget}
            loading={!data.entity && !data.error}
            error={data.error}
          />
        </div>

        <a
          href={buildEntityUrl('/mentions', data.entityType, data.entityId, data.sport, data.entityName)}
          class="button primary round"
        >
          {$_('mentions.mentions', { default: 'Mentions' })}
        </a>
      </div>
    </article>

    <!-- Main: Stats Grid -->
    <div class="s12 m12 l8">
      <div class="grid">
        {#each Object.entries(cardTitles) as [key, title]}
          {@const isGraph = viewModes[key] === 'graph'}
          <article class="s12 m6 entity-flip-card-shell" class:is-flipped={!isGraph}>
            <div class="entity-flip-card-inner">
              <!-- Front (Graph) -->
              <div class="entity-flip-card-face entity-flip-card-front">
                <nav>
                  <h6 class="max">{title}</h6>
                  <button
                    class="circle transparent"
                    on:click={() => toggleView(key)}
                    aria-label={$_('entityPage.switchToTable')}
                  >
                    <IconTable size={18} />
                  </button>
                </nav>
                <p class="secondary-text">
                  {$_('entityPage.graphComingSoon')}
                </p>
              </div>

              <!-- Back (Table) -->
              <div class="entity-flip-card-face entity-flip-card-back">
                <nav>
                  <h6 class="max">{title}</h6>
                  <button
                    class="circle transparent"
                    on:click={() => toggleView(key)}
                    aria-label={$_('entityPage.switchToGraph')}
                  >
                    <IconChartBar size={18} />
                  </button>
                </nav>
                <p class="secondary-text">
                  {$_('entityPage.tableComingSoon')}
                </p>
              </div>
            </div>
          </article>
        {/each}
      </div>
    </div>
  </div>
</div>

<style>
  .entity-flip-card-shell {
    perspective: 1000px;
  }
  
  .entity-flip-card-inner {
    position: relative;
    min-height: 200px;
    transition: transform 0.6s;
    transform-style: preserve-3d;
  }
  
  .entity-flip-card-shell.is-flipped .entity-flip-card-inner {
    transform: rotateY(180deg);
  }
  
  .entity-flip-card-face {
    position: absolute;
    inset: 0;
    backface-visibility: hidden;
    padding: 1rem;
    border-radius: 0.75rem;
    background: var(--surface-container);
  }
  
  .entity-flip-card-back {
    transform: rotateY(180deg);
  }
</style>

