<script lang="ts">
  /**
   * EntityAutocomplete component - search input with autocomplete dropdown
   * Uses BeerCSS styling
   */
  import { createEventDispatcher, onMount } from 'svelte';
  import { _ } from 'svelte-i18n';
  import { IconUser, IconUsers } from '@tabler/icons-svelte';
  import { activeSport, mapSportToBackendCode } from '$lib/stores/sport';
  import { searchData, type AutocompleteResult } from '$lib/data/dataLoader';

  export let placeholder = '';
  export let value = '';

  const dispatch = createEventDispatcher<{
    select: AutocompleteResult;
    change: string;
  }>();

  let inputElement: HTMLInputElement;
  let results: AutocompleteResult[] = [];
  let loading = false;
  let showDropdown = false;
  let activeIndex = -1;
  let debounceTimer: ReturnType<typeof setTimeout>;

  $: backendSport = mapSportToBackendCode($activeSport);
  $: placeholderText = placeholder || $_('search.searchPlayerOrTeam');

  async function search(query: string) {
    if (!query || query.trim().length < 2) {
      results = [];
      showDropdown = false;
      return;
    }

    loading = true;
    try {
      results = await searchData(backendSport, query.trim(), 10);
      showDropdown = results.length > 0;
      activeIndex = -1;
    } catch (err) {
      console.error('Search error:', err);
      results = [];
    } finally {
      loading = false;
    }
  }

  function handleInput(event: Event) {
    const input = event.target as HTMLInputElement;
    value = input.value;
    dispatch('change', value);

    // Debounced search
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => search(value), 200);
  }

  function handleSelect(result: AutocompleteResult) {
    value = result.label;
    showDropdown = false;
    dispatch('select', result);
  }

  function handleKeydown(event: KeyboardEvent) {
    if (!showDropdown) return;

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        activeIndex = Math.min(activeIndex + 1, results.length - 1);
        break;
      case 'ArrowUp':
        event.preventDefault();
        activeIndex = Math.max(activeIndex - 1, -1);
        break;
      case 'Enter':
        event.preventDefault();
        if (activeIndex >= 0 && results[activeIndex]) {
          handleSelect(results[activeIndex]);
        }
        break;
      case 'Escape':
        showDropdown = false;
        activeIndex = -1;
        break;
    }
  }

  function handleFocus() {
    if (results.length > 0) {
      showDropdown = true;
    }
  }

  function handleBlur() {
    // Delay to allow click on dropdown item
    setTimeout(() => {
      showDropdown = false;
    }, 150);
  }

  onMount(() => {
    return () => {
      clearTimeout(debounceTimer);
    };
  });
</script>

<div class="autocomplete-wrapper">
  <div class="field label prefix border round">
    <i>search</i>
    <input
      bind:this={inputElement}
      type="text"
      {value}
      on:input={handleInput}
      on:keydown={handleKeydown}
      on:focus={handleFocus}
      on:blur={handleBlur}
      autocomplete="off"
      aria-autocomplete="list"
      aria-haspopup="listbox"
      id="entity-search"
    />
    <label for="entity-search">{placeholderText}</label>
    {#if loading}
      <progress class="circle small absolute"></progress>
    {/if}
  </div>

  <!-- Dropdown -->
  {#if showDropdown && results.length > 0}
    <!-- svelte-ignore a11y-no-noninteractive-element-to-interactive-role -->
    <ul class="autocomplete-dropdown no-padding" role="listbox">
      {#each results as result, i}
        <!-- svelte-ignore a11y-click-events-have-key-events -->
        <li
          class="row padding wave"
          class:active={i === activeIndex}
          on:click={() => handleSelect(result)}
          on:mouseenter={() => (activeIndex = i)}
          role="option"
          aria-selected={i === activeIndex}
        >
          <!-- Icon -->
          <div class="circle small" class:tertiary={result.entity_type === 'player'} class:secondary={result.entity_type === 'team'}>
            {#if result.entity_type === 'player'}
              <IconUser size={14} />
            {:else}
              <IconUsers size={14} />
            {/if}
          </div>

          <!-- Name -->
          <div class="max">
            <span class="bold">{result.name}</span>
            {#if result.team || result.league}
              <div class="small-text">{result.team || result.league}</div>
            {/if}
          </div>

          <!-- Type chip -->
          <span class="chip small">{result.entity_type}</span>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .autocomplete-wrapper {
    position: relative;
    width: 100%;
  }
  
  .autocomplete-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    z-index: 100;
    margin-top: 4px;
    max-height: 300px;
    overflow-y: auto;
    background: var(--surface-container-low);
    border: 1px solid var(--outline);
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    list-style: none;
  }
  
  .autocomplete-dropdown li {
    cursor: pointer;
    text-decoration: none;
    color: inherit;
  }
  
  .autocomplete-dropdown li.active,
  .autocomplete-dropdown li:hover {
    background: var(--surface-container);
  }
  
  .absolute {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
  }
</style>

