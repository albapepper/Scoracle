<script lang="ts">
  /**
   * Widget component - displays entity info card.
   * Uses BeerCSS styling
   */
  import { IconUser, IconUsers, IconShirtSport } from '@tabler/icons-svelte';
  import type { WidgetData } from '$lib/data/entityApi';

  export let data: WidgetData | null = null;
  export let loading = false;
  export let error: string | null = null;
  export let showDetails = true;

  $: isPlayer = data?.type === 'player';
  $: photoUrl = isPlayer ? data?.photo_url : data?.logo_url;
  $: hasPhoto = !!photoUrl;

  // Build detail badges
  $: details = showDetails
    ? [
        data?.position,
        data?.age ? `Age ${data.age}` : null,
        data?.height,
        data?.conference,
        data?.division,
      ].filter(Boolean) as string[]
    : [];

  function handleImageError(event: Event) {
    const img = event.target as HTMLImageElement;
    img.style.display = 'none';
  }
</script>

{#if loading}
  <!-- Loading skeleton -->
  <article class="surface-variant round padding">
    <nav class="wrap">
      <div class="circle large skeleton"></div>
      <div class="max">
        <div class="skeleton" style="height: 1.25rem; width: 75%;"></div>
        <div class="skeleton small-margin" style="height: 1rem; width: 50%;"></div>
      </div>
    </nav>
  </article>
{:else if error}
  <!-- Error state -->
  <article class="error round padding">
    <p class="center-align">{error}</p>
  </article>
{:else if data}
  <!-- Widget content -->
  <article class="surface-variant round padding">
    <nav class="wrap">
      <!-- Photo/Avatar -->
      {#if hasPhoto}
        <img
          src={photoUrl}
          alt={data.display_name}
          class="circle large"
          on:error={handleImageError}
        />
      {:else}
        <div class="circle large" class:tertiary={isPlayer} class:secondary={!isPlayer}>
          {#if isPlayer}
            <IconUser size={24} />
          {:else}
            <IconUsers size={24} />
          {/if}
        </div>
      {/if}

      <!-- Info -->
      <div class="max">
        <h6 class="no-margin">{data.display_name}</h6>
        
        <nav class="wrap small-margin">
          <span class="chip small" class:tertiary={isPlayer} class:secondary={!isPlayer}>
            {isPlayer ? 'Player' : 'Team'}
          </span>
          {#if data.subtitle}
            <span class="small-text">{data.subtitle}</span>
          {/if}
        </nav>

        {#if details.length > 0}
          <nav class="wrap small-margin">
            {#each details as detail, i}
              <span class="chip small border">
                {#if i === 0 && data.position}
                  <IconShirtSport size={10} />
                {/if}
                {detail}
              </span>
            {/each}
          </nav>
        {/if}
      </div>
    </nav>
  </article>
{/if}

<style>
  img.circle.large {
    width: 64px;
    height: 64px;
    object-fit: cover;
  }
  
  div.circle.large {
    width: 64px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .skeleton {
    background: linear-gradient(
      90deg,
      var(--surface-container) 25%,
      var(--surface-variant) 50%,
      var(--surface-container) 75%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 4px;
  }
  
  @keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }
</style>

