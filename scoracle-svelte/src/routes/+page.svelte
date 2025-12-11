<script lang="ts">
  /**
   * HomePage - main landing page with sport selector and search
   * Uses BeerCSS styling
   */
  import { _ } from 'svelte-i18n';
  import { activeSport, sports } from '$lib/stores/index';
  import SearchForm from '$lib/components/SearchForm.svelte';

  function handleSportChange(sportId: string) {
    activeSport.change(sportId);
  }
</script>

<svelte:head>
  <title>Scoracle - {$_('home.title')}</title>
</svelte:head>

<div class="page center-align middle-align padding">
  <article class="medium-width surface-container round large-padding">
    <!-- Title -->
    <h4 class="center-align">{$_('home.title')}</h4>
    
    <!-- Subtitle -->
    <p class="center-align">{$_('home.selectSport')}</p>
    
    <!-- Sport Selector -->
    <nav class="no-space center-align">
      {#each sports as sport}
        <button
          class="border"
          class:fill={$activeSport === sport.id}
          on:click={() => handleSportChange(sport.id)}
        >
          {sport.display}
        </button>
      {/each}
    </nav>
    
    <!-- Search Form -->
    <div class="large-margin">
      <SearchForm inline />
    </div>
  </article>
</div>

<style>
  .page {
    min-height: calc(100vh - 120px);
  }
</style>

