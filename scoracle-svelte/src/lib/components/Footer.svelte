<script lang="ts">
  /**
   * Footer component - uses BeerCSS
   */
  import { _ } from 'svelte-i18n';

  $: year = new Date().getFullYear();
</script>

<footer class="surface-variant padding">
  <nav class="wrap">
    <span class="small-text">© {year} Scoracle. {$_('footer.allRightsReserved')}</span>
    <div class="max"></div>
    <a href="/terms" class="small-text link">{$_('footer.terms')}</a>
    <a href="/privacy" class="small-text link">{$_('footer.privacy')}</a>
  </nav>
</footer>

