import React, { useCallback, useEffect, useRef } from 'react';
import * as d3 from 'd3';
import theme from '../theme';

// Props:
// stats: Raw team statistics object
const TeamStatsBarChart = ({ stats }) => {
  const chartRef = useRef(null);

  const createBarChart = useCallback(() => {
    // Define key stats to visualize with their display names and keys
    const statDefinitions = [
      { key: 'points_per_game', label: 'Points' },
      { key: 'rebounds_per_game', label: 'Rebounds' },
      { key: 'assists_per_game', label: 'Assists' },
      { key: 'steals_per_game', label: 'Steals' },
      { key: 'blocks_per_game', label: 'Blocks' },
      { key: 'turnovers_per_game', label: 'Turnovers' }
    ];
    
    // Create data array using raw stats only
    const data = statDefinitions.map(def => ({
      label: def.label,
      key: def.key,
      value: stats[def.key],
    }));
    
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
  .text('Team Statistics');
    
    // Scales
    const xScale = d3.scaleBand()
      .domain(data.map(d => d.label))
      .range([0, innerWidth])
      .padding(0.2);
    
    const yScale = d3.scaleLinear()
  .domain([0, d3.max(data, d => d.value) * 1.2])
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
  .text("Per Game");
    
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
          const colors = [
            theme.colors.visualization.primary,
            theme.colors.visualization.secondary,
            theme.colors.visualization.tertiary,
            theme.colors.visualization.quaternary,
            theme.colors.visualization.quintary,
            theme.colors.ui.accent,
          ];
          return colors[i % colors.length];
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
      .text(d => d.value.toFixed(1))
      .style("font-family", theme.typography.fontFamily.secondary)
      .style("font-size", "11px")
      .style("font-weight", theme.typography.fontWeight.medium)
      .style("fill", theme.colors.text.primary);
    
  }, [stats]);

  useEffect(() => {
    if (!stats || !chartRef.current) return;

    // Clear previous chart
    d3.select(chartRef.current).selectAll("*").remove();

    // Create the bar chart
    createBarChart();

  }, [stats, createBarChart]);
  
  return (
    <div ref={chartRef} style={{ width: '100%', height: '300px', position: 'relative' }}>
      {/* D3 will render the chart here */}
    </div>
  );
};

// Export the component
export default TeamStatsBarChart;