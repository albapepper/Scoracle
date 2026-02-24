/**
 * Co-Mentions Tab Module
 *
 * Dynamically imported when the Co-mentions tab is first clicked.
 * Cross-references news articles with entity data to find co-mentioned entities.
 */

import { escapeHtml, parseEntityParams, showState } from '../utils/dom';
import { findCoMentions, loadEntitiesForSport, type Article, type CoMention } from '../utils/co-mentions';
import { waitForPageData } from '../utils/api-fetcher';

class CoMentionsTabManager {
  private container: HTMLElement | null = null;
  private sport: string | null = null;
  private type: string | null = null;
  private id: string | null = null;
  private loaded = false;

  constructor() {
    const params = parseEntityParams();
    this.sport = params.sport;
    this.type = params.type;
    this.id = params.id;

    const viewId = params.type === 'team' ? 'team-entity-view' : 'player-entity-view';
    const parentView = document.getElementById(viewId);
    this.container = parentView?.querySelector('#comentions-tab-content') as HTMLElement | null;
  }

  async load(): Promise<void> {
    if (this.loaded || !this.container) return;
    this.loaded = true;

    if (!this.sport || !this.type || !this.id) {
      this.showEmpty();
      return;
    }

    try {
      const newsData = await waitForPageData('news', 3000) as { articles?: Article[] };
      const articles = newsData?.articles || [];

      if (articles.length === 0) {
        this.showEmpty();
        return;
      }

      const entities = await loadEntitiesForSport(this.sport);
      const coMentions = findCoMentions(articles, entities, this.id, this.type);

      if (coMentions.length === 0) {
        this.showEmpty();
        return;
      }

      this.render(coMentions);
    } catch (err) {
      if (import.meta.env.DEV) {
        console.error('CoMentionsTab error:', err);
      }
      this.showEmpty();
    }
  }

  private render(coMentions: CoMention[]): void {
    const listEl = this.container?.querySelector('#comentions-list');
    if (!listEl) return;

    const html = coMentions.map(cm => {
      const name = escapeHtml(cm.entity.name);
      const type = cm.entity.type === 'player' ? 'Player' : 'Team';
      const team = cm.entity.team ? ` - ${escapeHtml(cm.entity.team)}` : '';
      const count = cm.mentionCount;
      const countLabel = count === 1 ? 'mention' : 'mentions';

      const link = `/co-mentions?sport=${this.sport}&type=${this.type}&id=${this.id}&coType=${cm.entity.type}&coId=${cm.entity.id}`;

      return `<div class="comention-item">
        <div class="comention-info">
          <a href="${link}" class="comention-name">${name}</a>
          <span class="comention-type">${type}${team}</span>
        </div>
        <span class="comention-count">${count} ${countLabel}</span>
      </div>`;
    }).join('');

    listEl.innerHTML = html;
    this.showContent();
  }

  private showContent(): void {
    showState(this.container, 'comentions', 'content', ['loading', 'content', 'empty']);
  }

  private showEmpty(): void {
    showState(this.container, 'comentions', 'empty', ['loading', 'content', 'empty']);
  }
}

/** Lazy singleton - creates the manager on first call, returns cached instance after. */
let instance: CoMentionsTabManager | null = null;

export function init(): CoMentionsTabManager {
  if (!instance) {
    instance = new CoMentionsTabManager();
  }
  return instance;
}
