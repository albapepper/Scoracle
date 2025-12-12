/**
 * Base Widget Class
 * 
 * All widgets extend this class. Provides:
 * - Container management
 * - Loading/error states
 * - JSON data binding
 * - Lifecycle hooks for render/update/destroy
 * 
 * Designed to be lightweight and D3-compatible.
 */

export interface WidgetConfig {
  container: HTMLElement;
  data?: any;
  options?: Record<string, any>;
}

export abstract class BaseWidget<T = any> {
  protected container: HTMLElement;
  protected data: T | null = null;
  protected options: Record<string, any>;
  protected isLoading = false;
  protected error: string | null = null;

  constructor(config: WidgetConfig) {
    this.container = config.container;
    this.data = config.data || null;
    this.options = config.options || {};
  }

  /**
   * Set loading state and show skeleton
   */
  protected setLoading(loading: boolean): void {
    this.isLoading = loading;
    if (loading) {
      this.renderSkeleton();
    }
  }

  /**
   * Set error state
   */
  protected setError(message: string | null): void {
    this.error = message;
    if (message) {
      this.renderError(message);
    }
  }

  /**
   * Update widget with new data
   */
  public update(data: T): void {
    this.data = data;
    this.error = null;
    this.isLoading = false;
    this.render();
  }

  /**
   * Clear the container
   */
  protected clear(): void {
    this.container.innerHTML = '';
  }

  /**
   * Escape HTML to prevent XSS
   */
  protected escapeHtml(str: string): string {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  /**
   * Override in subclass: render loading skeleton
   */
  protected renderSkeleton(): void {
    this.container.innerHTML = `
      <div class="animate-pulse space-y-3">
        <div class="h-4 bg-slate-300 dark:bg-slate-700 rounded w-3/4"></div>
        <div class="h-4 bg-slate-300 dark:bg-slate-700 rounded w-1/2"></div>
        <div class="h-4 bg-slate-300 dark:bg-slate-700 rounded w-2/3"></div>
      </div>
    `;
  }

  /**
   * Override in subclass: render error state
   */
  protected renderError(message: string): void {
    this.container.innerHTML = `
      <div class="text-center py-4">
        <p class="text-red-600 dark:text-red-400 text-sm">${this.escapeHtml(message)}</p>
      </div>
    `;
  }

  /**
   * Override in subclass: main render method
   */
  protected abstract render(): void;

  /**
   * Override in subclass: cleanup (remove event listeners, etc.)
   */
  public destroy(): void {
    this.clear();
  }
}
