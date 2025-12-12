/**
 * Entity Info Widget
 * 
 * Displays basic entity information in a card.
 * Data: EntityWidget JSON from API
 */

import { BaseWidget, type WidgetConfig } from './BaseWidget';

export interface EntityInfoData {
  display_name?: string;
  subtitle?: string;
  type?: string;
  position?: string;
  age?: string | number;
  height?: string;
  conference?: string;
  division?: string;
  photo_url?: string;
  logo_url?: string;
}

export class EntityInfoWidget extends BaseWidget<EntityInfoData> {
  constructor(config: WidgetConfig) {
    super(config);
    if (this.data) {
      this.render();
    }
  }

  protected renderSkeleton(): void {
    this.container.innerHTML = `
      <div class="animate-pulse">
        <div class="h-6 bg-slate-300 dark:bg-slate-700 rounded w-48 mb-3"></div>
        <div class="h-4 bg-slate-300 dark:bg-slate-700 rounded w-32 mb-4"></div>
        <div class="space-y-3">
          <div class="h-4 bg-slate-300 dark:bg-slate-700 rounded w-24"></div>
          <div class="h-4 bg-slate-300 dark:bg-slate-700 rounded w-20"></div>
          <div class="h-4 bg-slate-300 dark:bg-slate-700 rounded w-28"></div>
        </div>
      </div>
    `;
  }

  protected render(): void {
    if (!this.data) {
      this.renderSkeleton();
      return;
    }

    const d = this.data;
    const fields: string[] = [];

    // Build field rows
    const addField = (label: string, value: string | number | undefined) => {
      if (value !== undefined && value !== null && value !== '') {
        fields.push(`
          <div>
            <dt class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide">${label}</dt>
            <dd class="text-slate-900 dark:text-slate-100">${this.escapeHtml(String(value))}</dd>
          </div>
        `);
      }
    };

    addField('Position', d.position);
    addField('Age', d.age);
    addField('Height', d.height);
    addField('Conference', d.conference);
    addField('Division', d.division);
    addField('Type', d.type);

    this.container.innerHTML = `
      <div class="space-y-4">
        ${d.display_name ? `
          <div>
            <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100">${this.escapeHtml(d.display_name)}</h3>
            ${d.subtitle ? `<p class="text-sm text-slate-600 dark:text-slate-400">${this.escapeHtml(d.subtitle)}</p>` : ''}
          </div>
        ` : ''}
        ${fields.length > 0 ? `
          <dl class="grid grid-cols-2 gap-3 text-sm">
            ${fields.join('')}
          </dl>
        ` : ''}
      </div>
    `;
  }
}
