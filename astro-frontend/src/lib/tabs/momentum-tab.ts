/**
 * Momentum Tab Module
 *
 * Dynamically imported when the Momentum tab is first clicked.
 * Computes momentum metrics from the form string (FOOTBALL teams only)
 * and renders a pizza chart + form badges.
 *
 * Currently derives all data client-side from the `form` field in stats data.
 * Future: Will be replaced by a dedicated momentum API endpoint that serves
 * pre-computed momentum metrics for all entity types.
 *
 * Football points weighting: W = 3, D = 1, L = 0
 */

import { parseEntityParams } from '../utils/dom';
import { waitForPageData } from '../utils/api-fetcher';
import { PizzaChart, type PizzaChartStat } from '../charts/pizza-chart';

interface StatsPageData {
  season: number;
  entity: {
    id: string;
    name: string;
    type: string;
  };
  form?: string;
}

/**
 * Compute momentum metrics from a form string (e.g., "WWDLWWWDW").
 *
 * Returns 5 PizzaChartStat entries mapped to a 0-100 scale:
 *  1. Points Rate  - Points earned vs max possible (W=3, D=1, L=0)
 *  2. Win Rate     - Wins / total games
 *  3. Unbeaten     - (Wins + Draws) / total games
 *  4. Streak       - Current unbeaten run length, mapped to /10 scale
 *  5. Trend        - Last 3 games vs overall, centered at 50
 */
function computeMomentumMetrics(form: string): PizzaChartStat[] {
  const results = form.toUpperCase().split('').filter(c => 'WDL'.includes(c));
  const total = results.length;
  if (total === 0) return [];

  const wins = results.filter(r => r === 'W').length;
  const draws = results.filter(r => r === 'D').length;
  const points = wins * 3 + draws;
  const maxPoints = total * 3;

  // 1. Points Rate: points earned / max possible -> 0-100
  const pointsRate = Math.round((points / maxPoints) * 100);

  // 2. Win Rate: wins / total -> 0-100
  const winRate = Math.round((wins / total) * 100);

  // 3. Unbeaten Rate: (wins + draws) / total -> 0-100
  const unbeatenRate = Math.round(((wins + draws) / total) * 100);

  // 4. Current Streak: consecutive non-loss results from most recent game backwards
  //    Mapped to 0-100 where 10 game unbeaten streak = 100
  let streak = 0;
  for (let i = results.length - 1; i >= 0; i--) {
    if (results[i] !== 'L') streak++;
    else break;
  }
  const streakScore = Math.min(100, Math.round((streak / 10) * 100));

  // 5. Recent Trend: compare last 3 games points rate to overall rate
  //    Centered at 50 (stable). > 50 = improving, < 50 = declining.
  const recent = results.slice(-3);
  const recentPoints = recent.filter(r => r === 'W').length * 3
                     + recent.filter(r => r === 'D').length;
  const recentRate = recentPoints / (recent.length * 3);
  const overallRate = points / maxPoints;
  const trendScore = Math.max(0, Math.min(100,
    Math.round(50 + (recentRate - overallRate) * 100)
  ));

  // Determine trend label
  let trendLabel: string;
  if (trendScore > 55) trendLabel = 'Improving';
  else if (trendScore < 45) trendLabel = 'Declining';
  else trendLabel = 'Stable';

  return [
    { key: 'points_rate', label: 'Points Rate', value: `${points}/${maxPoints}`, percentile: pointsRate },
    { key: 'win_rate', label: 'Win Rate', value: `${wins}W in ${total}`, percentile: winRate },
    { key: 'unbeaten_rate', label: 'Unbeaten', value: `${wins + draws}/${total}`, percentile: unbeatenRate },
    { key: 'current_streak', label: 'Streak', value: `${streak} unbeaten`, percentile: streakScore },
    { key: 'recent_trend', label: 'Trend', value: trendLabel, percentile: trendScore },
  ];
}

/**
 * Build a summary string from form results.
 * e.g., "7W 2D 1L · 23/30 pts (77%)"
 */
function buildSummary(form: string): string {
  const results = form.toUpperCase().split('').filter(c => 'WDL'.includes(c));
  const total = results.length;
  if (total === 0) return '';

  const wins = results.filter(r => r === 'W').length;
  const draws = results.filter(r => r === 'D').length;
  const losses = results.filter(r => r === 'L').length;
  const points = wins * 3 + draws;
  const maxPoints = total * 3;
  const pct = Math.round((points / maxPoints) * 100);

  return `${wins}W ${draws}D ${losses}L · ${points}/${maxPoints} pts (${pct}%)`;
}

class MomentumTabManager {
  private container: HTMLElement | null = null;
  private pizzaChart: PizzaChart | null = null;
  private loaded = false;
  private themeObserver: MutationObserver | null = null;

  constructor() {
    const params = parseEntityParams();
    const viewId = params.type === 'team' ? 'team-entity-view' : 'player-entity-view';
    const parentView = document.getElementById(viewId);
    this.container = parentView?.querySelector('#momentum-tab-content') as HTMLElement | null;
  }

  async load(): Promise<void> {
    if (this.loaded || !this.container) return;
    this.loaded = true;

    const params = parseEntityParams();
    const { sport, type } = params;

    // Only FOOTBALL team entities have momentum data currently
    if (!sport || sport.toUpperCase() !== 'FOOTBALL' || type !== 'team') {
      this.showUnavailable();
      return;
    }

    try {
      // Wait for stats data (already fetched by TeamStatsTab)
      const statsData = await waitForPageData('stats', 5000) as StatsPageData;

      if (!statsData || !statsData.form) {
        this.showEmpty();
        return;
      }

      const form = statsData.form;
      const metrics = computeMomentumMetrics(form);

      if (metrics.length < 3) {
        this.showEmpty();
        return;
      }

      this.renderChart(metrics);
      this.renderFormBadges(form);
      this.renderSummary(form);
      this.showContent();
      this.observeThemeChanges();
    } catch (err) {
      if (import.meta.env.DEV) {
        console.error('MomentumTab error:', err);
      }
      this.showError();
    }
  }

  private renderChart(metrics: PizzaChartStat[]): void {
    const chartContainer = this.container?.querySelector('#momentum-pizza-chart') as HTMLElement;
    const chartLoading = this.container?.querySelector('#momentum-chart-loading');

    if (!chartContainer) return;

    // Hide loading skeleton
    chartLoading?.classList.add('hidden');

    this.pizzaChart = new PizzaChart(chartContainer, {
      width: 360,
      height: 360,
      innerRadius: 35,
      outerRadius: 120,
      labelOffset: 30,
    });

    this.pizzaChart.render(metrics);
  }

  private renderFormBadges(form: string): void {
    const formSection = this.container?.querySelector('#momentum-form-section');
    const formDisplay = this.container?.querySelector('#momentum-form-display');

    if (!formSection || !formDisplay) return;

    const badges = form
      .toUpperCase()
      .split('')
      .map(char => {
        let className = '';
        let label = '';

        switch (char) {
          case 'W':
            className = 'win';
            label = 'W';
            break;
          case 'D':
            className = 'draw';
            label = 'D';
            break;
          case 'L':
            className = 'loss';
            label = 'L';
            break;
          default:
            return '';
        }

        const title = label === 'W' ? 'Win' : label === 'D' ? 'Draw' : 'Loss';
        return `<span class="form-badge ${className}" title="${title}">${label}</span>`;
      })
      .filter(Boolean);

    if (badges.length > 0) {
      formDisplay.innerHTML = badges.join('');
      formSection.classList.remove('hidden');
    }
  }

  private renderSummary(form: string): void {
    const summarySection = this.container?.querySelector('#momentum-summary');
    const summaryText = this.container?.querySelector('#momentum-summary-text');

    if (!summarySection || !summaryText) return;

    const summary = buildSummary(form);
    if (summary) {
      summaryText.textContent = summary;
      summarySection.classList.remove('hidden');
    }
  }

  private observeThemeChanges(): void {
    if (this.themeObserver) return;

    this.themeObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          this.pizzaChart?.refresh();
        }
      });
    });

    this.themeObserver.observe(document.documentElement, { attributes: true });
  }

  private showContent(): void {
    this.container?.querySelector('#momentum-chart-loading')?.classList.add('hidden');
    this.container?.querySelector('#momentum-chart-container')?.classList.remove('hidden');
    this.container?.querySelector('#momentum-unavailable')?.classList.add('hidden');
    this.container?.querySelector('#momentum-empty')?.classList.add('hidden');
    this.container?.querySelector('#momentum-error')?.classList.add('hidden');
  }

  private showUnavailable(): void {
    this.container?.querySelector('#momentum-chart-loading')?.classList.add('hidden');
    this.container?.querySelector('#momentum-chart-container')?.classList.add('hidden');
    this.container?.querySelector('#momentum-form-section')?.classList.add('hidden');
    this.container?.querySelector('#momentum-summary')?.classList.add('hidden');
    this.container?.querySelector('#momentum-unavailable')?.classList.remove('hidden');
    this.container?.querySelector('#momentum-empty')?.classList.add('hidden');
    this.container?.querySelector('#momentum-error')?.classList.add('hidden');
  }

  private showEmpty(): void {
    this.container?.querySelector('#momentum-chart-loading')?.classList.add('hidden');
    this.container?.querySelector('#momentum-chart-container')?.classList.add('hidden');
    this.container?.querySelector('#momentum-form-section')?.classList.add('hidden');
    this.container?.querySelector('#momentum-summary')?.classList.add('hidden');
    this.container?.querySelector('#momentum-unavailable')?.classList.add('hidden');
    this.container?.querySelector('#momentum-empty')?.classList.remove('hidden');
    this.container?.querySelector('#momentum-error')?.classList.add('hidden');
  }

  private showError(): void {
    this.container?.querySelector('#momentum-chart-loading')?.classList.add('hidden');
    this.container?.querySelector('#momentum-chart-container')?.classList.add('hidden');
    this.container?.querySelector('#momentum-form-section')?.classList.add('hidden');
    this.container?.querySelector('#momentum-summary')?.classList.add('hidden');
    this.container?.querySelector('#momentum-unavailable')?.classList.add('hidden');
    this.container?.querySelector('#momentum-empty')?.classList.add('hidden');
    this.container?.querySelector('#momentum-error')?.classList.remove('hidden');
  }
}

/** Lazy singleton - creates the manager on first call, returns cached instance after. */
let instance: MomentumTabManager | null = null;

export function init(): MomentumTabManager {
  if (!instance) {
    instance = new MomentumTabManager();
  }
  return instance;
}
