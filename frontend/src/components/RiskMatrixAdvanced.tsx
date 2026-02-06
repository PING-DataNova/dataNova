/**
 * Matrice de Risque Avancée - Style Portfolio Risk Matrix
 * 
 * Affiche une matrice visuelle avec zones colorées en dégradé
 * et des points représentant chaque risque positionné selon:
 * - Axe X: Probabilité (0-100%)
 * - Axe Y: Impact/Influence (0-100%)
 */

import React, { useMemo } from 'react';

export interface RiskPoint {
  id: string;
  title: string;
  probability: number;  // 0-100
  impact: number;       // 0-100
  category?: 'Réglementations' | 'Climat' | 'Géopolitique';
}

interface RiskMatrixAdvancedProps {
  items: RiskPoint[];
  onPointClick?: (item: RiskPoint) => void;
  showLegend?: boolean;
  title?: string;
}

const RiskMatrixAdvanced: React.FC<RiskMatrixAdvancedProps> = ({ 
  items, 
  onPointClick,
  showLegend = true,
  title = "Portfolio Risk Matrix"
}) => {
  // Calculer la couleur d'un point basée sur sa position
  const getPointColor = (probability: number, impact: number): string => {
    const score = (probability + impact) / 2;
    if (score < 25) return '#22c55e'; // Vert
    if (score < 50) return '#eab308'; // Jaune
    if (score < 75) return '#f97316'; // Orange
    return '#ef4444'; // Rouge
  };

  // Légende des couleurs
  const legendItems = [
    { label: 'Critical', color: '#ef4444', range: '75-100%' },
    { label: 'High Risk', color: '#f97316', range: '50-75%' },
    { label: 'Medium', color: '#eab308', range: '25-50%' },
    { label: 'Low Risk', color: '#22c55e', range: '0-25%' },
  ];

  // Statistiques
  const stats = useMemo(() => {
    const critical = items.filter(i => (i.probability + i.impact) / 2 >= 75).length;
    const high = items.filter(i => (i.probability + i.impact) / 2 >= 50 && (i.probability + i.impact) / 2 < 75).length;
    const medium = items.filter(i => (i.probability + i.impact) / 2 >= 25 && (i.probability + i.impact) / 2 < 50).length;
    const low = items.filter(i => (i.probability + i.impact) / 2 < 25).length;
    return { critical, high, medium, low, total: items.length };
  }, [items]);

  return (
    <div className="w-full h-full flex flex-col bg-slate-900 rounded-2xl p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-white font-bold text-lg">{title}</h3>
        <div className="flex items-center gap-2">
          <span className="text-slate-400 text-sm">{stats.total} risques</span>
        </div>
      </div>

      <div className="flex flex-1 gap-6">
        {/* Légende à gauche */}
        {showLegend && (
          <div className="flex flex-col gap-2 w-32 shrink-0">
            {legendItems.map((item, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <div className="flex flex-col">
                  <span className="text-white text-xs font-medium">{item.label}</span>
                  <span className="text-slate-500 text-[10px]">{item.range}</span>
                </div>
              </div>
            ))}
            
            {/* Stats */}
            <div className="mt-4 pt-4 border-t border-slate-700">
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-red-400">● Critical</span>
                  <span className="text-white font-bold">{stats.critical}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-orange-400">● High</span>
                  <span className="text-white font-bold">{stats.high}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-yellow-400">● Medium</span>
                  <span className="text-white font-bold">{stats.medium}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-green-400">● Low</span>
                  <span className="text-white font-bold">{stats.low}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Matrice principale */}
        <div className="flex-1 flex flex-col">
          {/* Label Y */}
          <div className="flex items-center mb-2">
            <span className="text-slate-400 text-xs font-medium transform -rotate-0">
              Impact ↑
            </span>
          </div>
          
          <div className="flex-1 flex">
            {/* Axe Y labels */}
            <div className="flex flex-col justify-between pr-2 py-1">
              <span className="text-slate-500 text-[10px]">100%</span>
              <span className="text-slate-500 text-[10px]">75%</span>
              <span className="text-slate-500 text-[10px]">50%</span>
              <span className="text-slate-500 text-[10px]">25%</span>
              <span className="text-slate-500 text-[10px]">0%</span>
            </div>

            {/* Zone de la matrice avec gradient */}
            <div className="flex-1 relative rounded-xl overflow-hidden bg-slate-800">
              {/* Grille neutre - les points seront colorés selon la légende */}
              <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                {/* Grille */}
                <g stroke="rgba(255,255,255,0.15)" strokeWidth="0.3">
                  {/* Lignes horizontales */}
                  <line x1="0" y1="25" x2="100" y2="25" />
                  <line x1="0" y1="50" x2="100" y2="50" />
                  <line x1="0" y1="75" x2="100" y2="75" />
                  {/* Lignes verticales */}
                  <line x1="25" y1="0" x2="25" y2="100" />
                  <line x1="50" y1="0" x2="50" y2="100" />
                  <line x1="75" y1="0" x2="75" y2="100" />
                </g>
              </svg>

              {/* Points des risques */}
              {items.map((item, idx) => {
                const x = `${item.probability}%`;
                const y = `${100 - item.impact}%`; // Inversé car Y va de haut en bas
                const color = getPointColor(item.probability, item.impact);
                
                return (
                  <div
                    key={item.id || idx}
                    className="absolute w-3 h-3 rounded-full cursor-pointer hover:scale-150 transition-transform z-10 ring-2 ring-white/50"
                    style={{
                      left: x,
                      top: y,
                      backgroundColor: '#1e293b',
                      transform: 'translate(-50%, -50%)',
                      boxShadow: `0 0 6px ${color}`
                    }}
                    onClick={() => onPointClick?.(item)}
                    title={`${item.title}\nProbabilité: ${item.probability}%\nImpact: ${item.impact}%`}
                  >
                    <div 
                      className="absolute inset-0.5 rounded-full"
                      style={{ backgroundColor: color }}
                    />
                  </div>
                );
              })}
            </div>
          </div>

          {/* Axe X labels */}
          <div className="flex mt-2 pl-8">
            <div className="flex-1 flex justify-between">
              <span className="text-slate-500 text-[10px]">0%</span>
              <span className="text-slate-500 text-[10px]">25%</span>
              <span className="text-slate-500 text-[10px]">50%</span>
              <span className="text-slate-500 text-[10px]">75%</span>
              <span className="text-slate-500 text-[10px]">100%</span>
            </div>
          </div>
          
          {/* Label X */}
          <div className="text-center mt-1 pl-8">
            <span className="text-slate-400 text-xs font-medium">
              Probabilité →
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskMatrixAdvanced;
