import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const TeamStatsBarChart = ({ stats }) => {
  const chartRef = useRef(null);
  
  useEffect(() => {
    if (!stats || !chartRef.current) return;
    
    // Clear previous chart
    d3.select(chartRef.current).selectAll("*").remove();
    
    // Create the bar chart
    createBarChart();
  }, [stats]);
  
  const createBarChart = () => {
    // Stats to display on the bar chart
    const data = [
      { label: "Points", value: stats.points_per_game },
      { label: "Rebounds", value: stats.rebounds_per_game },
      { label: "Assists", value: stats.assists_per_game },
      { label: "Steals", value: stats.steals_per_game },
      { label: "Blocks", value: stats.blocks_per_game },
      { label: "Turnovers", value: stats.turnovers_per_game }
    ];
    
    // Chart dimensions
    const width = 500;
    const height = 300;
    const margin = { top: 20, right: 30, bottom: 40, left: 40 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    // Create SVG
    const svg = d3.select(chartRef.current)
      .append("svg")
      .attr("width", width)
      .attr("height", height)
      .append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);
    
    // Scales
    const xScale = d3.scaleBand()
      .domain(data.map(d => d.label))
      .range([0, innerWidth])
      .padding(0.2);
    
    const yScale = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.value) * 1.2])  // Add 20% padding at the top
      .range([innerHeight, 0]);
    
    // Draw X axis
    svg.append("g")
      .attr("transform", `translate(0, ${innerHeight})`)
      .call(d3.axisBottom(xScale))
      .selectAll("text")
      .style("text-anchor", "middle");
    
    // Draw Y axis
    svg.append("g")
      .call(d3.axisLeft(yScale).ticks(5));
    
    // Add label for Y axis
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -margin.left)
      .attr("x", -innerHeight / 2)
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .style("font-size", "12px")
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
          "#36A2EB", // Blue
          "#4BC0C0", // Teal
          "#9966FF", // Purple
          "#FF9F40", // Orange
          "#FF6384", // Red
          "#FFCD56"  // Yellow
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
      .style("font-size", "12px")
      .style("fill", "#333");
  };
  
  return (
    <div ref={chartRef} style={{ width: '100%', height: '300px' }}>
      {/* D3 will render the chart here */}
    </div>
  );
};

export default TeamStatsBarChart;