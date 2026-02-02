import React, { useEffect, useState } from 'react';
import './UnifiedDashboard.css';
import { RegulationCard } from '../components/RegulationCard/RegulationCard';
import { useRegulations, useRegulationActions } from '../hooks/useRegulations';
import { impactsService } from '../services/impactsService';

export const UnifiedDashboard: React.FC = () => {
  const { regulations, loading, error, total, refetch } = useRegulations({ limit: 50 });
  const { updating, updateStatus } = useRegulationActions(() => refetch());
  const [impactsCount, setImpactsCount] = useState(0);
  const [highRiskCount, setHighRiskCount] = useState(0);

  useEffect(() => {
    const loadImpacts = async () => {
      try {
        const resp = await impactsService.getImpacts({ limit: 100 });
        setImpactsCount(resp.total);
        setHighRiskCount(resp.impacts.filter(i => i.impact_level === 'eleve').length);
      } catch (err) {
        console.warn('Impossible de récupérer les impacts:', err);
      }
    };
    loadImpacts();
  }, []);

  const handleValidate = async (id: string) => {
    await updateStatus(id, 'validated');
  };

  const handleReject = async (id: string) => {
    await updateStatus(id, 'rejected');
  };

  const handleReview = async (id: string) => {
    await updateStatus(id, 'to-review');
  };

  return (
    <div className="unified-layout">
      <header className="unified-header">
        <h1>Tableau de bord unifié</h1>
        <div className="unified-header-meta">
          <div className="meta-item">Réglementations: {total}</div>
          <div className="meta-item">Impacts analysés: {impactsCount}</div>
          <div className="meta-item warning">Risques élevés: {highRiskCount}</div>
        </div>
      </header>

      <main className="unified-main">
        <section className="unified-left">
          <div className="list-header">
            <h2>Réglementations</h2>
            <p className="muted">Validez, rejetez ou marquez pour relecture</p>
          </div>

          {loading ? (
            <div className="loading">Chargement des réglementations...</div>
          ) : error ? (
            <div className="error">Erreur: {error}</div>
          ) : (
            <div className="regulations-grid">
              {regulations.map((reg) => (
                <RegulationCard
                  key={reg.id}
                  regulation={reg}
                  onValidate={handleValidate}
                  onReject={handleReject}
                  onReview={handleReview}
                  disabled={updating}
                />
              ))}
              {regulations.length === 0 && (
                <div className="empty">Aucune réglementation trouvée.</div>
              )}
            </div>
          )}
        </section>

        <aside className="unified-right">
          <div className="report-card">
            <h3>Reporting</h3>
            <div className="report-metrics">
              <div className="metric">
                <div className="metric-value">{total}</div>
                <div className="metric-label">Réglementations suivies</div>
              </div>
              <div className="metric">
                <div className="metric-value">{impactsCount}</div>
                <div className="metric-label">Impacts analysés</div>
              </div>
              <div className="metric warning">
                <div className="metric-value">{highRiskCount}</div>
                <div className="metric-label">Risques élevés</div>
              </div>
            </div>
            <div className="report-actions">
              <button className="btn primary" onClick={() => window.print()}>Exporter PDF</button>
            </div>
          </div>

          <div className="quick-list">
            <h4>Impacts récents</h4>
            <p className="muted">Affichage succinct des derniers impacts détectés</p>
            {/* Placeholder: on peut remplacer par une liste détaillée selon la maquette */}
            <div className="impact-placeholder">Aucun détail (maquette à venir)</div>
          </div>
        </aside>
      </main>
    </div>
  );
};
