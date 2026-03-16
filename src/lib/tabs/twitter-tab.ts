/**
 * Twitter Tab Module
 *
 * Dynamically imported when the Twitter tab is first clicked.
 * Fetches journalist tweets about the current entity.
 */

import { escapeHtml, parseEntityParams, showState } from '../utils/dom';
import { formatDate } from '../utils/date';
import { swrFetch, waitForPageData, getPageData, setPageData, CACHE_PRESETS } from '../utils/api-fetcher';
import { profileUrl, twitterStatusUrl, twitterFeedUrl } from '../utils/data-sources';

interface Tweet {
  id: string;
  text: string;
  author: string;
  author_username: string;
  created_at: string;
  metrics?: {
    like_count?: number;
    retweet_count?: number;
  };
}

interface TwitterResponse {
  tweets?: Tweet[];
}

interface TwitterStatusResponse {
  configured: boolean;
}

interface ProfileResponse {
  entity_id: number;
  entity_type: string;
  info: {
    full_name?: string;
    first_name?: string;
    last_name?: string;
    name?: string;
    team?: { name: string };
  };
}

class TwitterTabManager {
  private container: HTMLElement | null;
  private loaded = false;

  constructor() {
    const params = parseEntityParams();
    const viewId = params.type === 'team' ? 'team-entity-view' : 'player-entity-view';
    const parentView = document.getElementById(viewId);
    this.container = parentView?.querySelector('#twitter-tab-content') as HTMLElement | null;
  }

  async load(): Promise<void> {
    if (this.loaded || !this.container) return;
    this.loaded = true;

    const params = parseEntityParams();
    const { sport, type, id } = params;

    if (!sport || !type || !id) {
      this.showEmpty();
      return;
    }

    try {
      const isEnabled = await this.checkTwitterEnabled();
      if (!isEnabled) {
        this.showUnavailable();
        return;
      }

      const entityName = await this.getEntityName(type, id, sport);
      if (!entityName) {
        this.showEmpty();
        return;
      }

      await this.fetchTwitter(entityName, sport);
    } catch (err) {
      if (import.meta.env.DEV) {
        console.error('TwitterTab error:', err);
      }
      this.showError();
    }
  }

  private async checkTwitterEnabled(): Promise<boolean> {
    try {
      const { url, headers } = twitterStatusUrl();
      const { data } = await swrFetch<TwitterStatusResponse>(url, { ...CACHE_PRESETS.twitter, headers });
      return data?.configured ?? false;
    } catch {
      return false;
    }
  }

  private async getEntityName(type: string, id: string, sport: string): Promise<string | null> {
    let profileData = getPageData('widget') as ProfileResponse | undefined;

    if (!profileData) {
      try {
        profileData = await waitForPageData('widget', 1000) as ProfileResponse;
      } catch {
        const { url, headers } = profileUrl(sport, type, id);
        const { data } = await swrFetch<ProfileResponse>(url, { ...CACHE_PRESETS.widget, headers });
        profileData = data;
        if (data) setPageData('widget', data);
      }
    }

    if (!profileData?.info) return null;

    const info = profileData.info;
    if (profileData.entity_type === 'team') {
      return info.name || info.full_name || null;
    }
    return info.full_name || `${info.first_name || ''} ${info.last_name || ''}`.trim() || null;
  }

  private async fetchTwitter(entityName: string, sport: string): Promise<void> {
    const { url, headers } = twitterFeedUrl(entityName, sport, 10);
    const { data } = await swrFetch<TwitterResponse>(url, { ...CACHE_PRESETS.twitter, headers });

    const tweets = data?.tweets || [];
    if (tweets.length === 0) {
      this.showEmpty();
      return;
    }

    this.renderTweets(tweets);
    this.showContent();
  }

  private renderTweets(tweets: Tweet[]): void {
    const list = this.container?.querySelector('#twitter-list');
    if (!list) return;

    list.innerHTML = tweets.map(tweet => {
      const text = escapeHtml(tweet.text);
      const username = escapeHtml(tweet.author_username);
      const date = formatDate(tweet.created_at);
      const likes = tweet.metrics?.like_count || 0;
      const retweets = tweet.metrics?.retweet_count || 0;

      return `<div class="content-item">
        <p class="content-excerpt">${text}</p>
        <div class="content-meta">@${username} · ${date} · ${likes} likes · ${retweets} retweets</div>
      </div>`;
    }).join('');
  }

  private static readonly STATES = ['loading', 'content', 'empty', 'unavailable', 'error'];

  private showContent(): void { showState(this.container, 'twitter', 'content', TwitterTabManager.STATES); }
  private showEmpty(): void { showState(this.container, 'twitter', 'empty', TwitterTabManager.STATES); }
  private showUnavailable(): void { showState(this.container, 'twitter', 'unavailable', TwitterTabManager.STATES); }
  private showError(): void { showState(this.container, 'twitter', 'error', TwitterTabManager.STATES); }
}

/** Lazy singleton - creates the manager on first call, returns cached instance after. */
let instance: TwitterTabManager | null = null;

export function init(): TwitterTabManager {
  if (!instance) {
    instance = new TwitterTabManager();
  }
  return instance;
}
