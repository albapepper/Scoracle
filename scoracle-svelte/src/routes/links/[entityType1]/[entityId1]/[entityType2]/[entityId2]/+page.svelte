<script lang="ts">
  /**
   * Links page - displays two entities side by side with shared articles
   */
  import { _ } from 'svelte-i18n';
  import { IconExternalLink } from '@tabler/icons-svelte';
  import { colorScheme, getThemeColors } from '$lib/stores/index';
  import Widget from '$lib/components/Widget.svelte';
  import { buildEntityUrl } from '$lib/utils/entityName';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  let colors = $derived(getThemeColors($colorScheme));

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
  <title>{$_('links.title')} - {data.entity1.name} & {data.entity2.name} - Scoracle</title>
</svelte:head>

<div class="container mx-auto px-4 py-8 max-w-6xl">
  <!-- Header -->
  <div class="mb-8">
    <h1 class="text-3xl font-bold mb-2" style="color: {colors.text.primary};">
      {data.entity1.name} & {data.entity2.name}
    </h1>
    <p class="text-lg" style="color: {colors.text.secondary};">
      {$_('links.articlesAboutBoth')}
    </p>
  </div>

  <!-- Two Entity Widgets Side by Side -->
  <div class="grid md:grid-cols-2 gap-6 mb-8">
    <!-- Entity 1 -->
    <div class="card p-6 rounded-xl" style="background-color: {colors.background.secondary};">
      <div class="space-y-4 text-center">
        <h2 class="text-xl font-bold" style="color: {colors.text.primary};">
          {data.entity1.name}
        </h2>
        
        <div class="flex justify-center">
          <Widget
            data={data.entity1.data?.widget ?? null}
            loading={!data.entity1.data && !data.error}
            error={data.error}
          />
        </div>
        
        <div class="flex gap-2">
          <a
            href={buildEntityUrl('/entity', data.entity1.type, data.entity1.id, data.sport, data.entity1.name)}
            class="flex-1 py-2 px-3 rounded-lg text-center text-sm font-medium transition-colors border"
            style="border-color: {colors.ui.primary}; color: {colors.ui.primary};"
          >
            {$_('mentions.statisticalProfile')}
          </a>
          <a
            href={buildEntityUrl('/mentions', data.entity1.type, data.entity1.id, data.sport, data.entity1.name)}
            class="flex-1 py-2 px-3 rounded-lg text-center text-sm font-medium transition-colors border"
            style="border-color: {colors.ui.primary}; color: {colors.ui.primary};"
          >
            {$_('mentions.mentions')}
          </a>
        </div>
      </div>
    </div>

    <!-- Entity 2 -->
    <div class="card p-6 rounded-xl" style="background-color: {colors.background.secondary};">
      <div class="space-y-4 text-center">
        <h2 class="text-xl font-bold" style="color: {colors.text.primary};">
          {data.entity2.name}
        </h2>
        
        <div class="flex justify-center">
          <Widget
            data={data.entity2.data?.widget ?? null}
            loading={!data.entity2.data && !data.error}
            error={data.error}
          />
        </div>
        
        <div class="flex gap-2">
          <a
            href={buildEntityUrl('/entity', data.entity2.type, data.entity2.id, data.sport, data.entity2.name)}
            class="flex-1 py-2 px-3 rounded-lg text-center text-sm font-medium transition-colors border"
            style="border-color: {colors.ui.primary}; color: {colors.ui.primary};"
          >
            {$_('mentions.statisticalProfile')}
          </a>
          <a
            href={buildEntityUrl('/mentions', data.entity2.type, data.entity2.id, data.sport, data.entity2.name)}
            class="flex-1 py-2 px-3 rounded-lg text-center text-sm font-medium transition-colors border"
            style="border-color: {colors.ui.primary}; color: {colors.ui.primary};"
          >
            {$_('mentions.mentions')}
          </a>
        </div>
      </div>
    </div>
  </div>

  <!-- Shared Articles -->
  <div class="card p-6 rounded-xl" style="background-color: {colors.background.secondary};">
    <h2 class="text-2xl font-bold mb-6" style="color: {colors.text.primary};">
      {$_('links.articlesAboutBoth')}
    </h2>
    
    {#if data.sharedArticles && data.sharedArticles.length > 0}
      <div class="space-y-4">
        {#each data.sharedArticles as article}
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
        {$_('links.noArticles')}
      </p>
    {/if}
  </div>
</div>
