/**
 * Component Bus
 *
 * Typed registry replacing (window as any) for inter-component communication.
 * Components register their public APIs here, and consumers access them
 * with full TypeScript type safety.
 *
 * Usage:
 *   // Producer (registers API)
 *   import { register } from '../../lib/utils/component-bus';
 *   register('comparisonModal', { open, close, isOpen });
 *
 *   // Consumer (reads API)
 *   import { get, waitFor } from '../../lib/utils/component-bus';
 *   get('comparisonModal')?.open(...);        // sync, may be undefined
 *   const api = await waitFor('comparisonModal'); // async, waits for registration
 */

import type { AutocompleteEntity } from './autocomplete';

// ─── Type-safe API interfaces for each registered component ─────────────────

export interface ComponentAPIs {
  // Default tab managers (eager-loaded)
  playerStatsTab: {
    load(): void;
    refreshChart(): void;
  };
  teamStatsTab: {
    load(): void;
    refreshChart(): void;
  };
  newsTab: {
    load(): void;
  };

  // Profile widgets
  playerProfileWidget: {
    getSport(): string | null;
    getType(): 'player';
    getId(): string | null;
    getName(): string;
    getPosition(): string | undefined;
    getPositionGroup(): string | undefined;
    hide(): void;
    show(): void;
  };
  teamProfileWidget: {
    getSport(): string | null;
    getType(): 'team';
    getId(): string | null;
    getName(): string;
    hide(): void;
    show(): void;
  };

  // Comparison components
  comparisonModal: {
    open(
      sport: string,
      type: string,
      id: string,
      onSelect: (entity: AutocompleteEntity) => void,
      positionGroup?: string
    ): void;
    close(): void;
    isOpen(): boolean;
  };
  profileWidgetComparison: {
    show(sport: string, primaryType: string, primaryId: string, secondaryType: string, secondaryId: string): void;
    hide(): void;
    isVisible(): boolean;
    getPrimaryData(): unknown;
    getSecondaryData(): unknown;
  };
  statsComparisonContent: {
    show(
      sport: string, primaryType: string, primaryId: string,
      secondaryType: string, secondaryId: string,
      primaryName?: string, secondaryName?: string
    ): void;
    hide(): void;
    isVisible(): boolean;
  };
  swComparison: {
    show(
      sport: string, primaryType: string, primaryId: string,
      secondaryType: string, secondaryId: string,
      primaryName?: string, secondaryName?: string
    ): void;
    hide(): void;
    isVisible(): boolean;
  };
  statsComparison: {
    show(
      sport: string, primaryType: string, primaryId: string,
      secondaryType: string, secondaryId: string,
      primaryName?: string, secondaryName?: string
    ): void;
    hide(): void;
    isVisible(): boolean;
  };
}

export type ComponentName = keyof ComponentAPIs;

// ─── Registry ───────────────────────────────────────────────────────────────

const registry = new Map<string, unknown>();
const waiters = new Map<string, Array<(api: unknown) => void>>();

/**
 * Register a component's public API.
 * Resolves any pending waitFor() calls for this component.
 */
export function register<K extends ComponentName>(name: K, api: ComponentAPIs[K]): void {
  registry.set(name, api);
  // Resolve any pending waitFor() calls
  const pending = waiters.get(name);
  if (pending) {
    pending.forEach(resolve => resolve(api));
    waiters.delete(name);
  }
}

/**
 * Get a component's API synchronously.
 * Returns undefined if the component hasn't registered yet.
 */
export function get<K extends ComponentName>(name: K): ComponentAPIs[K] | undefined {
  return registry.get(name) as ComponentAPIs[K] | undefined;
}

/**
 * Wait for a component to register its API.
 * Resolves immediately if already registered.
 * Rejects after timeout (default 5s).
 */
export function waitFor<K extends ComponentName>(name: K, timeout = 5000): Promise<ComponentAPIs[K]> {
  const existing = registry.get(name);
  if (existing) return Promise.resolve(existing as ComponentAPIs[K]);

  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      const pending = waiters.get(name);
      if (pending) {
        const index = pending.indexOf(wrappedResolve);
        if (index !== -1) pending.splice(index, 1);
      }
      reject(new Error(`Component '${name}' not registered within ${timeout}ms`));
    }, timeout);

    function wrappedResolve(api: unknown): void {
      clearTimeout(timer);
      resolve(api as ComponentAPIs[K]);
    }

    if (!waiters.has(name)) waiters.set(name, []);
    waiters.get(name)!.push(wrappedResolve);
  });
}
