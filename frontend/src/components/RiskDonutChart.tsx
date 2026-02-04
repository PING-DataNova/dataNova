/**
 * Donut Chart pour la classification des risques
 * Style sombre comme dans la maquette
 */

import React from 'react';

interface RiskDonutChartProps {
  data: {
    label: string;
    value: number;
    color: string;
  }[];
  title?: string;
}

const RiskDonutChart: React.FC<RiskDonutChartProps> = ({ 
  data,
  title = "Portfolio Risk Classifications"
}) => {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  
  // Calculer les angles pour le donut
  let cumulativeAngle = 0;
  const segments = data.map(item => {
    const angle = (item.value / total) * 360;
    const startAngle = cumulativeAngle;
    cumulativeAngle += angle;
    return {
      ...item,
      startAngle,
      endAngle: cumulativeAngle,
      percentage: Math.round((item.value / total) * 100)
    };
  });

  // Fonction pour convertir angle en coordonnées
  const polarToCartesian = (centerX: number, centerY: number, radius: number, angleInDegrees: number) => {
    const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0;
    return {
      x: centerX + (radius * Math.cos(angleInRadians)),
      y: centerY + (radius * Math.sin(angleInRadians))
    };
  };

  // Créer le path d'un arc
  const describeArc = (x: number, y: number, radius: number, startAngle: number, endAngle: number) => {
    const start = polarToCartesian(x, y, radius, endAngle);
    const end = polarToCartesian(x, y, radius, startAngle);
    const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
    return [
      "M", start.x, start.y,
      "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y
    ].join(" ");
  };

  const size = 200;
  const center = size / 2;
  const outerRadius = 80;
  const innerRadius = 50;

  return (
    <div className="bg-slate-900 rounded-2xl p-6 h-full">
      <h3 className="text-white font-bold text-lg mb-4">{title}</h3>
      
      <div className="flex items-center justify-between">
        {/* Légende à gauche */}
        <div className="space-y-3">
          {segments.map((item, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded-sm"
                style={{ backgroundColor: item.color }}
              />
              <div className="flex flex-col">
                <span className="text-white text-xs font-medium">{item.label}</span>
                <span className="text-slate-500 text-[10px]">{item.value} risques</span>
              </div>
            </div>
          ))}
        </div>

        {/* Donut Chart */}
        <div className="relative">
          <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
            {/* Segments du donut */}
            {segments.map((segment, idx) => {
              if (segment.value === 0) return null;
              
              // Pour un segment complet (360°), utiliser un cercle
              if (segment.endAngle - segment.startAngle >= 359.9) {
                return (
                  <circle
                    key={idx}
                    cx={center}
                    cy={center}
                    r={(outerRadius + innerRadius) / 2}
                    fill="none"
                    stroke={segment.color}
                    strokeWidth={outerRadius - innerRadius}
                  />
                );
              }

              // Arc path
              const path = describeArc(center, center, (outerRadius + innerRadius) / 2, segment.startAngle, segment.endAngle);
              
              return (
                <path
                  key={idx}
                  d={path}
                  fill="none"
                  stroke={segment.color}
                  strokeWidth={outerRadius - innerRadius}
                  strokeLinecap="butt"
                  className="transition-all hover:opacity-80"
                />
              );
            })}
            
            {/* Cercle intérieur (trou du donut) */}
            <circle
              cx={center}
              cy={center}
              r={innerRadius - 2}
              fill="#0f172a"
            />
            
            {/* Texte central */}
            <text
              x={center}
              y={center - 8}
              textAnchor="middle"
              className="fill-white font-black text-3xl"
            >
              {total}
            </text>
            <text
              x={center}
              y={center + 12}
              textAnchor="middle"
              className="fill-slate-400 text-xs"
            >
              Total
            </text>
          </svg>
        </div>
      </div>

      {/* Barre de progression en bas */}
      <div className="mt-6 h-2 bg-slate-800 rounded-full overflow-hidden flex">
        {segments.map((segment, idx) => (
          <div
            key={idx}
            style={{ 
              width: `${segment.percentage}%`,
              backgroundColor: segment.color
            }}
            className="h-full transition-all"
            title={`${segment.label}: ${segment.percentage}%`}
          />
        ))}
      </div>
    </div>
  );
};

export default RiskDonutChart;
