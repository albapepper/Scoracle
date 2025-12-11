<script lang="ts">
  /**
   * MentionsPage - displays entity mentions/news
   * Uses BeerCSS styling
   */
  import { _ } from 'svelte-i18n';
  import { IconNews, IconChartLine, IconBrandTwitter, IconBrandReddit, IconExternalLink } from '@tabler/icons-svelte';
  import Widget from '$lib/components/Widget.svelte';
  import { buildEntityUrl } from '$lib/utils/entityName';
  import type { PageData } from './$types';

  export let data: PageData;

  // Active tab state
  let activeTab: 'articles' | 'rankings' | 'twitter' | 'reddit' = 'articles';

  const tabs = [
    { id: 'articles' as const, icon: IconNews, label: 'mentions.articlesTab' },
    { id: 'rankings' as const, icon: IconChartLine, label: 'mentions.rankingsTab' },
    { id: 'twitter' as const, icon: IconBrandTwitter, label: 'mentions.tweetsTab' },
    { id: 'reddit' as const, icon: IconBrandReddit, label: 'mentions.redditTab' },
  ];

  function formatDate(dateStr: string): string {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateStr;
    }
  }
</script>

<svelte:head>
  <title>{$_('mentions.mentions')} - {data.entityName} - Scoracle</title>
</svelte:head>

<div class="grid padding responsive">
  <!-- Sidebar: Entity Info Card -->
  <div class="s12 m4 l3">
    <article class="surface-container round padding">
      <h4 class="center-align">{data.entityName}</h4>
      
      <div class="center-align">
        <Widget
          data={data.entity?.widget}
          loading={!data.entity && !data.error}
          error={data.error}
        />
      </div>
      
      <nav class="center-align">
        <a
          href={buildEntityUrl('/entity', data.entityType, data.entityId, data.sport, data.entityName)}
          class="button border round"
        >
          {$_('mentions.statisticalProfile')}
        </a>
      </nav>
    </article>
  </div>

  <!-- Main: Mentions Content -->
  <div class="s12 m8 l9">
    <!-- Tab Navigation -->
    <nav class="tabs">
      {#each tabs as tab}
        <a
          class:active={activeTab === tab.id}
          href="#!"
          on:click|preventDefault={() => (activeTab = tab.id)}
        >
          <svelte:component this={tab.icon} size={18} />
          <span class="hide-on-small">{$_(tab.label)}</span>
        </a>
      {/each}
    </nav>

    <!-- Tab Content -->
    <article class="surface-container round padding">
      {#if activeTab === 'articles'}
        {#if data.mentions && data.mentions.length > 0}
          {#each data.mentions as article}
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              class="row padding surface-variant round wave margin"
            >
              {#if article.image_url}
                <img
                  src={article.image_url}
                  alt=""
                  class="round"
                  style="width: 80px; height: 80px; object-fit: cover;"
                />
              {/if}
              <div class="max">
                <h6 class="no-margin">{article.title}</h6>
                <nav class="small-text">
                  <span>{article.source}</span>
                  <span>•</span>
                  <span>{formatDate(article.published_at)}</span>
                  <IconExternalLink size={14} />
                </nav>
                {#if article.summary}
                  <p class="small-text">{article.summary}</p>
                {/if}
              </div>
            </a>
          {/each}
        {:else}
          <p class="center-align padding">{$_('mentions.none')}</p>
        {/if}
      {:else if activeTab === 'rankings'}
        <p class="center-align padding">Rankings coming soon.</p>
      {:else if activeTab === 'twitter'}
        <p class="center-align padding">{$_('mentions.tweetsComingSoon')}</p>
      {:else if activeTab === 'reddit'}
        <p class="center-align padding">{$_('mentions.redditComingSoon')}</p>
      {/if}
    </article>
  </div>
</div>

<style>
  a.row {
    text-decoration: none;
    color: inherit;
  }
  
  .tabs a {
    flex: 1;
    justify-content: center;
  }
</style>

