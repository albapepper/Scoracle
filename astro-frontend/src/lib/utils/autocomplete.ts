/**
 * Autocomplete Manager
 *
 * Shared autocomplete logic for search components.
 * Handles data loading, caching, filtering, and rendering.
 */

import { escapeHtml, getSportDisplay } from './dom';

export interface AutocompleteEntity {
  id: string;
  name: string;
  type: 'player' | 'team';
  team?: string;
}

export interface AutocompleteConfig {
  inputEl: HTMLInputElement;
  suggestionsEl: HTMLElement;
  onSelect: (entity: AutocompleteEntity) => void;
  initialSport?: string;
  renderItem?: (entity: AutocompleteEntity, index: number) => string;
  itemClass?: string;
}

const CACHE_KEY = 'scoracle_autocomplete_cache';
const CACHE_EXPIRY = 24 * 60 * 60 * 1000; // 24 hours

export class AutocompleteManager {
  private inputEl: HTMLInputElement;
  private suggestionsEl: HTMLElement;
  private onSelect: (entity: AutocompleteEntity) => void;
  private renderItem: (entity: AutocompleteEntity, index: number) => string;
  private itemClass: string;

  private currentSport: string;
  private allData: AutocompleteEntity[] = [];
  private suggestions: AutocompleteEntity[] = [];
  private selectedIndex = -1;

  constructor(config: AutocompleteConfig) {
    this.inputEl = config.inputEl;
    this.suggestionsEl = config.suggestionsEl;
    this.onSelect = config.onSelect;
    this.currentSport = config.initialSport || 'nba';
    this.itemClass = config.itemClass || 'suggestion-item';

    // Default render function
    this.renderItem = config.renderItem || ((entity, index) => `
      <button
        type="button"
        data-index="${index}"
        class="${this.itemClass}"
        tabindex="-1"
      >
        <div class="suggestion-name">${escapeHtml(entity.name)}</div>
        <div class="suggestion-meta">${entity.type === 'player' ? (entity.team || 'Player') : 'Team'}</div>
      </button>
    `);

    this.init();
  }

  private async init() {
    await this.loadData();
    this.bindEvents();
  }

  private async loadData() {
    try {
      // Check cache first
      const cache = localStorage.getItem(CACHE_KEY);
      if (cache) {
        const cachedData = JSON.parse(cache);
        if (cachedData[this.currentSport]) {
          const { data, timestamp } = cachedData[this.currentSport];
          if (Date.now() - timestamp < CACHE_EXPIRY) {
            this.allData = data;
            return;
          }
        }
      }

      // Fetch fresh data
      const response = await fetch(`/data/${this.currentSport}.json`);
      if (!response.ok) throw new Error('Failed to fetch data');

      const json = await response.json();
      const items: AutocompleteEntity[] = [];

      // Handle players - support both flat array and items array structure
      if (json.players?.items) {
        items.push(...json.players.items.map((p: any) => ({
          id: String(p.id),
          name: p.name,
          type: 'player' as const,
          team: p.currentTeam || p.team,
        })));
      } else if (Array.isArray(json.players)) {
        items.push(...json.players.map((p: any) => ({
          id: String(p.id),
          name: p.name,
          type: 'player' as const,
          team: p.currentTeam || p.team,
        })));
      }

      // Handle teams - support both flat array and items array structure
      if (json.teams?.items) {
        items.push(...json.teams.items.map((t: any) => ({
          id: String(t.id),
          name: t.name,
          type: 'team' as const,
        })));
      } else if (Array.isArray(json.teams)) {
        items.push(...json.teams.map((t: any) => ({
          id: String(t.id),
          name: t.name,
          type: 'team' as const,
        })));
      }

      this.allData = items;

      // Update cache
      const newCache = cache ? JSON.parse(cache) : {};
      newCache[this.currentSport] = { data: items, timestamp: Date.now() };
      localStorage.setItem(CACHE_KEY, JSON.stringify(newCache));
    } catch (error) {
      if (import.meta.env.DEV) {
        console.error('Failed to load autocomplete data:', error);
      }
    }
  }

  private bindEvents() {
    this.inputEl.addEventListener('input', () => this.onInput());
    this.inputEl.addEventListener('focus', () => this.showSuggestions());
    this.inputEl.addEventListener('blur', () => setTimeout(() => this.hideSuggestions(), 200));
    this.inputEl.addEventListener('keydown', (e) => this.handleKeydown(e));
  }

  private onInput() {
    const query = this.inputEl.value.toLowerCase();

    if (query.length < 2) {
      this.suggestions = [];
      this.selectedIndex = -1;
      this.hideSuggestions();
      return;
    }

    this.suggestions = this.allData
      .filter(item => item.name.toLowerCase().includes(query))
      .slice(0, 10);

    this.selectedIndex = -1;
    this.renderSuggestions();
  }

  private renderSuggestions() {
    if (this.suggestions.length === 0) {
      this.suggestionsEl.innerHTML = '<div class="no-results">No results found</div>';
      this.suggestionsEl.classList.remove('hidden');
      return;
    }

    this.suggestionsEl.innerHTML = this.suggestions
      .map((entity, index) => this.renderItem(entity, index))
      .join('');

    // Bind click handlers
    this.suggestionsEl.querySelectorAll(`.${this.itemClass}`).forEach(el => {
      el.addEventListener('click', () => {
        const index = parseInt((el as HTMLElement).dataset.index || '0');
        this.selectSuggestion(this.suggestions[index]);
      });
    });

    this.showSuggestions();
  }

  private showSuggestions() {
    if (this.suggestions.length > 0 || this.inputEl.value.length >= 2) {
      this.suggestionsEl.classList.remove('hidden');
    }
  }

  private hideSuggestions() {
    this.suggestionsEl.classList.add('hidden');
    this.selectedIndex = -1;
  }

  private selectSuggestion(entity: AutocompleteEntity) {
    this.inputEl.value = entity.name;
    this.hideSuggestions();
    this.onSelect(entity);
  }

  private handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      this.hideSuggestions();
      this.inputEl.blur();
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (this.suggestions.length > 0) {
        this.selectedIndex = Math.min(this.selectedIndex + 1, this.suggestions.length - 1);
        this.updateSelectedState();
      }
      return;
    }

    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (this.suggestions.length > 0) {
        this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
        this.updateSelectedState();
      }
      return;
    }

    if (e.key === 'Enter') {
      e.preventDefault();
      if (this.selectedIndex >= 0 && this.suggestions[this.selectedIndex]) {
        this.selectSuggestion(this.suggestions[this.selectedIndex]);
      } else if (this.suggestions.length > 0) {
        this.selectSuggestion(this.suggestions[0]);
      }
    }
  }

  private updateSelectedState() {
    const items = this.suggestionsEl.querySelectorAll(`.${this.itemClass}`);
    items.forEach((item, index) => {
      item.classList.toggle('selected', index === this.selectedIndex);
      if (index === this.selectedIndex) {
        (item as HTMLElement).scrollIntoView({ block: 'nearest' });
      }
    });
  }

  /**
   * Change the current sport and reload data.
   */
  public setSport(sport: string) {
    if (this.currentSport !== sport) {
      this.currentSport = sport;
      this.allData = [];
      this.suggestions = [];
      this.selectedIndex = -1;
      this.inputEl.value = '';
      this.inputEl.placeholder = `Search ${getSportDisplay(sport)} players or teams...`;
      this.hideSuggestions();
      this.loadData();
    }
  }

  /**
   * Get current sport.
   */
  public getSport(): string {
    return this.currentSport;
  }
}
