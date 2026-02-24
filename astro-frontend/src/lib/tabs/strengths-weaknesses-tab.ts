/**
 * Strengths & Weaknesses Tab Module
 *
 * Dynamically imported when the Strengths tab is first clicked.
 * Extracts strength/weakness indicators from stats percentile data.
 */

import { escapeHtml, parseEntityParams, showState } from '../utils/dom';
import { waitForPageData } from '../utils/api-fetcher';
import type { Category } from '../utils/stats-categorizer';

interface StatsPageData {
  season: number;
  entity: {
    id: string;
    name: string;
    type: string;
  };
  categories: Category[];
}

interface StrengthWeaknessItem {
  key: string;
  label: string;
  value: number | string | null;
  percentile: number;
  indicator: string;
  count: number;
  type: 'strength' | 'weakness';
}

function getIndicator(percentile: number): { symbol: string; count: number; type: 'strength' | 'weakness' } | null {
  if (percentile >= 90) return { symbol: '+', count: 4, type: 'strength' };
  if (percentile >= 80) return { symbol: '+', count: 3, type: 'strength' };
  if (percentile >= 70) return { symbol: '+', count: 2, type: 'strength' };
  if (percentile <= 10) return { symbol: '-', count: 4, type: 'weakness' };
  if (percentile <= 20) return { symbol: '-', count: 3, type: 'weakness' };
  if (percentile <= 30) return { symbol: '-', count: 2, type: 'weakness' };
  return null;
}

function extractStrengthsWeaknesses(categories: Category[]): {
  strengths: StrengthWeaknessItem[];
  weaknesses: StrengthWeaknessItem[];
} {
  const strengths: StrengthWeaknessItem[] = [];
  const weaknesses: StrengthWeaknessItem[] = [];

  for (const category of categories) {
    for (const stat of category.stats) {
      if (stat.percentile === undefined || stat.percentile === null) continue;

      const indicator = getIndicator(stat.percentile);
      if (!indicator) continue;

      const item: StrengthWeaknessItem = {
        key: stat.key,
        label: stat.label,
        value: stat.value,
        percentile: stat.percentile,
        indicator: indicator.symbol,
        count: indicator.count,
        type: indicator.type,
      };

      if (indicator.type === 'strength') {
        strengths.push(item);
      } else {
        weaknesses.push(item);
      }
    }
  }

  strengths.sort((a, b) => b.percentile - a.percentile);
  weaknesses.sort((a, b) => a.percentile - b.percentile);

  return { strengths, weaknesses };
}

function formatValue(value: number | string | null): string {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'number') {
    if (value > 0 && value < 1) {
      return (value * 100).toFixed(1) + '%';
    }
    if (!Number.isInteger(value)) {
      return value.toFixed(1);
    }
  }
  return String(value);
}

class StrengthsWeaknessesTabManager {
  private container: HTMLElement | null = null;
  private loaded = false;

  constructor() {
    const params = parseEntityParams();
    const viewId = params.type === 'team' ? 'team-entity-view' : 'player-entity-view';
    const parentView = document.getElementById(viewId);
    this.container = parentView?.querySelector('#sw-tab-content') as HTMLElement | null;
  }

  async load(): Promise<void> {
    if (this.loaded || !this.container) return;
    this.loaded = true;

    try {
      const statsData = await waitForPageData('stats', 5000) as StatsPageData;

      if (!statsData || !statsData.categories || statsData.categories.length === 0) {
        this.showEmpty();
        return;
      }

      const { strengths, weaknesses } = extractStrengthsWeaknesses(statsData.categories);
      this.render(strengths, weaknesses);
    } catch (err) {
      if (import.meta.env.DEV) {
        console.error('StrengthsWeaknessesTab error:', err);
      }
      this.showError();
    }
  }

  private render(strengths: StrengthWeaknessItem[], weaknesses: StrengthWeaknessItem[]): void {
    const strengthsList = this.container?.querySelector('#sw-strengths-list');
    const weaknessesList = this.container?.querySelector('#sw-weaknesses-list');

    if (!strengthsList || !weaknessesList) return;

    if (strengths.length > 0) {
      strengthsList.innerHTML = strengths.map(item => this.renderItem(item)).join('');
    } else {
      strengthsList.innerHTML = '<p class="sw-none">No notable strengths</p>';
    }

    if (weaknesses.length > 0) {
      weaknessesList.innerHTML = weaknesses.map(item => this.renderItem(item)).join('');
    } else {
      weaknessesList.innerHTML = '<p class="sw-none">No notable weaknesses</p>';
    }

    this.showContent();
  }

  private renderItem(item: StrengthWeaknessItem): string {
    const indicatorSymbols = item.indicator.repeat(item.count);
    const typeClass = item.type;

    return `
      <div class="sw-item">
        <div class="sw-item-info">
          <span class="sw-item-label">${escapeHtml(item.label)}</span>
          <span class="sw-item-value">${escapeHtml(formatValue(item.value))}</span>
        </div>
        <div class="sw-item-indicator ${typeClass}">
          ${indicatorSymbols}
          <span class="sw-item-percentile">${Math.round(item.percentile)}%</span>
        </div>
      </div>
    `;
  }

  private showContent(): void { showState(this.container, 'sw', 'content'); }
  private showEmpty(): void { showState(this.container, 'sw', 'empty'); }
  private showError(): void { showState(this.container, 'sw', 'error'); }
}

/** Lazy singleton - creates the manager on first call, returns cached instance after. */
let instance: StrengthsWeaknessesTabManager | null = null;

export function init(): StrengthsWeaknessesTabManager {
  if (!instance) {
    instance = new StrengthsWeaknessesTabManager();
  }
  return instance;
}
