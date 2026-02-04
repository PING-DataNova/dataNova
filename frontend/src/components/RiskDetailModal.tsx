import React from 'react';
import { RiskDetailResponse, AffectedEntity } from '../services/impactsService';

interface RiskDetailModalProps {
  risk: RiskDetailResponse | null;
  isLoading: boolean;
  onClose: () => void;
}

const RiskDetailModal: React.FC<RiskDetailModalProps> = ({ risk, isLoading, onClose }) => {
  if (!risk && !isLoading) return null;

  const getRiskLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'critique':
        return 'bg-red-500 text-white';
      case 'eleve':
      case 'élevé':
      case 'fort':
        return 'bg-orange-500 text-white';
      case 'moyen':
        return 'bg-yellow-500 text-white';
      default:
        return 'bg-green-500 text-white';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-red-600';
    if (score >= 50) return 'text-orange-600';
    if (score >= 25) return 'text-yellow-600';
    return 'text-green-600';
  };

  const formatRecommendations = (recommendations: string) => {
    return recommendations.split('\n').filter(line => line.trim()).map((line, index) => (
      <li key={index} className="flex items-start gap-2 mb-2">
        <span className="text-blue-500 mt-1">•</span>
        <span>{line.replace(/^-\s*/, '')}</span>
      </li>
    ));
  };

  // Fonction pour extraire les informations clés du reasoning
  const extractKeyInfo = (reasoning: string) => {
    const lines = reasoning.split('\n').filter(l => l.trim());
    const keyInfo: { label: string; value: string }[] = [];
    
    // Chercher les infos importantes
    lines.forEach(line => {
      if (line.includes('PROBABILITÉ D\'IMPACT:')) {
        const match = line.match(/(\d+)%/);
        if (match) keyInfo.push({ label: 'Probabilité', value: match[1] + '%' });
      }
      if (line.includes('DURÉE ESTIMÉE:')) {
        const match = line.match(/(\d+)\s*jours/);
        if (match) keyInfo.push({ label: 'Durée', value: match[1] + ' jours' });
      }
      if (line.includes('Impact financier estimé:')) {
        const match = line.match(/([\d,\.]+[€$])|(\d+[,\.]*\d*\s*(M€|k€|EUR))/);
        if (match) keyInfo.push({ label: 'Impact financier', value: match[0] });
      }
    });
    
    return keyInfo;
  };

  const renderAffectedEntity = (entity: AffectedEntity, index: number, type: 'site' | 'supplier') => {
    const scoreColor = getScoreColor(entity.risk_score);
    const keyInfo = entity.reasoning ? extractKeyInfo(entity.reasoning) : [];
    
    return (
      <div key={entity.id || index} className="bg-slate-50 rounded-lg p-3 mb-2 border border-slate-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {type === 'site' ? (
              <svg className="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
            ) : (
              <svg className="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
            )}
            <h4 className="font-semibold text-slate-800 text-sm">{entity.name}</h4>
          </div>
          <div className="flex items-center gap-2">
            <span className={`font-bold text-sm ${scoreColor}`}>
              {entity.risk_score.toFixed(1)}/100
            </span>
            {entity.business_interruption_score != null && entity.business_interruption_score > 0 && (
              <span className="text-xs text-slate-500 bg-slate-200 px-2 py-0.5 rounded">
                BI: {entity.business_interruption_score.toFixed(0)}%
              </span>
            )}
          </div>
        </div>
        {keyInfo.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {keyInfo.map((info, idx) => (
              <span key={idx} className="text-xs bg-white px-2 py-1 rounded border border-slate-200">
                <span className="text-slate-500">{info.label}:</span> <span className="font-medium text-slate-700">{info.value}</span>
              </span>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div 
      className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 overflow-y-auto" 
      style={{ zIndex: 9999 }}
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-2xl w-full max-w-3xl shadow-2xl my-4 flex flex-col max-h-[85vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-800 to-slate-700 text-white p-6 relative">
          <button 
            onClick={onClose}
            className="absolute top-4 right-4 w-10 h-10 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          
          {isLoading ? (
            <div className="animate-pulse">
              <div className="h-8 bg-white/20 rounded w-3/4 mb-3"></div>
              <div className="h-4 bg-white/20 rounded w-1/2"></div>
            </div>
          ) : risk && (
            <>
              <div className="flex items-start gap-4">
                <div className="flex-1">
                  <h2 className="text-2xl font-bold mb-2">{risk.regulation_title}</h2>
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className={`px-3 py-1 rounded-full text-sm font-bold ${getRiskLevelColor(risk.risk_level)}`}>
                      {risk.risk_level.toUpperCase()}
                    </span>
                    <span className="text-white/80">
                      Score: <span className="font-bold">{risk.risk_score.toFixed(1)}/100</span>
                    </span>
                    <span className="text-white/60">
                      {new Date(risk.created_at).toLocaleDateString('fr-FR', {
                        day: 'numeric',
                        month: 'long',
                        year: 'numeric'
                      })}
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Content */}
        <div className="overflow-y-auto flex-1 min-h-0">
          {isLoading ? (
            <div className="p-6 space-y-4 animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-full"></div>
              <div className="h-4 bg-slate-200 rounded w-5/6"></div>
              <div className="h-4 bg-slate-200 rounded w-4/6"></div>
              <div className="h-32 bg-slate-200 rounded mt-6"></div>
            </div>
          ) : risk && (
            <div className="p-6 space-y-6">
              {/* Description de l'impact */}
              {risk.impacts_description && (
                <section>
                  <h3 className="text-lg font-bold text-slate-800 mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
                    Description de l'Impact
                  </h3>
                  <div className="bg-slate-50 rounded-lg p-4 text-slate-700">
                    {risk.impacts_description}
                  </div>
                </section>
              )}

              {/* Impact Supply Chain */}
              {risk.supply_chain_impact && (
                <section className="flex items-center gap-4">
                  <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
                    <svg className="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>
                    Impact Supply Chain
                  </h3>
                  <div className={`px-3 py-1 rounded-lg font-bold text-sm ${
                    risk.supply_chain_impact === 'critique' ? 'bg-red-100 text-red-700' :
                    risk.supply_chain_impact === 'elevé' || risk.supply_chain_impact === 'fort' ? 'bg-orange-100 text-orange-700' :
                    'bg-yellow-100 text-yellow-700'
                  }`}>
                    {risk.supply_chain_impact.toUpperCase()}
                  </div>
                </section>
              )}

              {/* Sites et Fournisseurs en 2 colonnes */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Sites Affectés */}
                {risk.affected_sites && risk.affected_sites.length > 0 && (
                  <section>
                    <h3 className="text-base font-bold text-slate-800 mb-2 flex items-center gap-2">
                      <svg className="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
                      Sites Affectés ({risk.affected_sites.length})
                    </h3>
                    <div className="max-h-60 overflow-y-auto pr-1 space-y-1">
                      {risk.affected_sites.map((site, idx) => renderAffectedEntity(site, idx, 'site'))}
                    </div>
                  </section>
                )}

                {/* Fournisseurs Affectés */}
                {risk.affected_suppliers && risk.affected_suppliers.length > 0 && (
                  <section>
                    <h3 className="text-base font-bold text-slate-800 mb-2 flex items-center gap-2">
                      <svg className="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
                      Fournisseurs ({risk.affected_suppliers.length})
                    </h3>
                    <div className="max-h-60 overflow-y-auto pr-1 space-y-1">
                      {risk.affected_suppliers.map((supplier, idx) => renderAffectedEntity(supplier, idx, 'supplier'))}
                    </div>
                  </section>
                )}
              </div>

              {/* Alertes Météo - Version compacte */}
              {risk.weather_risk_summary && (
                <section>
                  <h3 className="text-base font-bold text-slate-800 mb-2 flex items-center gap-2">
                    <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"/></svg>
                    Risques Météorologiques
                  </h3>
                  <div className="bg-blue-50 rounded-lg p-3">
                    <div className="flex flex-wrap items-center gap-4 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xl font-bold text-blue-600">{risk.weather_risk_summary.total_alerts}</span>
                        <span className="text-xs text-slate-600">alertes</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xl font-bold text-blue-600">{risk.weather_risk_summary.entities_with_alerts}</span>
                        <span className="text-xs text-slate-600">entités</span>
                      </div>
                      <div className={`px-2 py-1 rounded text-sm font-bold ${
                        risk.weather_risk_summary.max_severity === 'critical' ? 'bg-red-100 text-red-700' :
                        risk.weather_risk_summary.max_severity === 'high' ? 'bg-orange-100 text-orange-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {risk.weather_risk_summary.max_severity.toUpperCase()}
                      </div>
                    </div>
                    
                    {risk.weather_risk_summary.alerts_by_type && Object.keys(risk.weather_risk_summary.alerts_by_type).length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(risk.weather_risk_summary.alerts_by_type).map(([type, count]) => (
                          <span key={type} className="px-2 py-0.5 bg-white rounded text-xs text-slate-700 border border-slate-200">
                            {type === 'extreme_heat' && 'Chaleur'}
                            {type === 'extreme_cold' && 'Froid'}
                            {type === 'strong_wind' && 'Vent'}
                            {type === 'storm' && 'Tempête'}
                            {' '}{count}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </section>
              )}

              {/* Recommandations */}
              {risk.recommendations && (
                <section>
                  <h3 className="text-lg font-bold text-slate-800 mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
                    Recommandations
                  </h3>
                  <div className="bg-green-50 rounded-lg p-4">
                    <ul className="text-slate-700">
                      {formatRecommendations(risk.recommendations)}
                    </ul>
                  </div>
                </section>
              )}

              {/* Source */}
              {risk.source_url && (
                <section>
                  <h3 className="text-lg font-bold text-slate-800 mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>
                    Source
                  </h3>
                  <a 
                    href={risk.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 hover:underline break-all"
                  >
                    {risk.source_url}
                  </a>
                  {risk.source_excerpt && (
                    <div className="mt-3 bg-slate-50 rounded-lg p-4 text-sm text-slate-600 italic">
                      "{risk.source_excerpt.substring(0, 300)}..."
                    </div>
                  )}
                </section>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-200 p-4 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-slate-100 text-slate-700 rounded-lg font-medium hover:bg-slate-200 transition-colors"
          >
            Fermer
          </button>
          {risk?.source_url && (
            <a
              href={risk.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-6 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors"
            >
              Voir la source
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default RiskDetailModal;
