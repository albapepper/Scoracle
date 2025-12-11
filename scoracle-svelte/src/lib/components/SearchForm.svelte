<script lang="ts">
  /**
   * SearchForm component - main search form with autocomplete
   * Uses BeerCSS styling
   */
  import { goto } from '$app/navigation';
  import { _ } from 'svelte-i18n';
  import { IconArrowUp } from '@tabler/icons-svelte';
  import { activeSport } from '$lib/stores/sport';
  import { searchData, type AutocompleteResult } from '$lib/data/dataLoader';
  import EntityAutocomplete from './EntityAutocomplete.svelte';

  /** External reference only - kept for API compatibility */
  export const inline = false;

  let query = '';
  let selected: AutocompleteResult | null = null;
  let isLoading = false;
  let error = '';

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

<form on:submit={handleSubmit}>
  <div class="field round fill suffix">
    <EntityAutocomplete
      on:select={handleSelect}
      on:change={handleChange}
    />
    <button type="submit" class="circle" disabled={isLoading}>
      {#if isLoading}
        <progress class="circle small"></progress>
      {:else}
        <IconArrowUp size={18} />
      {/if}
    </button>
  </div>
  
  {#if error}
    <p class="error-text small-text center-align">{error}</p>
  {/if}
</form>

<style>
  .field {
    position: relative;
  }
  
  .error-text {
    color: var(--error);
    margin-top: 0.5rem;
  }
</style>

