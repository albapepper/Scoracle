<script lang="ts">
  /**
   * Error page - displayed when navigation fails
   */
  import { page } from '$app/stores';
  import { _ } from 'svelte-i18n';
  import { colorScheme, getThemeColors } from '$lib/stores';

  $: colors = getThemeColors($colorScheme);
  $: status = $page.status;
  $: message = $page.error?.message || $_('notFound.message');
</script>

<div class="container mx-auto px-4 py-16">
  <div class="max-w-md mx-auto text-center space-y-6">
    <h1 class="text-6xl font-bold" style="color: {colors.text.accent};">
      {status}
    </h1>

    <h2 class="text-2xl font-semibold" style="color: {colors.text.primary};">
      {status === 404 ? $_('notFound.title') : 'Error'}
    </h2>

    <p style="color: {colors.text.secondary};">
      {message}
    </p>

    <a
      href="/"
      class="inline-block py-3 px-6 rounded-lg font-medium text-white transition-colors"
      style="background-color: {colors.ui.primary};"
    >
      {$_('notFound.backHome')}
    </a>
  </div>
</div>

