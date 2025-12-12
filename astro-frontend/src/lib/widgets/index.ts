/**
 * Widget Registry & Factory
 * 
 * Central place to register and instantiate widgets.
 * Makes it easy to add new widget types (including D3-based ones).
 */

import { BaseWidget, type WidgetConfig } from './BaseWidget';
import { EntityInfoWidget } from './EntityInfoWidget';

// Widget type registry
const WIDGET_TYPES: Record<string, new (config: WidgetConfig) => BaseWidget> = {
  'entity-info': EntityInfoWidget,
  // Future widgets:
  // 'stats-chart': StatsChartWidget,  // D3-based
  // 'performance-graph': PerformanceWidget,  // D3-based
  // 'news-feed': NewsFeedWidget,
};

/**
 * Create a widget instance by type
 */
export function createWidget(
  type: string,
  container: HTMLElement,
  data?: any,
  options?: Record<string, any>
): BaseWidget | null {
  const WidgetClass = WIDGET_TYPES[type];
  
  if (!WidgetClass) {
    console.warn(`Unknown widget type: ${type}`);
    return null;
  }

  return new WidgetClass({ container, data, options });
}

/**
 * Initialize all widgets on a page
 * Looks for elements with data-widget attribute
 */
export function initWidgets(): Map<string, BaseWidget> {
  const widgets = new Map<string, BaseWidget>();
  
  document.querySelectorAll('[data-widget]').forEach((el, index) => {
    const container = el as HTMLElement;
    const type = container.dataset.widget!;
    const dataAttr = container.dataset.widgetData;
    
    let data = null;
    if (dataAttr) {
      try {
        data = JSON.parse(dataAttr);
      } catch (e) {
        console.warn('Failed to parse widget data:', e);
      }
    }

    const widget = createWidget(type, container, data);
    if (widget) {
      const id = container.id || `widget-${index}`;
      widgets.set(id, widget);
    }
  });

  return widgets;
}

/**
 * Register a custom widget type
 * Use this to add D3 or other custom widgets
 */
export function registerWidget(
  type: string,
  WidgetClass: new (config: WidgetConfig) => BaseWidget
): void {
  WIDGET_TYPES[type] = WidgetClass;
}

// Export types
export { BaseWidget, type WidgetConfig } from './BaseWidget';
export { EntityInfoWidget, type EntityInfoData } from './EntityInfoWidget';
