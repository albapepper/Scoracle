import React, { useCallback, useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import theme from '../theme';

// Props:
// stats: object of numeric metrics
// percentiles: object of percentiles by same keys (0-100)
// keys: optional array of keys to plot; if not provided, auto-pick top N by absolute value
// title: optional title
// maxBars: limit number of bars when auto-picking keys
const GenericStatsBarChart = ({ stats, percentiles = null, keys = null, title = 'Statistics', maxBars = 10 }) => {
  const chartRef = useRef(null);
  const [chartMode, setChartMode] = useState(percentiles ? 'percentiles' : 'raw');

  const getPercentileColor = useCallback((p) => {
    const c = theme.colors.visualization.percentiles;
    if (p >= 80) return c[4];
    if (p >= 60) return c[3];
    if (p >= 40) return c[2];
    if (p >= 20) return c[1];
    return c[0];
  }, []);

  const addToggleButton = useCallback(() => {
    const container = d3.select(chartRef.current);
    container.selectAll('.chart-toggle-button').remove();
    if (!percentiles) return; // no toggle if no percentiles
    container.append('button')
      .attr('class', 'chart-toggle-button')
      .style('position', 'absolute')
      .style('top', '10px')
      .style('right', '10px')
      .style('padding', '6px 12px')
      .style('background-color', theme.colors.ui.primary)
      .style('color', 'white')
      .style('border', 'none')
      .style('border-radius', '4px')
      .style('cursor', 'pointer')
      .text(chartMode === 'raw' ? 'Show Percentiles' : 'Show Raw Stats')
      .on('click', () => setChartMode((m) => (m === 'raw' ? 'percentiles' : 'raw')));
  }, [chartMode, percentiles]);

  const pickKeys = useCallback(() => {
    if (Array.isArray(keys) && keys.length) return keys;
    if (!stats) return [];
    // auto-pick top N numeric keys by magnitude
    const entries = Object.entries(stats).filter(([k, v]) => typeof v === 'number' && isFinite(v));
    // Sort by absolute value descending
    entries.sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
    return entries.slice(0, maxBars).map(([k]) => k);
  }, [keys, stats, maxBars]);

  const draw = useCallback(() => {
    const selectedKeys = pickKeys();
    const data = selectedKeys.map((k) => ({
      key: k,
      label: k.replace(/_/g, ' '),
      value: chartMode === 'percentiles' && percentiles && typeof percentiles[k] === 'number' ? percentiles[k] : stats[k],
      rawValue: stats[k],
      isPercentile: chartMode === 'percentiles' && percentiles && typeof percentiles[k] === 'number'
    }));

    const width = 640;
    const height = 360;
    const margin = { top: 36, right: 24, bottom: 60, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const root = d3.select(chartRef.current);
    const svg = root.append('svg').attr('width', width).attr('height', height);
    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    // Title
    g.append('text')
      .attr('x', innerWidth / 2)
      .attr('y', -12)
      .attr('text-anchor', 'middle')
      .style('font-family', theme.typography.fontFamily.primary)
      .style('font-size', '16px')
      .style('font-weight', theme.typography.fontWeight.semibold)
      .style('fill', theme.colors.text.accent)
      .text(chartMode === 'percentiles' ? `${title} (Percentiles)` : title);

    const x = d3.scaleBand().domain(data.map((d) => d.label)).range([0, innerWidth]).padding(0.2);
    const yMax = chartMode === 'percentiles' ? 100 : d3.max(data, (d) => d.value) || 1;
    const y = d3.scaleLinear().domain([0, yMax * 1.1]).nice().range([innerHeight, 0]);

    g.append('g').attr('transform', `translate(0,${innerHeight})`).call(d3.axisBottom(x)).selectAll('text')
      .style('font-family', theme.typography.fontFamily.secondary)
      .style('font-size', '10px')
      .attr('transform', 'rotate(-25)')
      .style('text-anchor', 'end');

    g.append('g').call(d3.axisLeft(y).ticks(5)).selectAll('text')
      .style('font-family', theme.typography.fontFamily.secondary)
      .style('font-size', '10px');

    g.selectAll('.bar')
      .data(data)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', (d) => x(d.label))
      .attr('y', (d) => y(d.value))
      .attr('width', x.bandwidth())
      .attr('height', (d) => innerHeight - y(d.value))
      .attr('fill', (d, i) => chartMode === 'percentiles' ? getPercentileColor(d.value) : theme.colors.visualization.palette?.[i % (theme.colors.visualization.palette?.length || 5)] || theme.colors.visualization.primary)
      .attr('rx', 4).attr('ry', 4);

    g.selectAll('.label')
      .data(data)
      .enter()
      .append('text')
      .attr('class', 'label')
      .attr('x', (d) => x(d.label) + x.bandwidth() / 2)
      .attr('y', (d) => y(d.value) - 6)
      .attr('text-anchor', 'middle')
      .style('font-family', theme.typography.fontFamily.secondary)
      .style('font-size', '10px')
      .style('fill', theme.colors.text.primary)
      .text((d) => d.isPercentile ? `${d.value.toFixed(0)}%` : (typeof d.value === 'number' ? d.value.toFixed(2) : String(d.value)));

    if (chartMode === 'percentiles') {
      g.selectAll('.raw')
        .data(data)
        .enter()
        .append('text')
        .attr('class', 'raw')
        .attr('x', (d) => x(d.label) + x.bandwidth() / 2)
        .attr('y', (d) => y(d.value) + 14)
        .attr('text-anchor', 'middle')
        .style('font-family', theme.typography.fontFamily.secondary)
        .style('font-size', '9px')
        .style('fill', theme.colors.text.secondary)
        .text((d) => `(${typeof d.rawValue === 'number' ? d.rawValue.toFixed(2) : '-'})`);
    }
  }, [chartMode, stats, percentiles, pickKeys, getPercentileColor, title]);

  useEffect(() => {
    if (!stats || !chartRef.current) return;
    d3.select(chartRef.current).selectAll('*').remove();
    draw();
    addToggleButton();
  }, [stats, percentiles, draw, addToggleButton]);

  return (
    <div ref={chartRef} style={{ width: '100%', height: 360, position: 'relative' }} />
  );
};

export default GenericStatsBarChart;
