/**
 * Pizza/Radar Chart for Percentile Visualization
 *
 * A lightweight SVG implementation (no D3 dependency) of a pizza/radar-style
 * chart that visualizes stat percentiles as radial slices. Each slice's radius
 * represents the percentile rank (0-100), with labels showing both stat names
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

export interface ComparisonEntityData {
  name: string;
  stats: PizzaChartStat[];
}

export interface ComparisonColors {
  primary: string;
  primaryBg: string;
  secondary: string;
  secondaryBg: string;
}

/**
 * Get the color for a percentile tier from CSS variables.
 */
function getPercentileColor(percentile: number): string {
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
    cardBg: style.getPropertyValue('--bg-card').trim() || '#ffffff',
  };
}

/**
 * Get comparison colors from CSS variables.
 */
function getComparisonColors(): ComparisonColors {
  const style = getComputedStyle(document.documentElement);
  const isDark = document.documentElement.classList.contains('dark');

  return {
    primary: style.getPropertyValue(isDark ? '--compare-primary-dark' : '--compare-primary').trim() || '#2563eb',
    primaryBg: style.getPropertyValue('--compare-primary-bg').trim() || '#dbeafe',
    secondary: style.getPropertyValue(isDark ? '--compare-secondary-dark' : '--compare-secondary').trim() || '#dc2626',
    secondaryBg: style.getPropertyValue('--compare-secondary-bg').trim() || '#fee2e2',
  };
}

/**
 * Convert polar coordinates to cartesian.
 */
function polarToCartesian(centerX: number, centerY: number, radius: number, angleInRadians: number): { x: number; y: number } {
  return {
    x: centerX + radius * Math.cos(angleInRadians),
    y: centerY + radius * Math.sin(angleInRadians),
  };
}

/**
 * Generate an SVG arc path.
 */
function describeArc(
  centerX: number,
  centerY: number,
  innerRadius: number,
  outerRadius: number,
  startAngle: number,
  endAngle: number,
  padAngle: number = 0
): string {
  // Apply pad angle
  const adjustedStart = startAngle + padAngle / 2;
  const adjustedEnd = endAngle - padAngle / 2;

  const outerStart = polarToCartesian(centerX, centerY, outerRadius, adjustedStart);
  const outerEnd = polarToCartesian(centerX, centerY, outerRadius, adjustedEnd);
  const innerStart = polarToCartesian(centerX, centerY, innerRadius, adjustedStart);
  const innerEnd = polarToCartesian(centerX, centerY, innerRadius, adjustedEnd);

  const largeArcFlag = adjustedEnd - adjustedStart > Math.PI ? 1 : 0;

  // Create arc path: outer arc -> line to inner -> inner arc (reversed) -> close
  return [
    'M', outerStart.x, outerStart.y,
    'A', outerRadius, outerRadius, 0, largeArcFlag, 1, outerEnd.x, outerEnd.y,
    'L', innerEnd.x, innerEnd.y,
    'A', innerRadius, innerRadius, 0, largeArcFlag, 0, innerStart.x, innerStart.y,
    'Z',
  ].join(' ');
}

/**
 * Create an SVG element with proper namespace.
 */
function createSvgElement<K extends keyof SVGElementTagNameMap>(tag: K): SVGElementTagNameMap[K] {
  return document.createElementNS('http://www.w3.org/2000/svg', tag);
}

/**
 * Truncate label if too long.
 */
function truncateLabel(label: string, maxLength: number): string {
  if (label.length <= maxLength) return label;
  return label.substring(0, maxLength - 1) + '…';
}

export class PizzaChart {
  private container: HTMLElement;
  private svg: SVGSVGElement | null = null;
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
    this.svg = createSvgElement('svg');
    this.svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    this.svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    this.svg.setAttribute('class', 'pizza-chart-svg');
    this.svg.style.width = '100%';
    this.svg.style.maxWidth = `${width}px`;
    this.svg.style.height = 'auto';

    // Create main group
    const g = createSvgElement('g');
    g.setAttribute('transform', `translate(${centerX}, ${centerY})`);

    // Calculate angle for each stat
    const angleStep = (2 * Math.PI) / stats.length;

    // Draw background rings (25%, 50%, 75%, 100%)
    this.drawBackgroundRings(g, innerRadius, outerRadius, colors, centerX, centerY);

    // Draw pizza slices
    stats.forEach((stat, i) => {
      const startAngle = i * angleStep - Math.PI / 2; // Start from top
      const endAngle = startAngle + angleStep;

      // Calculate slice radius based on percentile
      const percentile = Math.max(0, Math.min(100, stat.percentile));
      const sliceRadius = innerRadius + ((outerRadius - innerRadius) * percentile) / 100;

      // Get color for this percentile
      const color = getPercentileColor(percentile);

      // Create arc path
      const arcPath = describeArc(0, 0, innerRadius, sliceRadius, startAngle, endAngle, 0.02);

      // Draw slice
      const path = createSvgElement('path');
      path.setAttribute('d', arcPath);
      path.setAttribute('fill', color);
      path.setAttribute('fill-opacity', '0.85');
      path.setAttribute('stroke', colors.ring);
      path.setAttribute('stroke-width', '1');
      g.appendChild(path);

      // Calculate label position (outside the chart)
      const labelAngle = (startAngle + endAngle) / 2;
      const labelRadius = outerRadius + labelOffset;
      const labelX = Math.cos(labelAngle) * labelRadius;
      const labelY = Math.sin(labelAngle) * labelRadius;

      // Determine text anchor based on position
      let textAnchor: string = 'middle';
      if (labelX > 10) textAnchor = 'start';
      else if (labelX < -10) textAnchor = 'end';

      // Draw stat label (name)
      const labelText = createSvgElement('text');
      labelText.setAttribute('x', String(labelX));
      labelText.setAttribute('y', String(labelY - 6));
      labelText.setAttribute('text-anchor', textAnchor);
      labelText.setAttribute('fill', colors.label);
      labelText.setAttribute('font-size', '10px');
      labelText.setAttribute('font-weight', '500');
      labelText.textContent = truncateLabel(stat.label, 14);
      g.appendChild(labelText);

      // Draw value label
      const valueText = createSvgElement('text');
      valueText.setAttribute('x', String(labelX));
      valueText.setAttribute('y', String(labelY + 8));
      valueText.setAttribute('text-anchor', textAnchor);
      valueText.setAttribute('fill', colors.sublabel);
      valueText.setAttribute('font-size', '9px');
      valueText.textContent = String(stat.value);
      g.appendChild(valueText);

      // Draw percentile inside the slice (if slice is large enough)
      if (percentile >= 20) {
        const percentLabelRadius = innerRadius + (sliceRadius - innerRadius) * 0.6;
        const percentX = Math.cos(labelAngle) * percentLabelRadius;
        const percentY = Math.sin(labelAngle) * percentLabelRadius;

        const percentText = createSvgElement('text');
        percentText.setAttribute('x', String(percentX));
        percentText.setAttribute('y', String(percentY + 3));
        percentText.setAttribute('text-anchor', 'middle');
        percentText.setAttribute('fill', '#ffffff');
        percentText.setAttribute('font-size', '10px');
        percentText.setAttribute('font-weight', '600');
        percentText.textContent = String(Math.round(stat.percentile));
        g.appendChild(percentText);
      }
    });

    // Draw center circle (covers inner radius)
    const centerCircle = createSvgElement('circle');
    centerCircle.setAttribute('r', String(innerRadius - 2));
    centerCircle.setAttribute('fill', colors.cardBg);
    g.appendChild(centerCircle);

    // Center label
    const centerLabel = createSvgElement('text');
    centerLabel.setAttribute('x', '0');
    centerLabel.setAttribute('y', '3');
    centerLabel.setAttribute('text-anchor', 'middle');
    centerLabel.setAttribute('fill', colors.sublabel);
    centerLabel.setAttribute('font-size', '9px');
    centerLabel.setAttribute('font-weight', '500');
    centerLabel.textContent = 'PERCENTILE';
    g.appendChild(centerLabel);

    this.svg.appendChild(g);
    this.container.appendChild(this.svg);
  }

  /**
   * Render an overlapping comparison chart for two entities.
   * Primary entity is rendered as filled slices, secondary as outlined.
   */
  renderComparison(primary: ComparisonEntityData, secondary: ComparisonEntityData): void {
    // Build a unified stat list from both entities
    const allStatKeys = new Set<string>();
    primary.stats.forEach(s => allStatKeys.add(s.key));
    secondary.stats.forEach(s => allStatKeys.add(s.key));

    const statKeyArray = Array.from(allStatKeys);

    if (statKeyArray.length < 3) {
      this.container.innerHTML = '<p class="chart-no-data">Not enough data for comparison chart</p>';
      return;
    }

    // Create lookup maps
    const primaryMap = new Map(primary.stats.map(s => [s.key, s]));
    const secondaryMap = new Map(secondary.stats.map(s => [s.key, s]));

    const { width, height, innerRadius, outerRadius, labelOffset } = this.options;
    const centerX = width / 2;
    const centerY = height / 2;
    const colors = getChartColors();
    const compareColors = getComparisonColors();

    // Clear previous content
    this.container.innerHTML = '';

    // Create SVG with viewBox for responsiveness
    this.svg = createSvgElement('svg');
    this.svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    this.svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    this.svg.setAttribute('class', 'pizza-chart-svg pizza-chart-comparison');
    this.svg.style.width = '100%';
    this.svg.style.maxWidth = `${width}px`;
    this.svg.style.height = 'auto';

    // Create main group
    const g = createSvgElement('g');
    g.setAttribute('transform', `translate(${centerX}, ${centerY})`);

    // Calculate angle for each stat
    const angleStep = (2 * Math.PI) / statKeyArray.length;

    // Draw background rings
    this.drawBackgroundRings(g, innerRadius, outerRadius, colors, centerX, centerY);

    // Draw slices for both entities
    statKeyArray.forEach((key, i) => {
      const startAngle = i * angleStep - Math.PI / 2; // Start from top
      const endAngle = startAngle + angleStep;
      const labelAngle = (startAngle + endAngle) / 2;

      const primaryStat = primaryMap.get(key);
      const secondaryStat = secondaryMap.get(key);

      // Draw primary entity slice (filled)
      if (primaryStat) {
        const percentile = Math.max(0, Math.min(100, primaryStat.percentile));
        const sliceRadius = innerRadius + ((outerRadius - innerRadius) * percentile) / 100;
        const arcPath = describeArc(0, 0, innerRadius, sliceRadius, startAngle, endAngle, 0.03);

        const path = createSvgElement('path');
        path.setAttribute('d', arcPath);
        path.setAttribute('fill', compareColors.primary);
        path.setAttribute('fill-opacity', '0.7');
        path.setAttribute('stroke', compareColors.primary);
        path.setAttribute('stroke-width', '1');
        path.setAttribute('class', 'comparison-slice primary');
        g.appendChild(path);
      }

      // Draw secondary entity slice (outlined/semi-transparent overlay)
      if (secondaryStat) {
        const percentile = Math.max(0, Math.min(100, secondaryStat.percentile));
        const sliceRadius = innerRadius + ((outerRadius - innerRadius) * percentile) / 100;
        const arcPath = describeArc(0, 0, innerRadius, sliceRadius, startAngle, endAngle, 0.03);

        const path = createSvgElement('path');
        path.setAttribute('d', arcPath);
        path.setAttribute('fill', compareColors.secondary);
        path.setAttribute('fill-opacity', '0.3');
        path.setAttribute('stroke', compareColors.secondary);
        path.setAttribute('stroke-width', '2');
        path.setAttribute('stroke-dasharray', '4,2');
        path.setAttribute('class', 'comparison-slice secondary');
        g.appendChild(path);
      }

      // Draw stat label (use primary stat if available, else secondary)
      const labelStat = primaryStat || secondaryStat;
      if (labelStat) {
        const labelRadius = outerRadius + labelOffset;
        const labelX = Math.cos(labelAngle) * labelRadius;
        const labelY = Math.sin(labelAngle) * labelRadius;

        // Determine text anchor based on position
        let textAnchor: string = 'middle';
        if (labelX > 10) textAnchor = 'start';
        else if (labelX < -10) textAnchor = 'end';

        // Draw stat label (name)
        const labelText = createSvgElement('text');
        labelText.setAttribute('x', String(labelX));
        labelText.setAttribute('y', String(labelY - 6));
        labelText.setAttribute('text-anchor', textAnchor);
        labelText.setAttribute('fill', colors.label);
        labelText.setAttribute('font-size', '10px');
        labelText.setAttribute('font-weight', '500');
        labelText.textContent = truncateLabel(labelStat.label, 14);
        g.appendChild(labelText);

        // Draw value labels for both entities (stacked)
        const primaryValue = primaryStat ? String(primaryStat.value) : '-';
        const secondaryValue = secondaryStat ? String(secondaryStat.value) : '-';

        const valuesText = createSvgElement('text');
        valuesText.setAttribute('x', String(labelX));
        valuesText.setAttribute('y', String(labelY + 8));
        valuesText.setAttribute('text-anchor', textAnchor);
        valuesText.setAttribute('font-size', '8px');

        // Primary value
        const primarySpan = createSvgElement('tspan');
        primarySpan.setAttribute('fill', compareColors.primary);
        primarySpan.setAttribute('font-weight', '600');
        primarySpan.textContent = primaryValue;
        valuesText.appendChild(primarySpan);

        // Separator
        const sepSpan = createSvgElement('tspan');
        sepSpan.setAttribute('fill', colors.sublabel);
        sepSpan.textContent = ' / ';
        valuesText.appendChild(sepSpan);

        // Secondary value
        const secondarySpan = createSvgElement('tspan');
        secondarySpan.setAttribute('fill', compareColors.secondary);
        secondarySpan.setAttribute('font-weight', '600');
        secondarySpan.textContent = secondaryValue;
        valuesText.appendChild(secondarySpan);

        g.appendChild(valuesText);
      }
    });

    // Draw center circle
    const centerCircle = createSvgElement('circle');
    centerCircle.setAttribute('r', String(innerRadius - 2));
    centerCircle.setAttribute('fill', colors.cardBg);
    g.appendChild(centerCircle);

    // Center label - "VS"
    const centerLabel = createSvgElement('text');
    centerLabel.setAttribute('x', '0');
    centerLabel.setAttribute('y', '5');
    centerLabel.setAttribute('text-anchor', 'middle');
    centerLabel.setAttribute('fill', colors.sublabel);
    centerLabel.setAttribute('font-size', '12px');
    centerLabel.setAttribute('font-weight', '700');
    centerLabel.textContent = 'VS';
    g.appendChild(centerLabel);

    this.svg.appendChild(g);
    this.container.appendChild(this.svg);
  }

  /**
   * Draw background reference rings.
   */
  private drawBackgroundRings(
    g: SVGGElement,
    innerRadius: number,
    outerRadius: number,
    colors: ReturnType<typeof getChartColors>,
    _centerX: number,
    _centerY: number
  ): void {
    const rings = [25, 50, 75, 100];

    rings.forEach((pct) => {
      const r = innerRadius + ((outerRadius - innerRadius) * pct) / 100;
      const circle = createSvgElement('circle');
      circle.setAttribute('r', String(r));
      circle.setAttribute('fill', 'none');
      circle.setAttribute('stroke', pct === 50 ? colors.ringMajor : colors.ring);
      circle.setAttribute('stroke-width', pct === 50 ? '1.5' : '1');
      if (pct !== 50 && pct !== 100) {
        circle.setAttribute('stroke-dasharray', '3,3');
      }
      g.appendChild(circle);
    });
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
