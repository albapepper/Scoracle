<script lang="ts">
  /**
   * Root layout - wraps all pages with Header and Footer
   * Uses BeerCSS for styling
   */
  import { onMount } from 'svelte';
  import { isLoading } from 'svelte-i18n';
  import { preloadSport } from '$lib/data/dataLoader';
  import { activeSport } from '$lib/stores/index';
  import Header from '$lib/components/Header.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import '$lib/i18n';
  
  // Import BeerCSS - CSS first, then JS
  import 'beercss/dist/cdn/beer.min.css';
  import '../app.css';
  
  // Import BeerCSS JS for dynamic features (only in browser)
  onMount(async () => {
    await import('beercss');
  });

  // Preload data when sport changes (handles initial load too)
  $: if ($activeSport) {
    preloadSport($activeSport);
  }
</script>

<svelte:head>
  <title>Scoracle</title>
  <meta name="description" content="Scoracle - Sports analytics and player/team mentions" />
</svelte:head>

{#if $isLoading}
  <!-- Loading state while i18n initializes -->
  <div class="page center-align middle-align">
    <progress class="circle"></progress>
  </div>
{:else}
  <main class="responsive">
    <Header />
    <slot />
    <Footer />
  </main>
{/if}

