<script lang="ts">
  /**
   * Footer component
   * Migrated from React Footer.tsx
   */
  import { _ } from 'svelte-i18n';
  import { colorScheme, getThemeColors } from '$lib/stores/theme';

  $: colors = getThemeColors($colorScheme);
  $: year = new Date().getFullYear();
</script>

<footer
  class="mt-auto py-6 border-t"
  style="background-color: {colors.background.primary}; border-color: {colors.ui.border};"
>
  <div class="container mx-auto px-4">
    <div class="flex flex-col md:flex-row items-center justify-between gap-4">
      <!-- Copyright -->
      <p class="text-sm" style="color: {colors.text.secondary};">
        © {year} Scoracle. {$_('footer.allRightsReserved')}
      </p>

      <!-- Links -->
      <div class="flex items-center gap-6">
        <a
          href="/terms"
          class="text-sm hover:underline transition-colors"
          style="color: {colors.text.secondary};"
        >
          {$_('footer.terms')}
        </a>
        <a
          href="/privacy"
          class="text-sm hover:underline transition-colors"
          style="color: {colors.text.secondary};"
        >
          {$_('footer.privacy')}
        </a>
      </div>
    </div>
  </div>
</footer>

