import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import theme from '../theme';

// Props:
// stats: Raw team statistics object
// percentiles: (Optional) Team percentile rankings object
// showPercentiles: Boolean to toggle between raw stats and percentiles
const TeamStatsBarChart = ({ stats, percentiles, showPercentiles = false }) => {
  const chartRef = useRef(null);
  const [chartMode, setChartMode] = useState(showPercentiles ? 'percentiles' : 'raw');
  
  // Toggle between raw stats and percentiles
  const toggleChartMode = () => {
    setChartMode(prev => prev === 'raw' ? 'percentiles' : 'raw');
  };
  
  useEffect(() => {
    if (!stats || !chartRef.current) return;
    
    // Clear previous chart
    d3.select(chartRef.current).selectAll("*").remove();
    
    // Create the bar chart
    createBarChart();
    
    // Add toggle button if percentiles are available
    if (percentiles && Object.keys(percentiles).length > 0) {
      addToggleButton();
    }
  }, [stats, percentiles, chartMode]);
  
  const getPercentileColor = (percentile) => {
    // Use the theme's percentile color scale
    const percentileColors = theme.colors.visualization.percentiles;
    
    if (percentile >= 80) return percentileColors[4]; // Elite (80-100%)
    if (percentile >= 60) return percentileColors[3]; // Above average (60-80%)
    if (percentile >= 40) return percentileColors[2]; // Average (40-60%)
    if (percentile >= 20) return percentileColors[1]; // Below average (20-40%)
    return percentileColors[0]; // Very low (0-20%)
  };
  
  const addToggleButton = () => {
    const container = d3.select(chartRef.current);
    
    // Remove existing button if any
    container.selectAll('.chart-toggle-button').remove();
    
    // Add toggle button
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
      .on('click', toggleChartMode);
  };
  
  const createBarChart = () => {
    // Define key stats to visualize with their display names and keys
    const statDefinitions = [
      { key: 'points_per_game', label: 'Points' },
      { key: 'rebounds_per_game', label: 'Rebounds' },
      { key: 'assists_per_game', label: 'Assists' },
      { key: 'steals_per_game', label: 'Steals' },
      { key: 'blocks_per_game', label: 'Blocks' },
      { key: 'turnovers_per_game', label: 'Turnovers' }
    ];
    
    // Create data array based on chart mode
    const data = statDefinitions.map(def => {
      if (chartMode === 'percentiles' && percentiles && percentiles[def.key] !== undefined) {
        // For percentile mode
        return {
          label: def.label,
          key: def.key,
          value: percentiles[def.key],
          rawValue: stats[def.key],
          isPercentile: true
        };
      } else {
        // For raw stats mode
        return {
          label: def.label,
          key: def.key,
          value: stats[def.key],
          isPercentile: false
        };
      }
    });
    
    // Chart dimensions
    const width = 500;
    const height = 300;
    const margin = { top: 30, right: 30, bottom: 40, left: 50 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    // Create SVG
    const svg = d3.select(chartRef.current)
      .append("svg")
      .attr("width", width)
      .attr("height", height)
      .append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);
    
    // Add title
    svg.append("text")
      .attr("x", innerWidth / 2)
      .attr("y", -margin.top / 2)
      .attr("text-anchor", "middle")
      .style("font-family", theme.typography.fontFamily.primary)
      .style("font-size", "16px")
      .style("font-weight", theme.typography.fontWeight.semibold)
      .style("fill", theme.colors.text.accent)
      .text(chartMode === 'percentiles' ? 'Percentile Rankings' : 'Team Statistics');
    
    // Scales
    const xScale = d3.scaleBand()
      .domain(data.map(d => d.label))
      .range([0, innerWidth])
      .padding(0.2);
    
    const yScale = d3.scaleLinear()
      .domain([0, chartMode === 'percentiles' ? 100 : d3.max(data, d => d.value) * 1.2])
      .range([innerHeight, 0]);
    
    // Draw X axis
    svg.append("g")
      .attr("transform", `translate(0, ${innerHeight})`)
      .call(d3.axisBottom(xScale))
      .selectAll("text")
      .style("text-anchor", "middle")
      .style("font-family", theme.typography.fontFamily.secondary)
      .style("font-size", "10px");
    
    // Draw Y axis
    svg.append("g")
      .call(d3.axisLeft(yScale).ticks(5))
      .selectAll("text")
      .style("font-family", theme.typography.fontFamily.secondary)
      .style("font-size", "10px");
    
    // Add label for Y axis
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -margin.left + 15)
      .attr("x", -innerHeight / 2)
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .style("font-family", theme.typography.fontFamily.secondary)
      .style("font-size", "12px")
      .style("fill", theme.colors.text.secondary)
      .text(chartMode === 'percentiles' ? "Percentile Rank" : "Per Game");
    
    // Draw bars
    svg.selectAll(".bar")
      .data(data)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("x", d => xScale(d.label))
      .attr("width", xScale.bandwidth())
      .attr("y", d => yScale(d.value))
      .attr("height", d => innerHeight - yScale(d.value))
      .attr("fill", (d, i) => {
        // Use the theme colors for consistency
        if (chartMode === 'percentiles') {
          return getPercentileColor(d.value);
        } else {
          const colors = [
            theme.colors.visualization.primary,
            theme.colors.visualization.secondary,
            theme.colors.visualization.tertiary,
            theme.colors.visualization.quaternary,
            theme.colors.visualization.quintary,
            theme.colors.ui.accent,
          ];
          return colors[i % colors.length];
        }
      })
      .attr("rx", 4)  // Rounded corners
      .attr("ry", 4);
    
    // Add value labels on top of each bar
    svg.selectAll(".label")
      .data(data)
      .enter()
      .append("text")
      .attr("class", "label")
      .attr("x", d => xScale(d.label) + xScale.bandwidth() / 2)
      .attr("y", d => yScale(d.value) - 5)
      .attr("text-anchor", "middle")
      .text(d => {
        if (d.isPercentile) {
          return `${d.value.toFixed(0)}%`;
        } else {
          return d.value.toFixed(1);
        }
      })
      .style("font-family", theme.typography.fontFamily.secondary)
      .style("font-size", "11px")
      .style("font-weight", theme.typography.fontWeight.medium)
      .style("fill", theme.colors.text.primary);
    
    // Add raw value as smaller text below percentile
    if (chartMode === 'percentiles') {
      svg.selectAll(".raw-value")
        .data(data)
        .enter()
        .append("text")
        .attr("class", "raw-value")
        .attr("x", d => xScale(d.label) + xScale.bandwidth() / 2)
        .attr("y", d => yScale(d.value) + 15) // Position below the bar
        .attr("text-anchor", "middle")
        .text(d => `(${d.rawValue.toFixed(1)})`)
        .style("font-family", theme.typography.fontFamily.secondary)
        .style("font-size", "9px")
        .style("fill", theme.colors.text.secondary);
    }
    
    // Add legend if in percentile mode
    if (chartMode === 'percentiles') {
      const legendItems = [
        { label: "Elite (80-100%)", color: theme.colors.visualization.percentiles[4] },
        { label: "Above Avg (60-80%)", color: theme.colors.visualization.percentiles[3] },
        { label: "Average (40-60%)", color: theme.colors.visualization.percentiles[2] },
        { label: "Below Avg (20-40%)", color: theme.colors.visualization.percentiles[1] },
        { label: "Low (0-20%)", color: theme.colors.visualization.percentiles[0] }
      ];
      
      const legendX = innerWidth - 150;
      const legendY = 0;
      
      const legend = svg.append("g")
        .attr("transform", `translate(${legendX}, ${legendY})`);
      
      legendItems.forEach((item, i) => {
        const g = legend.append("g")
          .attr("transform", `translate(0, ${i * 15})`);
        
        g.append("rect")
          .attr("width", 10)
          .attr("height", 10)
          .attr("fill", item.color);
        
        g.append("text")
          .attr("x", 15)
          .attr("y", 8)
          .attr("font-size", "9px")
          .attr("font-family", theme.typography.fontFamily.secondary)
          .attr("fill", theme.colors.text.secondary)
          .text(item.label);
      });
    }
  };
  
  return (
    <div ref={chartRef} style={{ width: '100%', height: '300px', position: 'relative' }}>
      {/* D3 will render the chart here */}
    </div>
  );
};

// Export the component
export default TeamStatsBarChart;