import React, { useState } from 'react';
import { RiskData, ImpactLevel } from '../types';

interface RiskTableProps {
  risks: RiskData[];
  onRiskClick?: (riskId: string) => void;
}

const ImpactBadge: React.FC<{ level: ImpactLevel }> = ({ level }) => {
  const styles = {
    faible: { bg: 'bg-emerald-100', text: 'text-emerald-700', dot: 'bg-emerald-500' },
    moyen: { bg: 'bg-amber-100', text: 'text-amber-700', dot: 'bg-amber-500' },
    eleve: { bg: 'bg-orange-100', text: 'text-orange-700', dot: 'bg-orange-500' },
    critique: { bg: 'bg-red-100', text: 'text-red-700', dot: 'bg-red-500' },
  };

  const style = styles[level] || styles.moyen;
  const labels: Record<string, string> = { faible: 'Faible', moyen: 'Moyen', eleve: 'Eleve', critique: 'Critique' };

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${style.bg} ${style.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`}></span>
      {labels[level] || level}
    </span>
  );
};

// Parse le score depuis le texte
const extractScore = (text: string): number | null => {
  const match = text?.match(/(\d+\.?\d*)\s*\/\s*100/);
  return match ? parseFloat(match[1]) : null;
};

// Parse les entites affectees
const extractEntities = (text: string): { sites: number; suppliers: number } => {
  const sitesMatch = text?.match(/(\d+)\s*site\(s\)/i);
  const suppliersMatch = text?.match(/(\d+)\s*fournisseur\(s\)/i);
  return {
    sites: sitesMatch ? parseInt(sitesMatch[1]) : 0,
    suppliers: suppliersMatch ? parseInt(suppliersMatch[1]) : 0,
  };
};

// Formate la date
const formatDate = (dateStr: string): string => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' });
};

// Tronque le texte
const truncateText = (text: string, maxLength: number): string => {
  if (!text || text.length <= maxLength) return text || '';
  return text.substring(0, maxLength) + '...';
};

// Extrait le titre propre
const extractTitle = (risk: RiskData): string => {
  // Priorite: regulation_title > risk_main (si pas de ===) > premiere ligne de risk_details
  if (risk.regulation_title) {
    return risk.regulation_title;
  }
  if (risk.risk_main && !risk.risk_main.startsWith('===')) {
    return risk.risk_main;
  }
  // Extraire depuis risk_details
  const lines = (risk.risk_details || '').split('\n').filter(l => l.trim());
  for (const line of lines) {
    if (!line.startsWith('===') && !line.startsWith('---') && line.length > 10) {
      return truncateText(line.replace(/^[^:]+:\s*/, ''), 100);
    }
  }
  return 'Analyse de risque reglementaire';
};

// Extrait la synthese du texte
const extractSynthesis = (risk: RiskData): string => {
  const text = risk.risk_details || risk.llm_reasoning || '';
  
  // Chercher section SYNTHESE
  const synthMatch = text.match(/SYNTH[EÈ]SE[:\s]*([^=\n]+(?:\n(?![A-Z]{3,})[^\n=]+)*)/i);
  if (synthMatch) {
    return truncateText(synthMatch[1].trim(), 200);
  }
  
  // Sinon prendre les premieres lignes utiles
  const lines = text.split('\n').filter(l => 
    l.trim() && 
    !l.startsWith('===') && 
    !l.startsWith('---') &&
    l.length > 20
  );
  return truncateText(lines[0] || '', 200);
};

const RiskCard: React.FC<{ 
  risk: RiskData; 
  onViewDetails?: () => void;
}> = ({ risk, onViewDetails }) => {
  const [expanded, setExpanded] = useState(false);
  
  const score = extractScore(risk.risk_details || risk.llm_reasoning);
  const entities = extractEntities(risk.risk_details || risk.llm_reasoning);
  const title = extractTitle(risk);
  const synthesis = extractSynthesis(risk);

  return (
    <div className="bg-white rounded-xl border border-slate-200 hover:border-slate-300 hover:shadow-md transition-all duration-200 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-100">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-slate-900 text-sm leading-tight line-clamp-2">
              {title}
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              {formatDate(risk.created_at)}
            </p>
          </div>
          <ImpactBadge level={risk.impact_level} />
        </div>
      </div>

      {/* Corps */}
      <div className="p-4">
        {/* Score et Entites */}
        <div className="flex items-center gap-4 mb-3">
          {score && (
            <div className="flex items-center gap-2">
              <div className="relative w-10 h-10">
                <svg className="w-10 h-10 transform -rotate-90" viewBox="0 0 36 36">
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#E2E8F0"
                    strokeWidth="3"
                  />
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke={score >= 70 ? '#EF4444' : score >= 40 ? '#F59E0B' : '#10B981'}
                    strokeWidth="3"
                    strokeDasharray={`${score}, 100`}
                    strokeLinecap="round"
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-slate-700">
                  {Math.round(score)}
                </span>
              </div>
              <div className="text-xs">
                <p className="font-medium text-slate-700">Score</p>
                <p className="text-slate-500">/100</p>
              </div>
            </div>
          )}
          
          <div className="flex items-center gap-3 text-xs">
            {entities.sites > 0 && (
              <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-100 rounded-lg">
                <svg className="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                <span className="font-medium text-slate-600">{entities.sites} sites</span>
              </div>
            )}
            {entities.suppliers > 0 && (
              <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-100 rounded-lg">
                <svg className="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                </svg>
                <span className="font-medium text-slate-600">{entities.suppliers} fournisseurs</span>
              </div>
            )}
          </div>
        </div>

        {/* Synthese */}
        <div className="mb-3">
          <p className={`text-xs text-slate-600 leading-relaxed ${expanded ? '' : 'line-clamp-2'}`}>
            {synthesis}
          </p>
          {synthesis.length > 100 && (
            <button 
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-blue-600 hover:text-blue-700 font-medium mt-1"
            >
              {expanded ? 'Voir moins' : 'Voir plus'}
            </button>
          )}
        </div>
      </div>

      {/* Footer Actions */}
      <div className="px-4 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
        <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">
          {risk.category || 'Reglementation'}
        </span>
        <button
          onClick={onViewDetails}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-900 hover:text-white hover:border-slate-900 transition-all"
        >
          Voir details
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
};

const RiskTable: React.FC<RiskTableProps> = ({ risks, onRiskClick }) => {
  if (risks.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
        <svg className="w-12 h-12 mx-auto text-slate-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <h3 className="text-lg font-semibold text-slate-700 mb-1">Aucun risque identifie</h3>
        <p className="text-sm text-slate-500">Les analyses apparaitront ici une fois le pipeline execute.</p>
      </div>
    );
  }

  // Compter par niveau
  const countByLevel = risks.reduce((acc, r) => {
    acc[r.impact_level] = (acc[r.impact_level] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="space-y-4">
      {/* Header avec stats */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-4">
          <p className="text-sm text-slate-600">
            <span className="font-bold text-slate-900 text-lg">{risks.length}</span> risque{risks.length > 1 ? 's' : ''} identifie{risks.length > 1 ? 's' : ''}
          </p>
          <div className="flex items-center gap-2">
            {countByLevel.critique > 0 && (
              <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs font-semibold">
                {countByLevel.critique} critique{countByLevel.critique > 1 ? 's' : ''}
              </span>
            )}
            {countByLevel.eleve > 0 && (
              <span className="px-2 py-0.5 bg-orange-100 text-orange-700 rounded-full text-xs font-semibold">
                {countByLevel.eleve} eleve{countByLevel.eleve > 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-red-500"></span>
            Critique
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-orange-500"></span>
            Eleve
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-amber-500"></span>
            Moyen
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            Faible
          </span>
        </div>
      </div>

      {/* Grid de cartes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {risks.map((risk) => (
          <RiskCard
            key={risk.id}
            risk={risk}
            onViewDetails={() => onRiskClick?.(risk.id)}
          />
        ))}
      </div>
    </div>
  );
};

export default RiskTable;
