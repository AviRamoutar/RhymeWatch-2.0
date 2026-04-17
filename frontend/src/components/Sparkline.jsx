import React from "react";

export default function Sparkline({ values, width = 96, height = 28, up = true }) {
  if (!values || values.length < 2) {
    return <svg width={width} height={height} aria-hidden="true" />;
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const stepX = width / (values.length - 1);
  const points = values
    .map((v, i) => `${(i * stepX).toFixed(2)},${(height - ((v - min) / range) * height).toFixed(2)}`)
    .join(" ");
  const color = up ? "#f59e0b" : "#78716c";
  return (
    <svg width={width} height={height} aria-hidden="true" className="block">
      <polyline points={points} fill="none" stroke={color} strokeWidth="1" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}
