<script lang="ts">
  /**
   * Header component - site header with navigation and settings
   * Migrated from React Header.tsx
   */
  import { _ } from 'svelte-i18n';
  import { IconMenu2, IconX, IconSun, IconMoon } from '@tabler/icons-svelte';
  import { colorScheme, isDark, getThemeColors } from '$lib/stores/theme';
  import { languages, changeLanguage, locale } from '$lib/stores/language';

  let settingsOpen = $state(false);
  let colors = $derived(getThemeColors($colorScheme));

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

<header
  class="sticky top-0 z-50 h-16 border-b transition-colors"
  style="background-color: {colors.background.primary}; border-color: {colors.ui.border};"
>
  <div class="container mx-auto h-full flex items-center justify-between px-4 relative">
    <!-- Left: Hamburger menu -->
    <button
      class="p-2 rounded-lg hover:bg-surface-200 dark:hover:bg-surface-700 transition-colors"
      on:click={toggleSettings}
      aria-label={$_('header.menu')}
    >
      <IconMenu2 size={22} style="color: {colors.text.primary}" />
    </button>

    <!-- Center: Logo -->
    <a href="/" class="absolute left-1/2 -translate-x-1/2 flex items-center">
      <img src="/scoracle-logo.png" alt="Scoracle" class="h-10" />
    </a>

    <!-- Right: Language selector -->
    <select
      class="px-2 py-1 text-sm rounded border bg-transparent cursor-pointer"
      style="color: {colors.text.primary}; border-color: {colors.ui.border};"
      value={$locale}
      on:change={handleLanguageChange}
      aria-label={$_('header.language')}
    >
      {#each languages as lang}
        <option value={lang.id}>{lang.id.toUpperCase()}</option>
      {/each}
    </select>
  </div>
</header>

<!-- Settings Drawer Overlay -->
{#if settingsOpen}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div
    class="fixed inset-0 z-50 bg-black/30"
    on:click={closeSettings}
  >
    <!-- Drawer Panel -->
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div
      class="absolute left-0 top-0 h-full w-80 shadow-xl transition-transform"
      style="background-color: {colors.background.secondary};"
      on:click|stopPropagation
    >
      <!-- Drawer Header -->
      <div class="flex items-center justify-between p-4 border-b" style="border-color: {colors.ui.border};">
        <h2 class="text-lg font-semibold" style="color: {colors.text.primary};">
          {$_('header.settings')}
        </h2>
        <button
          class="p-2 rounded-lg hover:bg-surface-200 dark:hover:bg-surface-700 transition-colors"
          on:click={closeSettings}
          aria-label="Close"
        >
          <IconX size={20} style="color: {colors.text.primary}" />
        </button>
      </div>

      <!-- Drawer Content -->
      <div class="p-4 space-y-6">
        <!-- Appearance Section -->
        <div>
          <h3 class="text-sm font-semibold mb-3" style="color: {colors.text.primary};">
            {$_('header.appearance')}
          </h3>

          <!-- Dark Mode Toggle -->
          <label class="flex items-center justify-between cursor-pointer">
            <span class="flex items-center gap-2" style="color: {colors.text.primary};">
              {#if $isDark}
                <IconMoon size={18} />
              {:else}
                <IconSun size={18} />
              {/if}
              {$_('header.darkMode')}
            </span>
            <button
              class="relative w-12 h-6 rounded-full transition-colors"
              class:bg-primary-500={$isDark}
              class:bg-surface-400={!$isDark}
              on:click={() => colorScheme.toggle()}
              role="switch"
              aria-checked={$isDark}
            >
              <span
                class="absolute top-1 w-4 h-4 bg-white rounded-full transition-transform"
                class:translate-x-1={!$isDark}
                class:translate-x-7={$isDark}
              />
            </button>
          </label>
        </div>
      </div>
    </div>
  </div>
{/if}

