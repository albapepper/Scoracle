/**
 * Pizza/Radar Chart for Percentile Visualization
 *
 * A D3.js implementation of a pizza/radar-style chart that visualizes
 * stat percentiles as radial slices. Each slice's radius represents
 * the percentile rank (0-100), with labels showing both stat names
 * and raw values.
 *
 * Features:
 * - Radial slices sized by percentile (higher = larger radius)
 * - Background rings at 25%, 50%, 75%, 100%
 * - Color-coded by percentile tier (elite, above avg, avg, below, poor)
 * - Stat labels on outer edge with raw values
 * - Percentile values displayed inside slices
 * - Theme-aware (light/dark mode via CSS variables)
 * - Responsive SVG with viewBox
 */

import * as d3 from 'd3';

export interface PizzaChartStat {
  key: string;
  label: string;
  value: number | string;
  percentile: number;
  categoryId?: string;
}

export interface PizzaChartOptions {
  width?: number;
  height?: number;
  innerRadius?: number;
  outerRadius?: number;
  labelOffset?: number;
}

/**
 * Get the color for a percentile tier from CSS variables.
 */
function getPercentileColor(percentile: number): string {
  // Get computed CSS variable values
  const style = getComputedStyle(document.documentElement);

  if (percentile >= 90) {
    return style.getPropertyValue('--percentile-elite').trim() || '#16a34a';
  }
  if (percentile >= 75) {
    return style.getPropertyValue('--percentile-above').trim() || '#2563eb';
  }
  if (percentile >= 50) {
    return style.getPropertyValue('--percentile-average').trim() || '#d97706';
  }
  if (percentile >= 25) {
    return style.getPropertyValue('--percentile-below').trim() || '#ea580c';
  }
  return style.getPropertyValue('--percentile-poor').trim() || '#dc2626';
}

/**
 * Get chart colors from CSS variables.
 */
function getChartColors() {
  const style = getComputedStyle(document.documentElement);
  return {
    ring: style.getPropertyValue('--chart-ring').trim() || '#e5e5e5',
    ringMajor: style.getPropertyValue('--chart-ring-major').trim() || '#d1d5db',
    label: style.getPropertyValue('--chart-label').trim() || '#1a1a1a',
    sublabel: style.getPropertyValue('--chart-sublabel').trim() || '#666666',
  };
}

export class PizzaChart {
  private container: HTMLElement;
  private svg: d3.Selection<SVGSVGElement, unknown, null, undefined> | null = null;
  private options: Required<PizzaChartOptions>;
  private stats: PizzaChartStat[] = [];

  constructor(container: HTMLElement, options: PizzaChartOptions = {}) {
    this.container = container;
    this.options = {
      width: options.width ?? 360,
      height: options.height ?? 360,
      innerRadius: options.innerRadius ?? 35,
      outerRadius: options.outerRadius ?? 120,
      labelOffset: options.labelOffset ?? 30,
    };
  }

  /**
   * Render the pizza chart with the given stats.
   */
  render(stats: PizzaChartStat[]): void {
    this.stats = stats;

    if (stats.length < 3) {
      // Not enough data for a meaningful chart
      this.container.innerHTML = '<p class="chart-no-data">Not enough data for chart</p>';
      return;
    }

    const { width, height, innerRadius, outerRadius, labelOffset } = this.options;
    const centerX = width / 2;
    const centerY = height / 2;
    const colors = getChartColors();

    // Clear previous content
    this.container.innerHTML = '';

    // Create SVG with viewBox for responsiveness
    this.svg = d3
      .select(this.container)
      .append('svg')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .attr('class', 'pizza-chart-svg')
      .style('width', '100%')
      .style('max-width', `${width}px`)
      .style('height', 'auto');

    // Create main group centered
    const g = this.svg.append('g').attr('transform', `translate(${centerX}, ${centerY})`);

    // Calculate angle for each stat
    const angleStep = (2 * Math.PI) / stats.length;

    // Draw background rings (25%, 50%, 75%, 100%)
    this.drawBackgroundRings(g, innerRadius, outerRadius, colors);

    // Draw pizza slices
    stats.forEach((stat, i) => {
      const startAngle = i * angleStep - Math.PI / 2; // Start from top
      const endAngle = startAngle + angleStep;

      // Calculate slice radius based on percentile
      const percentile = Math.max(0, Math.min(100, stat.percentile));
      const sliceRadius = innerRadius + ((outerRadius - innerRadius) * percentile) / 100;

      // Get color for this percentile
      const color = getPercentileColor(percentile);

      // Create arc generator for the slice
      const arc = d3
        .arc<unknown>()
        .innerRadius(innerRadius)
        .outerRadius(sliceRadius)
        .startAngle(startAngle)
        .endAngle(endAngle)
        .padAngle(0.02)
        .cornerRadius(2);

      // Draw slice
      g.append('path')
        .attr('d', arc({}) as string)
        .attr('fill', color)
        .attr('fill-opacity', 0.85)
        .attr('stroke', colors.ring)
        .attr('stroke-width', 1);

      // Calculate label position (outside the chart)
      const labelAngle = (startAngle + endAngle) / 2;
      const labelRadius = outerRadius + labelOffset;
      const labelX = Math.cos(labelAngle) * labelRadius;
      const labelY = Math.sin(labelAngle) * labelRadius;

      // Determine text anchor based on position
      let textAnchor: 'start' | 'middle' | 'end' = 'middle';
      if (labelX > 10) textAnchor = 'start';
      else if (labelX < -10) textAnchor = 'end';

      // Draw stat label (name)
      g.append('text')
        .attr('x', labelX)
        .attr('y', labelY - 6)
        .attr('text-anchor', textAnchor)
        .attr('fill', colors.label)
        .attr('font-size', '10px')
        .attr('font-weight', '500')
        .text(this.truncateLabel(stat.label, 14));

      // Draw value label
      g.append('text')
        .attr('x', labelX)
        .attr('y', labelY + 8)
        .attr('text-anchor', textAnchor)
        .attr('fill', colors.sublabel)
        .attr('font-size', '9px')
        .text(String(stat.value));

      // Draw percentile inside the slice (if slice is large enough)
      if (percentile >= 20) {
        const percentLabelRadius = innerRadius + (sliceRadius - innerRadius) * 0.6;
        const percentX = Math.cos(labelAngle) * percentLabelRadius;
        const percentY = Math.sin(labelAngle) * percentLabelRadius;

        g.append('text')
          .attr('x', percentX)
          .attr('y', percentY + 3)
          .attr('text-anchor', 'middle')
          .attr('fill', '#ffffff')
          .attr('font-size', '10px')
          .attr('font-weight', '600')
          .text(`${Math.round(stat.percentile)}`);
      }
    });

    // Draw center circle (covers inner radius)
    g.append('circle')
      .attr('r', innerRadius - 2)
      .attr('fill', getComputedStyle(document.documentElement).getPropertyValue('--bg-card').trim() || '#ffffff');

    // Center label
    g.append('text')
      .attr('x', 0)
      .attr('y', 3)
      .attr('text-anchor', 'middle')
      .attr('fill', colors.sublabel)
      .attr('font-size', '9px')
      .attr('font-weight', '500')
      .text('PERCENTILE');
  }

  /**
   * Draw background reference rings.
   */
  private drawBackgroundRings(
    g: d3.Selection<SVGGElement, unknown, null, undefined>,
    innerRadius: number,
    outerRadius: number,
    colors: ReturnType<typeof getChartColors>
  ): void {
    const rings = [25, 50, 75, 100];

    rings.forEach((pct) => {
      const r = innerRadius + ((outerRadius - innerRadius) * pct) / 100;
      g.append('circle')
        .attr('r', r)
        .attr('fill', 'none')
        .attr('stroke', pct === 50 ? colors.ringMajor : colors.ring)
        .attr('stroke-width', pct === 50 ? 1.5 : 1)
        .attr('stroke-dasharray', pct === 50 || pct === 100 ? 'none' : '3,3');
    });
  }

  /**
   * Truncate label if too long.
   */
  private truncateLabel(label: string, maxLength: number): string {
    if (label.length <= maxLength) return label;
    return label.substring(0, maxLength - 1) + '…';
  }

  /**
   * Update the chart (e.g., on theme change).
   */
  refresh(): void {
    if (this.stats.length > 0) {
      this.render(this.stats);
    }
  }

  /**
   * Clean up the chart.
   */
  destroy(): void {
    if (this.svg) {
      this.svg.remove();
      this.svg = null;
    }
    this.container.innerHTML = '';
  }
}
