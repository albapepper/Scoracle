import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import theme from '../theme';

// Prop types:
// stats: Raw player statistics object
// percentiles: (Optional) Player percentile rankings object
// showPercentiles: Boolean to toggle between raw stats and percentiles
const PlayerStatsRadarChart = ({ stats, percentiles, showPercentiles = false }) => {
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
    
    // Create the radar chart
    createRadarChart();
    
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
  
  const createRadarChart = () => {
    // Define key stats to visualize with their display names
    const statDefinitions = [
      { key: 'points_per_game', name: 'Points', max: 30 },
      { key: 'rebounds_per_game', name: 'Rebounds', max: 15 },
      { key: 'assists_per_game', name: 'Assists', max: 12 },
      { key: 'steals_per_game', name: 'Steals', max: 4 },
      { key: 'blocks_per_game', name: 'Blocks', max: 4 },
      { key: 'field_goal_percentage', name: 'FG%', max: 1, format: value => `${(value * 100).toFixed(1)}%` }
    ];
    
    // Create features array based on chart mode
    const features = statDefinitions.map(def => {
      if (chartMode === 'percentiles' && percentiles && percentiles[def.key] !== undefined) {
        // For percentile mode, we use percentile values (always 0-100)
        return {
          name: def.name,
          key: def.key,
          value: percentiles[def.key],
          rawValue: stats[def.key],
          max: 100,
          isPercentile: true,
          format: value => `${value.toFixed(1)}%`
        };
      } else {
        // For raw stats mode
        return {
          name: def.name,
          key: def.key,
          value: stats[def.key],
          max: def.max,
          isPercentile: false,
          format: def.format || (value => value.toFixed(1))
        };
      }
    });
    
    // Chart dimensions
    const width = 400;
    const height = 400;
    const margin = { top: 50, right: 50, bottom: 50, left: 50 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    const radius = Math.min(innerWidth, innerHeight) / 2;
    
    // Create SVG
    const svg = d3.select(chartRef.current)
      .append("svg")
      .attr("width", width)
      .attr("height", height)
      .append("g")
      .attr("transform", `translate(${width/2}, ${height/2})`);
    
    // Add title
    svg.append("text")
      .attr("x", 0)
      .attr("y", -radius - 10)
      .attr("text-anchor", "middle")
      .style("font-family", theme.typography.fontFamily.primary)
      .style("font-size", "16px")
      .style("font-weight", theme.typography.fontWeight.semibold)
      .style("fill", theme.colors.text.accent)
      .text(chartMode === 'percentiles' ? 'Percentile Rankings' : 'Player Statistics');
    
    // Scales
    const angleScale = d3.scaleLinear()
      .domain([0, features.length])
      .range([0, 2 * Math.PI]);
    
    const radiusScale = d3.scaleLinear()
      .domain([0, chartMode === 'percentiles' ? 100 : 100]) // Percentiles are always 0-100
      .range([0, radius]);
    
    // Draw the background circles
    const circles = [20, 40, 60, 80, 100];
    
    svg.selectAll(".circle")
      .data(circles)
      .enter()
      .append("circle")
      .attr("class", "circle")
      .attr("r", d => radiusScale(d))
      .attr("fill", "none")
      .attr("stroke", theme.colors.ui.border)
      .attr("stroke-width", 1);
    
    // Draw the spokes
    features.forEach((feature, i) => {
      const angle = angleScale(i);
      const x = radius * Math.sin(angle);
      const y = -radius * Math.cos(angle);
      
      svg.append("line")
        .attr("x1", 0)
        .attr("y1", 0)
        .attr("x2", x)
        .attr("y2", y)
        .attr("stroke", theme.colors.ui.border)
        .attr("stroke-width", 1);
      
      // Add labels for the spokes
      svg.append("text")
        .attr("x", 1.1 * x)
        .attr("y", 1.1 * y)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "middle")
        .text(feature.name)
        .style("font-family", theme.typography.fontFamily.secondary)
        .style("font-size", "12px")
        .style("fill", theme.colors.text.secondary);
      
      // Add circle labels (20%, 40%, etc) at the first spoke
      if (i === 0) {
        circles.forEach(value => {
          const labelRadius = radiusScale(value);
          svg.append("text")
            .attr("x", 0)
            .attr("y", -labelRadius - 5)
            .attr("text-anchor", "middle")
            .attr("dominant-baseline", "middle")
            .text(chartMode === 'percentiles' ? `${value}%` : `${value}%`)
            .style("font-size", "8px")
            .style("fill", theme.colors.text.muted);
        });
      }
    });
    
    // Calculate points for the radar shape
    const points = features.map((feature, i) => {
      const angle = angleScale(i);
      
      // For raw stats, normalize as percentage of max
      // For percentiles, the value is already 0-100
      const normalizedValue = feature.isPercentile 
        ? feature.value 
        : (feature.value / feature.max) * 100;
      
      const r = radiusScale(normalizedValue);
      
      return {
        x: r * Math.sin(angle),
        y: -r * Math.cos(angle),
        value: feature.value,
        rawValue: feature.rawValue,
        normalizedValue,
        isPercentile: feature.isPercentile,
        format: feature.format
      };
    });
    
    // Create the radar shape
    const lineGenerator = d3.lineRadial()
      .angle((d, i) => angleScale(i))
      .radius(d => {
        const normalizedValue = d.isPercentile 
          ? d.value 
          : (d.value / d.max) * 100;
        return radiusScale(normalizedValue);
      })
      .curve(d3.curveLinearClosed);
    
    // Determine fill color based on mode
    const fillColor = chartMode === 'percentiles' 
      ? "rgba(84, 106, 123, 0.2)" // Muted blue-slate from theme
      : "rgba(53, 162, 235, 0.2)";
      
    const strokeColor = chartMode === 'percentiles' 
      ? "rgba(84, 106, 123, 0.7)" 
      : "rgba(53, 162, 235, 0.7)";
    
    // Draw the radar chart
    svg.append("path")
      .datum(features)
      .attr("d", lineGenerator)
      .attr("fill", fillColor)
      .attr("stroke", strokeColor)
      .attr("stroke-width", 2);
    
    // Add dots at each data point
    svg.selectAll(".dot")
      .data(points)
      .enter()
      .append("circle")
      .attr("class", "dot")
      .attr("cx", d => d.x)
      .attr("cy", d => d.y)
      .attr("r", 4)
      .attr("fill", d => {
        // For percentile mode, use color scale based on percentile value
        if (d.isPercentile) {
          return getPercentileColor(d.value);
        }
        // For raw stats mode, use consistent color
        return theme.colors.visualization.primary;
      });
    
    // Add value labels
    svg.selectAll(".value-label")
      .data(points)
      .enter()
      .append("text")
      .attr("class", "value-label")
      .attr("x", d => d.x)
      .attr("y", d => d.y - 10)
      .attr("text-anchor", "middle")
      .text(d => {
        // Format the value appropriately
        return d.format(d.value);
      })
      .style("font-size", "10px")
      .style("font-family", theme.typography.fontFamily.secondary)
      .style("fill", theme.colors.text.primary);
    
    // Add legend if in percentile mode
    if (chartMode === 'percentiles') {
      const legendItems = [
        { label: "Elite (80-100%)", color: theme.colors.visualization.percentiles[4] },
        { label: "Above Avg (60-80%)", color: theme.colors.visualization.percentiles[3] },
        { label: "Average (40-60%)", color: theme.colors.visualization.percentiles[2] },
        { label: "Below Avg (20-40%)", color: theme.colors.visualization.percentiles[1] },
        { label: "Low (0-20%)", color: theme.colors.visualization.percentiles[0] }
      ];
      
      const legend = svg.append("g")
        .attr("transform", `translate(${-radius}, ${radius/2})`);
      
      legendItems.forEach((item, i) => {
        const g = legend.append("g")
          .attr("transform", `translate(0, ${i * 20})`);
        
        g.append("rect")
          .attr("width", 12)
          .attr("height", 12)
          .attr("fill", item.color);
        
        g.append("text")
          .attr("x", 20)
          .attr("y", 10)
          .attr("font-size", "10px")
          .attr("font-family", theme.typography.fontFamily.secondary)
          .attr("fill", theme.colors.text.secondary)
          .text(item.label);
      });
    }
  };
  
  return (
    <div ref={chartRef} style={{ width: '100%', height: '400px', position: 'relative' }}>
      {/* D3 will render the chart here */}
    </div>
  );
};

export default PlayerStatsRadarChart;