<script lang="ts">
  /**
   * Error page - displayed when navigation fails
   * Uses BeerCSS styling
   */
  import { page } from '$app/stores';
  import { _ } from 'svelte-i18n';

  $: status = $page.status;
  $: message = $page.error?.message || $_('notFound.message');
</script>

<div class="page center-align middle-align padding">
  <article class="medium-width surface-container round large-padding center-align">
    <h1 class="primary-text">{status}</h1>
    
    <h4>{status === 404 ? $_('notFound.title') : 'Error'}</h4>
    
    <p>{message}</p>
    
    <nav>
      <a href="/" class="button round">
        <i>home</i>
        <span>{$_('notFound.backHome')}</span>
      </a>
    </nav>
  </article>
</div>

<style>
  .page {
    min-height: calc(100vh - 120px);
  }
  
  h1 {
    font-size: 6rem;
    font-weight: 700;
  }
</style>

