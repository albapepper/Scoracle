<script lang="ts">
  /**
   * Root layout - wraps all pages with Header and Footer
   */
  import { onMount } from 'svelte';
  import { isLoading } from 'svelte-i18n';
  import { colorScheme } from '$lib/stores/index';
  import { preloadSport } from '$lib/data/dataLoader';
  import { activeSport } from '$lib/stores/index';
  import Header from '$lib/components/Header.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import '$lib/i18n';
  import '../app.css';

  // Preload data for initial sport
  onMount(() => {
    preloadSport($activeSport);
  });

  // Subscribe to sport changes to preload data
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
  <div class="min-h-screen flex items-center justify-center bg-surface-50">
    <div class="animate-pulse text-xl">Loading...</div>
  </div>
{:else}
  <div
    class="min-h-screen flex flex-col transition-colors"
    class:scoracle-light={$colorScheme === 'light'}
    class:scoracle-dark={$colorScheme === 'dark'}
    class:dark={$colorScheme === 'dark'}
  >
    <Header />

    <main class="flex-1">
      <slot />
    </main>

    <Footer />
  </div>
{/if}

