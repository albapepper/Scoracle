/**
 * Tab Controller
 *
 * Shared utility for managing tabbed interfaces across content cards.
 * Handles:
 * - Tab button click listeners
 * - CSS class toggling (active state)
 * - Lazy-load callbacks per tab
 * - Optional hover-prefetch per tab
 *
 * Usage:
 *   const controller = new TabController(cardElement, {
 *     onTabChange: (tabId) => { ... },
 *     prefetch: { 'player-similarity': () => similarityTab?.prefetch?.() },
 *   });
 */

export interface TabControllerOptions {
  /** Callback fired when any tab is activated. Receives the data-tab value. Can be async for dynamic imports. */
  onTabChange?: (tabId: string) => void | Promise<void>;

  /** Map of tab IDs to prefetch functions, triggered on mouseenter (once). Can be async for dynamic imports. */
  prefetch?: Record<string, () => void | Promise<void>>;

  /** CSS selector for tab buttons. Defaults to '.tab-btn'. */
  buttonSelector?: string;

  /** CSS selector for tab content panels. Defaults to '.tab-content'. */
  panelSelector?: string;
}

export class TabController {
  private container: HTMLElement;
  private options: TabControllerOptions;

  constructor(container: HTMLElement, options: TabControllerOptions = {}) {
    this.container = container;
    this.options = options;
    this.bindEvents();
  }

  private bindEvents(): void {
    const btnSelector = this.options.buttonSelector || '.tab-btn';
    const panelSelector = this.options.panelSelector || '.tab-content';

    this.container.querySelectorAll(btnSelector).forEach(btn => {
      // Tab click handler
      btn.addEventListener('click', (e) => {
        const target = e.currentTarget as HTMLButtonElement;
        const tabId = target.dataset.tab;
        if (!tabId) return;

        // Update active tab button
        this.container.querySelectorAll(btnSelector).forEach(b => b.classList.remove('active'));
        target.classList.add('active');

        // Update active tab content panel (convention: id = `${data-tab}-tab`)
        this.container.querySelectorAll(panelSelector).forEach(p => p.classList.remove('active'));
        const panel = this.container.querySelector(`#${tabId}-tab`);
        if (panel) panel.classList.add('active');

        // Fire callback for lazy loading / side effects
        this.options.onTabChange?.(tabId);
      });

      // Hover prefetch handler (once per tab)
      const tabId = btn.getAttribute('data-tab');
      if (tabId && this.options.prefetch?.[tabId]) {
        btn.addEventListener('mouseenter', () => {
          this.options.prefetch![tabId]();
        }, { once: true });
      }
    });
  }
}
