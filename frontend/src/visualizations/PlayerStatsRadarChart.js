import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const PlayerStatsRadarChart = ({ stats }) => {
  const chartRef = useRef(null);
  
  useEffect(() => {
    if (!stats || !chartRef.current) return;
    
    // Clear previous chart
    d3.select(chartRef.current).selectAll("*").remove();
    
    // Create the radar chart
    createRadarChart();
  }, [stats]);
  
  const createRadarChart = () => {
    // Stats to display on the radar chart
    const features = [
      { name: "Points", value: stats.points_per_game, key: "points_per_game", max: 30 },
      { name: "Rebounds", value: stats.rebounds_per_game, key: "rebounds_per_game", max: 15 },
      { name: "Assists", value: stats.assists_per_game, key: "assists_per_game", max: 12 },
      { name: "Steals", value: stats.steals_per_game, key: "steals_per_game", max: 4 },
      { name: "Blocks", value: stats.blocks_per_game, key: "blocks_per_game", max: 4 },
      { name: "Efficiency", value: stats.field_goal_percentage * 100, key: "field_goal_percentage", max: 100 }
    ];
    
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
    
    // Scales
    const angleScale = d3.scaleLinear()
      .domain([0, features.length])
      .range([0, 2 * Math.PI]);
    
    const radiusScale = d3.scaleLinear()
      .domain([0, 100])
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
      .attr("stroke", "#e5e5e5")
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
        .attr("stroke", "#e5e5e5")
        .attr("stroke-width", 1);
      
      // Add labels
      svg.append("text")
        .attr("x", 1.1 * x)
        .attr("y", 1.1 * y)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "middle")
        .text(feature.name)
        .style("font-size", "12px")
        .style("fill", "#666");
    });
    
    // Draw the data points
    const points = features.map((feature, i) => {
      const angle = angleScale(i);
      // Normalize the value as a percentage of max
      const normalizedValue = (feature.value / feature.max) * 100;
      const r = radiusScale(normalizedValue);
      return {
        x: r * Math.sin(angle),
        y: -r * Math.cos(angle),
        value: feature.value
      };
    });
    
    // Create the polygon
    const lineGenerator = d3.lineRadial()
      .angle((d, i) => angleScale(i))
      .radius((d) => radiusScale((d.value / d.max) * 100));
    
    const radialData = features.map(d => ({
      value: d.value,
      max: d.max
    }));
    
    // Draw the radar chart
    svg.append("path")
      .datum(radialData)
      .attr("d", lineGenerator)
      .attr("fill", "rgba(53, 162, 235, 0.2)")
      .attr("stroke", "rgba(53, 162, 235, 1)")
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
      .attr("fill", "rgba(53, 162, 235, 1)");
    
    // Add value labels
    svg.selectAll(".value-label")
      .data(points)
      .enter()
      .append("text")
      .attr("class", "value-label")
      .attr("x", d => d.x)
      .attr("y", d => d.y - 10)
      .attr("text-anchor", "middle")
      .text(d => d.value.toFixed(1))
      .style("font-size", "10px")
      .style("fill", "#333");
  };
  
  return (
    <div ref={chartRef} style={{ width: '100%', height: '400px' }}>
      {/* D3 will render the chart here */}
    </div>
  );
};

export default PlayerStatsRadarChart;