<script lang="ts">
  /**
   * EntityAutocomplete component - search input with autocomplete dropdown
   * Migrated from React EntityAutocomplete.tsx
   */
  import { createEventDispatcher, onMount } from 'svelte';
  import { _ } from 'svelte-i18n';
  import { IconSearch, IconUser, IconUsers } from '@tabler/icons-svelte';
  import { activeSport, mapSportToBackendCode } from '$lib/stores/sport';
  import { colorScheme, getThemeColors } from '$lib/stores/theme';
  import { searchData, type AutocompleteResult } from '$lib/data/dataLoader';

  let { placeholder = '', value = $bindable('') }: {
    placeholder?: string;
    value?: string;
  } = $props();

  const dispatch = createEventDispatcher<{
    select: AutocompleteResult;
    change: string;
  }>();

  let inputElement = $state<HTMLInputElement | undefined>(undefined);
  let results = $state<AutocompleteResult[]>([]);
  let loading = $state(false);
  let showDropdown = $state(false);
  let activeIndex = $state(-1);
  let debounceTimer = $state<ReturnType<typeof setTimeout> | undefined>(undefined);

  let colors = $derived(getThemeColors($colorScheme));
  let backendSport = $derived(mapSportToBackendCode($activeSport));
  let placeholderText = $derived(placeholder || $_('search.searchPlayerOrTeam'));

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

<div class="relative w-full">
  <!-- Input -->
  <div class="relative">
    <input
      bind:this={inputElement}
      type="text"
      {value}
      placeholder={placeholderText}
      class="w-full pl-10 pr-4 py-2 rounded-full border-0 bg-transparent text-sm focus:outline-none"
      style="color: {colors.text.primary};"
      oninput={handleInput}
      onkeydown={handleKeydown}
      onfocus={handleFocus}
      onblur={handleBlur}
      autocomplete="off"
      aria-autocomplete="list"
      aria-expanded={showDropdown}
    />
    <div class="absolute left-3 top-1/2 -translate-y-1/2">
      <IconSearch size={18} style="color: {colors.text.secondary};" />
    </div>
    {#if loading}
      <div class="absolute right-3 top-1/2 -translate-y-1/2">
        <div
          class="w-4 h-4 border-2 border-t-transparent rounded-full animate-spin"
          style="border-color: {colors.ui.primary}; border-top-color: transparent;"
        />
      </div>
    {/if}
  </div>

  <!-- Dropdown -->
  {#if showDropdown && results.length > 0}
    <ul
      class="absolute z-50 w-full mt-2 py-2 rounded-lg shadow-lg border max-h-72 overflow-y-auto"
      style="background-color: {colors.background.secondary}; border-color: {colors.ui.border};"
      role="listbox"
    >
      {#each results as result, i}
        <li
          class="px-4 py-2 cursor-pointer flex items-center gap-3 transition-colors"
          style="color: {colors.text.primary}; {i === activeIndex ? `background-color: ${colors.background.tertiary};` : ''}"
          onclick={() => handleSelect(result)}
          onmouseenter={() => (activeIndex = i)}
          role="option"
          aria-selected={i === activeIndex}
        >
          <!-- Icon -->
          <span
            class="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0"
            class:bg-blue-500={result.entity_type === 'player'}
            class:bg-green-500={result.entity_type === 'team'}
          >
            {#if result.entity_type === 'player'}
              <IconUser size={12} class="text-white" />
            {:else}
              <IconUsers size={12} class="text-white" />
            {/if}
          </span>

          <!-- Name -->
          <div class="flex-1 min-w-0">
            <div class="truncate font-medium">{result.name}</div>
            {#if result.team || result.league}
              <div class="text-xs truncate" style="color: {colors.text.secondary};">
                {result.team || result.league}
              </div>
            {/if}
          </div>

          <!-- Type badge -->
          <span
            class="px-2 py-0.5 text-xs rounded-full capitalize"
            class:bg-blue-100={result.entity_type === 'player'}
            class:text-blue-700={result.entity_type === 'player'}
            class:dark:bg-blue-900={result.entity_type === 'player'}
            class:dark:text-blue-300={result.entity_type === 'player'}
            class:bg-green-100={result.entity_type === 'team'}
            class:text-green-700={result.entity_type === 'team'}
            class:dark:bg-green-900={result.entity_type === 'team'}
            class:dark:text-green-300={result.entity_type === 'team'}
          >
            {result.entity_type}
          </span>
        </li>
      {/each}
    </ul>
  {/if}
</div>

