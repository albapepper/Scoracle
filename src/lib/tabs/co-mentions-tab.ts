/**
 * Co-Mentions Tab Module
 *
 * Dynamically imported when the Co-mentions tab is first clicked.
 * Cross-references news articles with entity data to find co-mentioned entities.
 *
 * Two views:
 * 1. Entity list — shows co-mentioned entities with mention counts
 * 2. Shared articles — shows articles mentioning both entities (inline drill-down)
 */

import { escapeHtml, parseEntityParams, showState } from '../utils/dom';
import { findCoMentions, entityMatchesText, loadEntitiesForSport, type Article, type CoMention } from '../utils/co-mentions';
import { waitForPageData } from '../utils/api-fetcher';
import { formatDate } from '../utils/date';

class CoMentionsTabManager {
  private container: HTMLElement | null = null;
  private sport: string | null = null;
  private type: string | null = null;
  private id: string | null = null;
  private loaded = false;
  private articles: Article[] = [];

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
      this.articles = newsData?.articles || [];

      if (this.articles.length === 0) {
        this.showEmpty();
        return;
      }

      const entities = await loadEntitiesForSport(this.sport);
      const coMentions = findCoMentions(this.articles, entities, this.id, this.type);

      if (coMentions.length === 0) {
        this.showEmpty();
        return;
      }

      this.renderEntityList(coMentions);
    } catch (err) {
      if (import.meta.env.DEV) {
        console.error('CoMentionsTab error:', err);
      }
      this.showEmpty();
    }
  }

  private renderEntityList(coMentions: CoMention[]): void {
    const listEl = this.container?.querySelector('#comentions-list');
    if (!listEl) return;

    const html = coMentions.map((cm, index) => {
      const name = escapeHtml(cm.entity.name);
      const type = cm.entity.type === 'player' ? 'Player' : 'Team';
      const team = cm.entity.team ? ` - ${escapeHtml(cm.entity.team)}` : '';
      const count = cm.mentionCount;
      const countLabel = count === 1 ? 'mention' : 'mentions';

      return `<div class="comention-item">
        <div class="comention-info">
          <button class="comention-name comention-drill-btn" data-index="${index}">${name}</button>
          <span class="comention-type">${type}${team}</span>
        </div>
        <span class="comention-count">${count} ${countLabel}</span>
      </div>`;
    }).join('');

    listEl.innerHTML = html;

    // Bind click handlers for drill-down
    listEl.querySelectorAll('.comention-drill-btn').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const index = parseInt((e.currentTarget as HTMLElement).dataset.index || '0', 10);
        this.showSharedArticles(coMentions[index]);
      });
    });

    this.showContent();
  }

  private showSharedArticles(coMention: CoMention): void {
    const listEl = this.container?.querySelector('#comentions-list');
    const sharedEl = this.container?.querySelector('#comentions-shared-articles');
    if (!listEl || !sharedEl) return;

    // Filter articles that mention the co-mentioned entity
    const sharedArticles = this.articles.filter(article => {
      const text = article.title || '';
      if (!text) return false;
      return entityMatchesText(coMention.entity.name, text);
    });

    const entityName = escapeHtml(coMention.entity.name);

    let html = `<button class="comentions-back-btn" id="comentions-back-btn">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 12H5M12 19l-7-7 7-7"/>
      </svg>
      Back to co-mentions
    </button>`;

    html += `<p class="comentions-shared-heading">Articles mentioning both entities</p>`;

    if (sharedArticles.length === 0) {
      html += `<p class="comentions-shared-empty">No shared articles found for ${entityName}</p>`;
    } else {
      html += sharedArticles.map(article => {
        const title = escapeHtml(article.title || 'Untitled');
        const link = article.link || '#';
        const source = escapeHtml(article.source || '');
        const date = formatDate(article.pub_date);

        return `<div class="comentions-article-item">
          <h3 class="comentions-article-title">
            <a href="${link}" target="_blank" rel="noopener">${title}</a>
          </h3>
          <div class="comentions-article-meta">${source}${source && date ? ' \u00b7 ' : ''}${date}</div>
        </div>`;
      }).join('');
    }

    sharedEl.innerHTML = html;

    // Bind back button
    const backBtn = sharedEl.querySelector('#comentions-back-btn');
    backBtn?.addEventListener('click', () => this.showEntityListView());

    // Toggle views
    (listEl as HTMLElement).style.display = 'none';
    (sharedEl as HTMLElement).style.display = 'block';
  }

  private showEntityListView(): void {
    const listEl = this.container?.querySelector('#comentions-list');
    const sharedEl = this.container?.querySelector('#comentions-shared-articles');
    if (!listEl || !sharedEl) return;

    (listEl as HTMLElement).style.display = '';
    (sharedEl as HTMLElement).style.display = 'none';
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
