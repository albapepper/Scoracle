/**
 * Similarity Tab Module
 *
 * Dynamically imported when the Similarity tab is first clicked (or hovered for prefetch).
 * Fetches and displays similar entities based on embedding similarity.
 */

import { parseEntityParams, escapeHtml, showState } from '../utils/dom';
import { swrFetch, setPageData, CACHE_PRESETS } from '../utils/api-fetcher';
import { similarityUrl } from '../utils/data-sources';
import { getCurrentSeason } from '../utils/season';
import type { SimilarityResponse, SimilarEntity } from '../types';

class SimilarityTabManager {
  private container: HTMLElement | null;
  private loaded = false;
  private prefetched = false;

  constructor() {
    const params = parseEntityParams();
    const viewId = params.type === 'team' ? 'team-entity-view' : 'player-entity-view';
    const parentView = document.getElementById(viewId);
    this.container = parentView?.querySelector('#similarity-tab-content') as HTMLElement | null;
  }

  private buildTarget(sport: string, type: string, id: string) {
    const season = getCurrentSeason(sport);
    return similarityUrl(sport, type, id, season, 5);
  }

  async prefetch(): Promise<void> {
    if (this.prefetched || this.loaded || !this.container) return;
    this.prefetched = true;

    const params = parseEntityParams();
    const { sport, type, id } = params;
    if (!sport || !type || !id) return;

    try {
      const { url, headers } = this.buildTarget(sport, type, id);
      await swrFetch<SimilarityResponse>(url, { ...CACHE_PRESETS.ml, headers });
    } catch {
      // Silent fail on prefetch - will retry on actual load
    }
  }

  async load(): Promise<void> {
    if (this.loaded || !this.container) return;
    this.loaded = true;

    const params = parseEntityParams();
    const { sport, type, id } = params;

    if (!sport || !type || !id) {
      this.showError();
      return;
    }

    try {
      const { url, headers } = this.buildTarget(sport, type, id);
      const { data } = await swrFetch<SimilarityResponse>(url, { ...CACHE_PRESETS.ml, headers });

      if (!data || !data.similar_entities || data.similar_entities.length === 0) {
        this.showEmpty();
        return;
      }

      setPageData('ml', { similarity: data });
      this.renderList(data.similar_entities, sport);
      this.showContent();
    } catch (err) {
      if (import.meta.env.DEV) {
        console.error('SimilarityTab error:', err);
      }
      this.showError();
    }
  }

  private getSimilarityIndicator(score: number): { symbol: string; count: number } {
    const percent = score * 100;
    if (percent >= 95) return { symbol: '+', count: 4 };
    if (percent >= 85) return { symbol: '+', count: 3 };
    if (percent >= 75) return { symbol: '+', count: 2 };
    return { symbol: '+', count: 1 };
  }

  private getDifferenceIndicator(count: number): string {
    if (count >= 3) return '---';
    if (count >= 2) return '--';
    return '-';
  }

  private getDisplayName(entity: SimilarEntity, sport: string): string {
    if (sport.toUpperCase() === 'FOOTBALL' && entity.first_name && entity.last_name) {
      return `${entity.first_name} ${entity.last_name}`;
    }
    return entity.entity_name;
  }

  private getInitials(name: string): string {
    const parts = name.split(' ').filter(Boolean);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  }

  private renderList(entities: SimilarEntity[], sport: string): void {
    const list = this.container?.querySelector('#similarity-list');
    if (!list) return;

    list.innerHTML = entities.map(entity => {
      const scorePercent = Math.round(entity.similarity_score * 100);
      const scoreClass = scorePercent >= 80 ? 'high' : scorePercent >= 60 ? 'medium' : 'low';
      const meta = [entity.position, entity.team].filter(Boolean).join(' - ');

      const displayName = this.getDisplayName(entity, sport);
      const indicator = this.getSimilarityIndicator(entity.similarity_score);
      const indicatorHtml = `<span class="similarity-indicator indicator-${indicator.count}">${indicator.symbol.repeat(indicator.count)}</span>`;

      const initials = this.getInitials(displayName);
      const avatarHtml = entity.photo_url
        ? `<img class="similarity-avatar" src="${escapeHtml(entity.photo_url)}" alt="" loading="lazy" />`
        : `<div class="similarity-avatar similarity-avatar-fallback">${escapeHtml(initials)}</div>`;

      const traitsHtml = Array.isArray(entity.shared_traits) && entity.shared_traits.length > 0
        ? `<div class="similarity-traits"><span class="trait-indicator">++</span> ${entity.shared_traits.map(t => escapeHtml(t)).join(', ')}</div>`
        : '';

      const diffsHtml = Array.isArray(entity.key_differences) && entity.key_differences.length > 0
        ? `<div class="similarity-differences"><span class="diff-indicator">${this.getDifferenceIndicator(entity.key_differences.length)}</span> ${entity.key_differences.map(d => escapeHtml(d)).join(', ')}</div>`
        : '';

      return `
        <li class="similarity-item"
            data-sport="${escapeHtml(sport)}"
            data-type="${escapeHtml(entity.entity_type)}"
            data-id="${entity.entity_id}">
          ${avatarHtml}
          <div class="similarity-item-info">
            <div class="similarity-item-header">
              <p class="similarity-item-name">${escapeHtml(displayName)}</p>
              ${indicatorHtml}
            </div>
            ${meta ? `<span class="similarity-item-meta">${escapeHtml(meta)}</span>` : ''}
            ${traitsHtml}
            ${diffsHtml}
          </div>
          <div class="similarity-score">
            <span class="score-value">${scorePercent}%</span>
            <div class="score-bar">
              <div class="score-bar-fill ${scoreClass}" style="width: ${scorePercent}%"></div>
            </div>
          </div>
        </li>
      `;
    }).join('');

    list.querySelectorAll('.similarity-item').forEach(item => {
      item.addEventListener('click', () => {
        const el = item as HTMLElement;
        const { sport: s, type: t, id: i } = el.dataset;
        if (s && t && i) {
          window.location.href = `/stats?sport=${s}&type=${t}&id=${i}`;
        }
      });
    });
  }

  private showContent(): void { showState(this.container, 'similarity', 'content'); }
  private showEmpty(): void { showState(this.container, 'similarity', 'empty'); }
  private showError(): void { showState(this.container, 'similarity', 'error'); }
}

/** Lazy singleton - creates the manager on first call, returns cached instance after. */
let instance: SimilarityTabManager | null = null;

export function init(): SimilarityTabManager {
  if (!instance) {
    instance = new SimilarityTabManager();
  }
  return instance;
}
