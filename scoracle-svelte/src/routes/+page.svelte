<script lang="ts">
  /**
   * HomePage - main landing page with sport selector and search
   * Migrated from React HomePage.tsx
   */
  import { _ } from 'svelte-i18n';
  import { activeSport, sports } from '$lib/stores/index';
  import { colorScheme, getThemeColors } from '$lib/stores/index';
  import SearchForm from '$lib/components/SearchForm.svelte';

  let colors = $derived(getThemeColors($colorScheme));

  function handleSportChange(sportId: string) {
    activeSport.change(sportId);
  }
</script>

<svelte:head>
  <title>Scoracle - {$_('home.title')}</title>
</svelte:head>

<div class="container mx-auto px-4 py-8">
  <div class="flex justify-center items-center min-h-[calc(100vh-250px)]">
    <div class="w-full max-w-xl">
      <div
        class="card p-8 rounded-2xl"
        style="background-color: {colors.background.tertiary};"
      >
        <!-- Title -->
        <h1
          class="text-2xl font-bold text-center mb-4"
          style="color: {colors.text.accent};"
        >
          {$_('home.title')}
        </h1>

        <!-- Subtitle -->
        <p
          class="text-center mb-6"
          style="color: {colors.text.secondary};"
        >
          {$_('home.selectSport')}
        </p>

        <!-- Sport Selector -->
        <div class="flex rounded-lg overflow-hidden mb-6 border" style="border-color: {colors.ui.border};">
          {#each sports as sport}
            <button
              class="flex-1 py-3 px-4 text-center font-medium transition-all"
              class:text-white={$activeSport === sport.id}
              style={$activeSport === sport.id
                ? `background-color: ${colors.ui.primary}; color: white;`
                : `background-color: ${colors.background.tertiary}; color: ${colors.text.primary};`}
              onclick={() => handleSportChange(sport.id)}
            >
              {sport.display}
            </button>
          {/each}
        </div>

        <!-- Search Form -->
        <SearchForm inline />
      </div>
    </div>
  </div>
</div>

