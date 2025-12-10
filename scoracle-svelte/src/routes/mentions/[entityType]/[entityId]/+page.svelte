<script lang="ts">
  /**
   * MentionsPage - displays entity mentions/news
   * Migrated from React MentionsPage.tsx
   */
  import { _ } from 'svelte-i18n';
  import { IconNews, IconChartLine, IconBrandTwitter, IconBrandReddit, IconExternalLink } from '@tabler/icons-svelte';
  import { colorScheme, getThemeColors } from '$lib/stores/index';
  import Widget from '$lib/components/Widget.svelte';
  import { buildEntityUrl } from '$lib/utils/entityName';
  import type { PageData } from './$types';

  export let data: PageData;

  $: colors = getThemeColors($colorScheme);

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

<div class="container mx-auto px-4 py-8 max-w-6xl">
  <div class="grid lg:grid-cols-[320px_1fr] gap-6">
    <!-- Sidebar: Entity Info Card -->
    <div class="lg:sticky lg:top-20 lg:self-start">
      <div class="card p-6 rounded-xl" style="background-color: {colors.background.secondary};">
        <div class="space-y-6 text-center">
          <h1 class="text-2xl font-bold" style="color: {colors.text.primary};">
            {data.entityName}
          </h1>

          <div class="flex justify-center">
            <Widget
              data={data.entity?.widget}
              loading={!data.entity && !data.error}
              error={data.error}
            />
          </div>

          <a
            href={buildEntityUrl('/entity', data.entityType, data.entityId, data.sport, data.entityName)}
            class="block w-full py-3 px-4 rounded-lg text-center font-medium transition-colors border"
            style="border-color: {colors.ui.primary}; color: {colors.ui.primary};"
          >
            {$_('mentions.statisticalProfile')}
          </a>
        </div>
      </div>
    </div>

    <!-- Main: Mentions Content -->
    <div class="space-y-6">
      <!-- Tab Navigation -->
      <div
        class="flex rounded-lg overflow-hidden border"
        style="border-color: {colors.ui.border}; background-color: {colors.background.secondary};"
      >
        {#each tabs as tab}
          <button
            class="flex-1 py-3 px-4 flex items-center justify-center gap-2 font-medium transition-all"
            class:text-white={activeTab === tab.id}
            style={activeTab === tab.id
              ? `background-color: ${colors.ui.primary}; color: white;`
              : `color: ${colors.text.secondary};`}
            on:click={() => (activeTab = tab.id)}
          >
            <svelte:component this={tab.icon} size={18} />
            <span class="hidden sm:inline">{$_(tab.label)}</span>
          </button>
        {/each}
      </div>

      <!-- Tab Content -->
      <div class="card p-6 rounded-xl" style="background-color: {colors.background.secondary};">
        {#if activeTab === 'articles'}
          {#if data.mentions && data.mentions.length > 0}
            <div class="space-y-4">
              {#each data.mentions as article}
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  class="block p-4 rounded-lg border transition-colors hover:border-primary-500"
                  style="border-color: {colors.ui.border}; background-color: {colors.background.tertiary};"
                >
                  <div class="flex items-start gap-4">
                    {#if article.image_url}
                      <img
                        src={article.image_url}
                        alt=""
                        class="w-20 h-20 rounded-lg object-cover flex-shrink-0"
                      />
                    {/if}
                    <div class="flex-1 min-w-0">
                      <h3 class="font-medium mb-1 line-clamp-2" style="color: {colors.text.primary};">
                        {article.title}
                      </h3>
                      <div class="flex items-center gap-2 text-sm" style="color: {colors.text.secondary};">
                        <span>{article.source}</span>
                        <span>•</span>
                        <span>{formatDate(article.published_at)}</span>
                        <IconExternalLink size={14} class="ml-auto flex-shrink-0" />
                      </div>
                      {#if article.summary}
                        <p class="mt-2 text-sm line-clamp-2" style="color: {colors.text.secondary};">
                          {article.summary}
                        </p>
                      {/if}
                    </div>
                  </div>
                </a>
              {/each}
            </div>
          {:else}
            <p class="text-center py-8" style="color: {colors.text.secondary};">
              {$_('mentions.none')}
            </p>
          {/if}
        {:else if activeTab === 'rankings'}
          <p class="text-center py-8" style="color: {colors.text.secondary};">
            Rankings coming soon.
          </p>
        {:else if activeTab === 'twitter'}
          <p class="text-center py-8" style="color: {colors.text.secondary};">
            {$_('mentions.tweetsComingSoon')}
          </p>
        {:else if activeTab === 'reddit'}
          <p class="text-center py-8" style="color: {colors.text.secondary};">
            {$_('mentions.redditComingSoon')}
          </p>
        {/if}
      </div>
    </div>
  </div>
</div>

