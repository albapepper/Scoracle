<script lang="ts">
  /**
   * SearchForm component - main search form with autocomplete
   * Migrated from React SearchForm.tsx
   */
  import { goto } from '$app/navigation';
  import { _ } from 'svelte-i18n';
  import { IconArrowUp } from '@tabler/icons-svelte';
  import { activeSport } from '$lib/stores/sport';
  import { colorScheme, getThemeColors } from '$lib/stores/theme';
  import { searchData, type AutocompleteResult } from '$lib/data/dataLoader';
  import EntityAutocomplete from './EntityAutocomplete.svelte';

  let { inline = false }: { inline?: boolean } = $props();

  let query = $state('');
  let selected = $state<AutocompleteResult | null>(null);
  let isLoading = $state(false);
  let error = $state('');

  let colors = $derived(getThemeColors($colorScheme));

  function handleSelect(event: CustomEvent<AutocompleteResult>) {
    selected = event.detail;
    query = event.detail.label;
  }

  function handleChange(event: CustomEvent<string>) {
    query = event.detail;
    // Clear selection if user types something different
    if (selected && query !== selected.label) {
      selected = null;
    }
  }

  async function handleSubmit(event: Event) {
    event.preventDefault();
    isLoading = true;
    error = '';

    try {
      if (!query.trim() && !selected) {
        throw new Error($_('search.enterTerm'));
      }

      // If user selected from autocomplete, navigate directly
      if (selected) {
        const plainName = (selected.name || selected.label || '').trim();
        const entityType = selected.entity_type || 'player';
        await goto(
          `/mentions/${entityType}/${selected.id}?sport=${$activeSport}&name=${encodeURIComponent(plainName)}`
        );
        return;
      }

      // Fallback: search local bundled data
      const results = await searchData($activeSport, query.trim(), 10);

      if (results.length >= 1) {
        const first = results[0];
        const plainName = (first.name || first.label || query).trim();
        const entityType = first.entity_type || 'player';
        await goto(
          `/mentions/${entityType}/${first.id}?sport=${$activeSport}&name=${encodeURIComponent(plainName)}`
        );
      } else {
        error = $_('search.noneFound', { values: { entity: $_('common.entity.all'), query } });
      }
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : $_('search.errorGeneric');
    } finally {
      isLoading = false;
    }
  }
</script>

{#if inline}
  <!-- Inline form (no card wrapper) -->
  <form on:submit={handleSubmit}>
    <div class="space-y-2">
      <div
        class="search-form-input-wrapper flex items-center rounded-full px-4 py-1 border transition-all"
        style="background-color: {colors.background.secondary}; border-color: {colors.ui.border};"
      >
        <div class="flex-1">
          <EntityAutocomplete
            on:select={handleSelect}
            on:change={handleChange}
          />
        </div>
        <button
          type="submit"
          disabled={isLoading}
          class="ml-2 w-9 h-9 rounded-full flex items-center justify-center text-white transition-colors disabled:opacity-50"
          style="background-color: {colors.ui.primary};"
        >
          {#if isLoading}
            <div
              class="w-4 h-4 border-2 border-t-transparent border-white rounded-full animate-spin"
            />
          {:else}
            <IconArrowUp size={18} />
          {/if}
        </button>
      </div>

      {#if error}
        <p class="text-center text-sm text-red-500 dark:text-red-400">{error}</p>
      {/if}
    </div>
  </form>
{:else}
  <!-- Card-wrapped form -->
  <div
    class="card p-6 rounded-xl"
    style="background-color: {colors.background.tertiary};"
  >
    <form on:submit={handleSubmit}>
      <div class="space-y-2">
        <div
          class="flex items-center rounded-full px-4 py-1 border transition-all"
          style="background-color: {colors.background.secondary}; border-color: {colors.ui.border};"
        >
          <div class="flex-1">
            <EntityAutocomplete
              on:select={handleSelect}
              on:change={handleChange}
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            class="ml-2 w-9 h-9 rounded-full flex items-center justify-center text-white transition-colors disabled:opacity-50"
            style="background-color: {colors.ui.primary};"
          >
            {#if isLoading}
              <div
                class="w-4 h-4 border-2 border-t-transparent border-white rounded-full animate-spin"
              />
            {:else}
              <IconArrowUp size={18} />
            {/if}
          </button>
        </div>

        {#if error}
          <p class="text-center text-sm text-red-500 dark:text-red-400">{error}</p>
        {/if}
      </div>
    </form>
  </div>
{/if}

