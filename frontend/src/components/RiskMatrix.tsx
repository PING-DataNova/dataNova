/**
 * Composant Matrice de Risque / Impact
 * 
 * Affiche une matrice 3x3 visuelle montrant la distribution des risques
 * selon leur niveau de risque (probabilité) et leur niveau d'impact (gravité).
 * 
 * Le quadrant critique (risque élevé + impact élevé) est mis en évidence.
 */

import React from 'react';

export interface RiskMatrixItem {
  id: string;
  title: string;
  riskLevel: 'faible' | 'moyen' | 'eleve';  // Probabilité/Niveau de risque
  impactLevel: 'faible' | 'moyen' | 'fort';  // Gravité de l'impact (fort = élevé)
  category?: 'Réglementations' | 'Climat' | 'Géopolitique';  // Catégorie du risque (optionnel)
}

interface RiskMatrixProps {
  items: RiskMatrixItem[];
  onCellClick?: (riskLevel: string, impactLevel: string, items: RiskMatrixItem[]) => void;
}

const RiskMatrix: React.FC<RiskMatrixProps> = ({ items, onCellClick }) => {
  // Niveaux pour les axes (de haut en bas pour le risque, de gauche à droite pour l'impact)
  const riskLevels: Array<'eleve' | 'moyen' | 'faible'> = ['eleve', 'moyen', 'faible'];
  const impactLevels: Array<'faible' | 'moyen' | 'fort'> = ['faible', 'moyen', 'fort'];

  // Labels d'affichage - mêmes termes pour risque et impact
  const levelLabels: Record<string, string> = {
    eleve: 'Élevé',
    fort: 'Élevé',  // fort = élevé pour l'impact
    moyen: 'Moyen',
    faible: 'Faible'
  };

  // Couleurs de fond selon la criticité avec dégradé subtil
  // Simplifié à 3 niveaux pour cohérence avec la légende
  const getCellStyle = (risk: string, impact: string): { bg: string; text: string; shadow: string } => {
    // Calculer un score de criticité (0-4)
    const riskScore = risk === 'eleve' ? 2 : risk === 'moyen' ? 1 : 0;
    const impactScore = impact === 'fort' ? 2 : impact === 'moyen' ? 1 : 0;
    const totalScore = riskScore + impactScore; // 0 à 4

    // 3 niveaux: Faible (0-1), Modéré (2), Élevé (3-4)
    if (totalScore <= 1) {
      // Faible - Vert
      return { bg: 'bg-gradient-to-br from-emerald-400 to-emerald-500', text: 'text-white', shadow: 'shadow-emerald-200' };
    } else if (totalScore === 2) {
      // Modéré - Jaune
      return { bg: 'bg-gradient-to-br from-amber-300 to-amber-400', text: 'text-amber-900', shadow: 'shadow-amber-200' };
    } else {
      // Élevé - Orange/Rouge
      return { bg: 'bg-gradient-to-br from-orange-500 to-red-500', text: 'text-white', shadow: 'shadow-orange-200' };
    }
  };

  // Compter les items dans chaque cellule
  const getItemsInCell = (risk: string, impact: string): RiskMatrixItem[] => {
    return items.filter(item => item.riskLevel === risk && item.impactLevel === impact);
  };

  // Vérifier si c'est la zone critique
  const isCriticalZone = (risk: string, impact: string): boolean => {
    return risk === 'eleve' && impact === 'fort';
  };

  return (
    <div className="w-full h-full flex flex-col">
      {/* Container principal */}
      <div className="flex-grow flex bg-gradient-to-br from-slate-50 to-slate-100 rounded-2xl p-4 shadow-inner">
        
        {/* Axe Y - Label Risque */}
        <div className="flex items-center pr-2">
          <div className="transform -rotate-90 whitespace-nowrap text-[9px] font-black uppercase tracking-[0.15em] text-slate-400">
            Risque ↑
          </div>
        </div>

        {/* Contenu principal avec grid */}
        <div className="flex-grow flex flex-col">
          {/* Grille avec labels Y intégrés */}
          <div className="flex-grow grid grid-rows-3 gap-2">
            {riskLevels.map(risk => (
              <div key={risk} className="flex items-center gap-2">
                {/* Label Y pour cette rangée */}
                <div className="w-12 text-right shrink-0">
                  <span className="text-[11px] font-semibold text-slate-500">
                    {levelLabels[risk]}
                  </span>
                </div>
                {/* Cellules de cette rangée */}
                <div className="flex-grow grid grid-cols-3 gap-2">
                  {impactLevels.map(impact => {
                    const cellItems = getItemsInCell(risk, impact);
                    const count = cellItems.length;
                    const isCritical = isCriticalZone(risk, impact);
                  const style = getCellStyle(risk, impact);

                  return (
                    <div
                      key={`${risk}-${impact}`}
                      onClick={() => count > 0 && onCellClick?.(risk, impact, cellItems)}
                      className={`
                        ${style.bg}
                        rounded-xl flex items-center justify-center
                        transition-all duration-300
                        ${count > 0 ? 'cursor-pointer hover:scale-110 hover:shadow-xl hover:z-10' : 'opacity-50 cursor-default'}
                        ${isCritical && count > 0 ? `ring-2 ring-red-500 ring-offset-2 shadow-lg ${style.shadow}` : ''}
                        relative overflow-hidden
                      `}
                    >
                      {/* Effet brillance */}
                      <div className="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent opacity-60 pointer-events-none" />
                      
                      {/* Compteur avec style amélioré */}
                      <div className={`
                        relative z-10 font-black text-xl
                        ${style.text}
                        ${count === 0 ? 'opacity-30 text-base' : ''}
                        drop-shadow-sm
                      `}>
                        {count > 0 ? count : '·'}
                      </div>
                      
                      {/* Indicateur zone critique animé */}
                      {isCritical && count > 0 && (
                        <>
                          <div className="absolute top-1 right-1 w-2 h-2 bg-white rounded-full animate-ping" />
                          <div className="absolute top-1 right-1 w-2 h-2 bg-white rounded-full" />
                        </>
                      )}
                    </div>
                  );
                })}
                </div>
              </div>
            ))}
          </div>

          {/* Axe X - Labels des impacts (avec offset pour aligner avec les cellules) */}
          <div className="flex items-center gap-2 mt-2">
            <div className="w-12 shrink-0"></div>
            <div className="flex-grow grid grid-cols-3 gap-1.5">
              {impactLevels.map(level => (
                <div key={level} className="flex justify-center">
                  <span className="text-[10px] font-semibold text-slate-500">
                    {levelLabels[level]}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Axe X - Label Impact */}
          <div className="flex items-center gap-2 mt-1">
            <div className="w-12 shrink-0"></div>
            <div className="flex-grow text-center">
              <span className="text-[8px] font-black uppercase tracking-[0.2em] text-slate-400">
                Impact →
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskMatrix;
