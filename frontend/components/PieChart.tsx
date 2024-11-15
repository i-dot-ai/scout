import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface PieChartProps {
  data: number[];
  labels: string[];
}

const PieChart: React.FC<PieChartProps> = ({ data, labels }) => {
  const ref = useRef<SVGSVGElement | null>(null);
  const tooltipRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!ref.current) return;

    const width = 600; // Increase width to accommodate the legend
    const height = 250;
    const radius = Math.min(width, height) / 2 - 50; // Adjust radius to fit the legend

    // Define a color scale that complements light blue and white
    const color = d3.scaleOrdinal<string>()
      .domain(labels)
      .range([
        '#4e79a7', '#f28e2c', '#e15759', '#76b7b2', '#59a14f',
        '#edc949', '#af7aa1', '#ff9da7', '#9c755f', '#bab0ab'
      ]);

    const pie = d3.pie<number>().value(d => d)(data);
    const arc = d3.arc<d3.PieArcDatum<number>>().innerRadius(0).outerRadius(radius);

    const svg = d3.select(ref.current)
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${radius + 70}, ${height / 2})`); // Move chart to the right

    const tooltip = d3.select(tooltipRef.current)
      .style('position', 'absolute')
      .style('background-color', 'white')
      .style('padding', '10px')
      .style('border', '1px solid #ccc')
      .style('border-radius', '5px')
      .style('box-shadow', '0 0 10px rgba(0, 0, 0, 0.1)')
      .style('pointer-events', 'none')
      .style('opacity', 0);

    const onMouseOver = (event: MouseEvent, d: d3.PieArcDatum<number>) => {
      tooltip.transition().duration(200).style('opacity', 1);
      tooltip.html(`${labels[d.index]}: ${d.value}`)
        .style('left', `${event.pageX + 10}px`)
        .style('top', `${event.pageY + 10}px`);
    };

    const onMouseMove = (event: MouseEvent) => {
      tooltip.style('left', `${event.pageX + 10}px`)
        .style('top', `${event.pageY + 10}px`);
    };

    const onMouseOut = () => {
      tooltip.transition().duration(200).style('opacity', 0);
    };

    svg.selectAll('path')
      .data(pie)
      .enter()
      .append('path')
      .attr('d', arc)
      .attr('fill', (d, i) => color(i.toString()) as string)
      .on('mouseover', function(event, d) {
        d3.select(this).transition().duration(200).attr('opacity', 0.7);
        onMouseOver(event as unknown as MouseEvent, d);
      })
      .on('mousemove', function(event, d) {
        onMouseMove(event as unknown as MouseEvent);
      })
      .on('mouseout', function(event, d) {
        d3.select(this).transition().duration(200).attr('opacity', 1);
        onMouseOut();
      });

    // Add legend
    const legend = svg.append('g')
      .attr('transform', `translate(${radius + 50}, -${height / 2 - 20})`); // Adjust legend position

    const legendHeight = labels.length * 20;
    const legendStartY = legendHeight*2;

    labels.forEach((label, i) => {
      const legendRow = legend.append('g')
        .attr('transform', `translate(0, ${legendStartY + i * 20})`); // Centrally align labels

      legendRow.append('rect')
        .attr('width', 10)
        .attr('height', 10)
        .attr('fill', color(i.toString()) as string);

      legendRow.append('text')
        .attr('x', 20)
        .attr('y', 10)
        .attr('text-anchor', 'start')
        .style('text-transform', 'capitalize')
        .text(label);
    });

    return () => {
      d3.select(ref.current).selectAll('*').remove();
      tooltip.remove();
    };
  }, [data, labels]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <svg ref={ref}></svg>
      <div ref={tooltipRef} className="tooltip"></div>
      <p>Breakdown of negative outputs by category</p>
    </div>
  );
};

export default PieChart;
