import React from 'react';
import { 
  SupplierAnalysisResponse, 
  RISK_LEVEL_COLORS, 
  SEVERITY_COLORS,
  PRIORITY_COLORS 
} from '../types/supplier';
import './SupplierAnalysisResults.css';

interface SupplierAnalysisResultsProps {
  result: SupplierAnalysisResponse;
  onNewAnalysis: () => void;
  onBack: () => void;
}

const SupplierAnalysisResults: React.FC<SupplierAnalysisResultsProps> = ({
  result,
  onNewAnalysis,
  onBack
}) => {
  const { supplier_info, regulatory_risks, weather_risks, risk_score, risk_level, recommendations } = result;

  // Calculer le pourcentage pour la barre de progression
  const scorePercentage = (risk_score / 10) * 100;

  return (
    <div className="results-page">
      {/* Header */}
      <div className="results-header">
        <button className="back-button" onClick={onBack}>
          Retour
        </button>
        <h1>Résultats - {supplier_info.name}</h1>
        <p className="subtitle">{supplier_info.city ? `${supplier_info.city}, ` : ''}{supplier_info.country}</p>
      </div>

      {/* Score global */}
      <div className="score-card">
        <h2>Score de Risque Global</h2>
        <div className="score-bar-container">
          <div 
            className="score-bar" 
            style={{ 
              width: `${scorePercentage}%`,
              backgroundColor: RISK_LEVEL_COLORS[risk_level] || '#6B7280'
            }}
          ></div>
        </div>
        <div className="score-display">
          <span className="score-value">{risk_score.toFixed(1)}</span>
          <span className="score-max">/ 10</span>
          <span 
            className="risk-level-badge"
            style={{ backgroundColor: RISK_LEVEL_COLORS[risk_level] || '#6B7280' }}
          >
            {risk_level}
          </span>
        </div>
      </div>

      {/* Stats rapides */}
      <div className="quick-stats">
        <div className="stat-card regulatory">
          <span className="stat-value">{regulatory_risks.count}</span>
          <span className="stat-label">Risques réglementaires</span>
        </div>
        <div className="stat-card weather">
          <span className="stat-value">{weather_risks.count}</span>
          <span className="stat-label">Alertes météo</span>
        </div>
      </div>

      {/* Risques réglementaires */}
      {regulatory_risks.count > 0 && (
        <div className="section">
          <h2>Risques réglementaires</h2>
          <div className="risks-list">
            {regulatory_risks.items.map((risk, index) => (
              <div key={index} className={`risk-card relevance-${risk.relevance}`}>
                <div className="risk-header">
                  <span 
                    className="relevance-badge"
                    style={{ backgroundColor: risk.relevance === 'high' ? '#EF4444' : risk.relevance === 'medium' ? '#F59E0B' : '#10B981' }}
                  >
                    {risk.relevance.toUpperCase()}
                  </span>
                  <span className="risk-type">{risk.document_type || 'REGULATION'}</span>
                </div>
                <h3>{risk.title}</h3>
                <div className="risk-meta">
                  <span>CELEX: {risk.celex_id}</span>
                  {risk.publication_date && <span>{risk.publication_date}</span>}
                  <span>Matière: {risk.matched_keyword}</span>
                </div>
                <a 
                  href={risk.source_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="eurlex-link"
                >
                  Voir sur EUR-Lex
                </a>
                {risk.celex_id && (
                  <a
                    href={`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}/documents/by-celex/${risk.celex_id}`}
                    download={`${risk.celex_id}.pdf`}
                    className="pdf-link"
                    style={{marginLeft: '1em', color: '#2563eb', fontWeight: 'bold'}}
                  >
                    Télécharger PDF
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Alertes météo */}
      {weather_risks.count > 0 && (
        <div className="section">
          <h2>Alertes météo (16 prochains jours)</h2>
          <div className="risks-list">
            {weather_risks.items.map((alert, index) => (
              <div key={index} className={`risk-card severity-${alert.severity}`}>
                <div className="risk-header">
                  <span 
                    className="severity-badge"
                    style={{ backgroundColor: SEVERITY_COLORS[alert.severity] || '#6B7280' }}
                  >
                    {alert.severity.toUpperCase()}
                  </span>
                  <span className="alert-type">
                    {alert.alert_type === 'heavy_rain' && 'Fortes pluies'}
                    {alert.alert_type === 'snow' && 'Neige'}
                    {alert.alert_type === 'extreme_heat' && 'Canicule'}
                    {alert.alert_type === 'extreme_cold' && 'Grand froid'}
                    {alert.alert_type === 'high_wind' && 'Vents forts'}
                  </span>
                </div>
                <h3>{alert.description}</h3>
                <div className="risk-meta">
                  <span>{alert.date}</span>
                  <span>{alert.value} {alert.unit} (seuil: {alert.threshold})</span>
                </div>
                <div className="supply-chain-impact">
                  Impact: {alert.supply_chain_risk}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pas de risques détectés */}
      {regulatory_risks.count === 0 && weather_risks.count === 0 && (
        <div className="no-risks">
          <h3>Aucun risque majeur détecté</h3>
          <p>Ce fournisseur ne présente pas de risques réglementaires ou météorologiques significatifs pour le moment.</p>
        </div>
      )}

      {/* Recommandations */}
      {recommendations.length > 0 && (
        <div className="section">
          <h2>Recommandations</h2>
          <div className="recommendations-list">
            {recommendations.map((rec, index) => (
              <div key={index} className={`recommendation-card priority-${rec.priority}`}>
                <div className="rec-header">
                  <span 
                    className="priority-badge"
                    style={{ backgroundColor: PRIORITY_COLORS[rec.priority] || '#6B7280' }}
                  >
                    {rec.priority === 'high' && 'HAUTE PRIORITÉ'}
                    {rec.priority === 'medium' && 'MOYENNE'}
                    {rec.priority === 'low' && 'BASSE'}
                  </span>
                  <span className="rec-type">
                    {rec.type === 'regulatory' && 'Réglementaire'}
                    {rec.type === 'weather' && 'Météo'}
                    {rec.type === 'general' && 'Général'}
                  </span>
                </div>
                <h3>{rec.action}</h3>
                <p>{rec.details}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Informations du fournisseur */}
      <div className="section supplier-summary">
      <h2>Récapitulatif fournisseur</h2>
        <div className="summary-grid">
          <div className="summary-item">
            <span className="label">Nom</span>
            <span className="value">{supplier_info.name}</span>
          </div>
          <div className="summary-item">
            <span className="label">Localisation</span>
            <span className="value">{supplier_info.city ? `${supplier_info.city}, ` : ''}{supplier_info.country}</span>
          </div>
          <div className="summary-item">
            <span className="label">Criticité</span>
            <span className="value">{supplier_info.criticality}</span>
          </div>
          {supplier_info.annual_volume && (
            <div className="summary-item">
              <span className="label">Volume annuel</span>
              <span className="value">{supplier_info.annual_volume.toLocaleString()} €</span>
            </div>
          )}
          <div className="summary-item full-width">
            <span className="label">Matières</span>
            <div className="tags">
              {supplier_info.materials.map(m => (
                <span key={m} className="tag">{m}</span>
              ))}
            </div>
          </div>
          {supplier_info.nc_codes.length > 0 && (
            <div className="summary-item full-width">
              <span className="label">Codes NC</span>
              <div className="tags">
                {supplier_info.nc_codes.map(c => (
                  <span key={c} className="tag tag-code">{c}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Temps de traitement */}
      <div className="processing-info">
        Analyse effectuée en {(result.processing_time_ms / 1000).toFixed(2)}s
      </div>

      {/* Actions */}
      <div className="actions">
        <button className="action-button primary" onClick={onNewAnalysis}>
          Nouvelle analyse
        </button>
        <button className="action-button secondary" onClick={onBack}>
          Retour au dashboard
        </button>
      </div>
    </div>
  );
};

export default SupplierAnalysisResults;
