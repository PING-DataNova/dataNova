import React from 'react';
import { SupplierDBProfile } from '../services/supplierService';

interface SupplierProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  profile: SupplierDBProfile | null;
  loading: boolean;
  error?: string | null;
}

const SupplierProfileModal: React.FC<SupplierProfileModalProps> = ({
  isOpen,
  onClose,
  profile,
  loading,
  error
}) => {
  if (!isOpen) return null;

  const formatCurrency = (value: number | null | undefined) => {
    if (value == null) return 'N/A';
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatNumber = (value: number | null | undefined) => {
    if (value == null) return 'N/A';
    return new Intl.NumberFormat('fr-FR').format(value);
  };

  const getRiskBadgeColor = (level: string | undefined) => {
    switch (level) {
      case 'eleve': return 'bg-red-100 text-red-700 border-red-200';
      case 'moyen': return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'faible': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getRiskLabel = (level: string | undefined) => {
    switch (level) {
      case 'eleve': return 'Élevé';
      case 'moyen': return 'Moyen';
      case 'faible': return 'Faible';
      default: return level || 'N/A';
    }
  };

  const getHealthBadgeColor = (health: string | undefined) => {
    switch (health?.toLowerCase()) {
      case 'excellent': return 'bg-emerald-100 text-emerald-700';
      case 'bon': return 'bg-lime-100 text-lime-700';
      case 'acceptable': return 'bg-amber-100 text-amber-700';
      case 'precaire': 
      case 'précaire': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getCriticalityBadgeColor = (criticality: string | undefined) => {
    switch (criticality) {
      case 'Critique': return 'bg-red-50 text-red-700 border-red-200';
      case 'Important': return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'Standard': return 'bg-slate-50 text-slate-700 border-slate-200';
      default: return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  return (
    <div 
      className="fixed inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      style={{ zIndex: 10001 }}
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-3xl shadow-2xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-800 to-slate-900 p-6 relative">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-white/10 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            {loading ? (
              <div className="animate-pulse">
                <div className="h-6 w-48 bg-white/20 rounded mb-2"></div>
                <div className="h-4 w-32 bg-white/10 rounded"></div>
              </div>
            ) : profile ? (
              <div>
                <h2 className="text-2xl font-black text-white">{profile.name}</h2>
                <p className="text-white/70 text-sm">
                  {profile.city}, {profile.region} • {profile.country}
                </p>
              </div>
            ) : null}
          </div>
          <button 
            onClick={onClose}
            className="absolute top-4 right-4 w-10 h-10 bg-white/10 hover:bg-white/20 rounded-full flex items-center justify-center transition-colors"
          >
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="w-12 h-12 border-4 border-slate-200 border-t-slate-600 rounded-full animate-spin mb-4"></div>
              <p className="text-slate-500">Chargement du profil...</p>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
              <svg className="w-12 h-12 mx-auto mb-3 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <h3 className="text-red-700 font-bold mb-1">Erreur de chargement</h3>
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          ) : profile ? (
            <div className="space-y-6">
              {/* Badges de statut */}
              <div className="flex flex-wrap gap-2">
                {profile.risk_exposure && (
                  <span className={`px-3 py-1.5 rounded-full text-sm font-bold border ${getRiskBadgeColor(profile.risk_exposure.risk_level)}`}>
                    Risque {getRiskLabel(profile.risk_exposure.risk_level)}
                  </span>
                )}
                <span className={`px-3 py-1.5 rounded-full text-sm font-bold ${getHealthBadgeColor(profile.financial_health)}`}>
                  Santé financière: {profile.financial_health}
                </span>
                {profile.criticality_score !== null && (
                  <span className={`px-3 py-1.5 rounded-full text-sm font-bold ${
                    profile.criticality_score >= 8 ? 'bg-red-100 text-red-700' :
                    profile.criticality_score >= 5 ? 'bg-amber-100 text-amber-700' :
                    'bg-emerald-100 text-emerald-700'
                  }`}>
                    Criticité: {profile.criticality_score}/10
                  </span>
                )}
                <span className="px-3 py-1.5 rounded-full text-sm font-bold bg-slate-100 text-slate-700">
                  {profile.company_size}
                </span>
              </div>

              {/* Grille d'informations */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Informations générales */}
                <div className="bg-slate-50 rounded-xl p-4">
                  <h3 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">
                    Informations générales
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Code</span>
                      <span className="font-medium text-slate-800">{profile.code}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Secteur</span>
                      <span className="font-medium text-slate-800">{profile.sector}</span>
                    </div>
                    {profile.founded_year && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Fondée en</span>
                        <span className="font-medium text-slate-800">{profile.founded_year}</span>
                      </div>
                    )}
                    {profile.employee_count && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Employés</span>
                        <span className="font-medium text-slate-800">{formatNumber(profile.employee_count)}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Données financières */}
                <div className="bg-slate-50 rounded-xl p-4">
                  <h3 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">
                    Données financières
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">CA annuel</span>
                      <span className="font-medium text-slate-800">
                        {profile.annual_revenue_usd ? `${formatNumber(profile.annual_revenue_usd)} $` : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Volume d'achats</span>
                      <span className="font-medium text-slate-800">{formatCurrency(profile.annual_purchase_volume)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Valeur livraison/jour</span>
                      <span className="font-medium text-slate-800">{formatCurrency(profile.daily_delivery_value)}</span>
                    </div>
                  </div>
                </div>

                {/* Logistique */}
                <div className="bg-slate-50 rounded-xl p-4">
                  <h3 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">
                    Logistique
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Stock moyen</span>
                      <span className="font-medium text-slate-800">
                        {profile.average_stock_at_hutchinson_days ? `${profile.average_stock_at_hutchinson_days} jours` : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Délai substitution</span>
                      <span className="font-medium text-slate-800">
                        {profile.switch_time_days ? `${profile.switch_time_days} jours` : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Capacité extensible</span>
                      <span className={`font-medium ${profile.can_increase_capacity ? 'text-emerald-600' : 'text-red-600'}`}>
                        {profile.can_increase_capacity ? 'Oui' : 'Non'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Produits fournis */}
              {profile.products_supplied && profile.products_supplied.length > 0 && (
                <div>
                  <h3 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">
                    Produits fournis
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {profile.products_supplied.map((product, idx) => (
                      <span key={idx} className="px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium border border-blue-100">
                        {product}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Certifications */}
              {profile.certifications && profile.certifications.length > 0 && (
                <div>
                  <h3 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">
                    Certifications
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {profile.certifications.map((cert, idx) => (
                      <span key={idx} className="px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-lg text-sm font-medium border border-emerald-100">
                        ✓ {cert}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Exposition au risque */}
              {profile.risk_exposure && (
                <div className="bg-gradient-to-r from-slate-50 to-slate-100 rounded-xl p-4">
                  <h3 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-4">
                    Exposition au risque
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-black text-slate-800">{profile.risk_exposure.total_sites_served}</div>
                      <div className="text-xs text-slate-500 mt-1">Sites desservis</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-2xl font-black ${profile.risk_exposure.critical_relationships > 0 ? 'text-red-600' : 'text-slate-800'}`}>
                        {profile.risk_exposure.critical_relationships}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">Relations critiques</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-2xl font-black ${profile.risk_exposure.sole_supplier_for > 0 ? 'text-amber-600' : 'text-slate-800'}`}>
                        {profile.risk_exposure.sole_supplier_for}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">Fournisseur unique</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-2xl font-black ${profile.risk_exposure.backup_coverage > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                        {profile.risk_exposure.backup_coverage}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">Couverture backup</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Sites desservis */}
              {profile.sites_served && profile.sites_served.length > 0 && (
                <div>
                  <h3 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">
                    Sites Hutchinson desservis ({profile.sites_served.length})
                  </h3>
                  <div className="space-y-3">
                    {profile.sites_served.map((site, idx) => (
                      <div key={idx} className="border border-slate-200 rounded-xl p-4 hover:bg-slate-50 transition-colors">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h4 className="font-bold text-slate-800">{site.site_name}</h4>
                            <p className="text-sm text-slate-500">{site.site_country}</p>
                          </div>
                          <div className="flex gap-2">
                            <span className={`px-2 py-1 text-xs font-bold rounded-full border ${getCriticalityBadgeColor(site.criticality)}`}>
                              {site.criticality}
                            </span>
                            {site.is_sole_supplier && (
                              <span className="px-2 py-1 text-xs font-bold rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                                Unique
                              </span>
                            )}
                            {site.has_backup_supplier && (
                              <span className="px-2 py-1 text-xs font-bold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                                Backup ✓
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex flex-wrap gap-4 text-sm text-slate-600">
                          {site.lead_time_days && (
                            <span>Délai: {site.lead_time_days} jours</span>
                          )}
                          {site.annual_volume && (
                            <span>Volume: {formatCurrency(site.annual_volume)}</span>
                          )}
                        </div>
                        {site.products_supplied && site.products_supplied.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {site.products_supplied.map((p, i) => (
                              <span key={i} className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs">
                                {p}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Adresse complète */}
              <div className="border-t border-slate-200 pt-4">
                <h3 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-2">
                  Adresse complète
                </h3>
                <p className="text-sm text-slate-600">
                  {profile.address}
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Coordonnées: {profile.latitude}, {profile.longitude}
                </p>
              </div>
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-200 p-4 flex justify-end gap-2 bg-slate-50">
          <button 
            onClick={onClose}
            className="px-6 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-bold hover:bg-slate-800 transition-colors"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
};

export default SupplierProfileModal;
