<script lang="ts">
  /**
   * Header component - site header with navigation and settings
   * Uses BeerCSS styling
   */
  import { _ } from 'svelte-i18n';
  import { IconMenu2, IconX, IconSun, IconMoon } from '@tabler/icons-svelte';
  import { colorScheme, isDark } from '$lib/stores/theme';
  import { languages, changeLanguage, locale } from '$lib/stores/language';

  let settingsOpen = false;

  function toggleSettings() {
    settingsOpen = !settingsOpen;
  }

  function closeSettings() {
    settingsOpen = false;
  }

  function handleLanguageChange(event: Event) {
    const select = event.target as HTMLSelectElement;
    changeLanguage(select.value);
  }
</script>

<header class="fixed">
  <nav class="surface-variant">
    <button class="circle transparent" on:click={toggleSettings} aria-label={$_('header.menu')}>
      <IconMenu2 size={22} />
    </button>
    
    <a href="/" class="max center-align">
      <img src="/scoracle-logo.png" alt="Scoracle" class="responsive" style="max-height: 2.5rem;" />
    </a>
    
    <div class="field suffix small border round" style="min-width: 80px;">
      <select value={$locale} on:change={handleLanguageChange} aria-label={$_('header.language')}>
        {#each languages as lang}
          <option value={lang.id}>{lang.id.toUpperCase()}</option>
        {/each}
      </select>
      <i>arrow_drop_down</i>
    </div>
  </nav>
</header>

<!-- Settings Drawer -->
<dialog class="left" class:active={settingsOpen}>
  <nav>
    <h5 class="max">{$_('header.settings')}</h5>
    <button class="circle transparent" on:click={closeSettings} aria-label="Close">
      <IconX size={20} />
    </button>
  </nav>
  
  <div class="padding">
    <!-- Appearance Section -->
    <h6>{$_('header.appearance')}</h6>
    
    <label class="switch">
      <input type="checkbox" checked={$isDark} on:change={() => colorScheme.toggle()} />
      <span></span>
      <span class="row">
        {#if $isDark}
          <IconMoon size={18} />
        {:else}
          <IconSun size={18} />
        {/if}
        {$_('header.darkMode')}
      </span>
    </label>
  </div>
</dialog>

<!-- Overlay for drawer -->
{#if settingsOpen}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div class="overlay active" on:click={closeSettings}></div>
{/if}

<style>
  header {
    z-index: 100;
    top: 0;
    left: 0;
    right: 0;
  }
  
  dialog.left {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    width: 280px;
    max-width: 80vw;
    margin: 0;
    border-radius: 0 1rem 1rem 0;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    z-index: 200;
  }
  
  dialog.left.active {
    transform: translateX(0);
  }
  
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 150;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.3s ease;
  }
  
  .overlay.active {
    opacity: 1;
    pointer-events: auto;
  }
</style>

