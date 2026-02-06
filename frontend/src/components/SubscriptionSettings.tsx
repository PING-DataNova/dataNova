import React, { useState, useEffect } from 'react';
import {
  subscriptionService,
  Subscription,
  SubscriptionCreate,
  SupplierOption,
  SiteOption,
  EventTypeOption,
  CriticalityOption,
} from '../services/subscriptionService';

interface SubscriptionSettingsProps {
  userEmail: string;
  onClose: () => void;
}

const SubscriptionSettings: React.FC<SubscriptionSettingsProps> = ({ userEmail, onClose }) => {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Options pour les filtres
  const [supplierOptions, setSupplierOptions] = useState<SupplierOption[]>([]);
  const [siteOptions, setSiteOptions] = useState<SiteOption[]>([]);
  const [countryOptions, setCountryOptions] = useState<string[]>([]);
  const [eventTypeOptions, setEventTypeOptions] = useState<EventTypeOption[]>([]);
  const [criticalityOptions, setCriticalityOptions] = useState<CriticalityOption[]>([]);
  
  // État du formulaire pour nouvel abonnement
  const [showNewForm, setShowNewForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<SubscriptionCreate>({
    email: userEmail,
    subscription_name: 'Mon abonnement',
    event_types: ['all'],
    supplier_ids: [],
    site_ids: [],
    countries: [],
    min_criticality: 'MOYEN',
    notify_immediately: true,
    include_weather_alerts: true,
    include_regulatory: true,
    include_geopolitical: true,
  });

  // Charger les données
  useEffect(() => {
    loadData();
  }, [userEmail]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [subs, suppliers, sites, countries, eventTypes, criticalities] = await Promise.all([
        subscriptionService.getSubscriptions(userEmail),
        subscriptionService.getSupplierOptions(),
        subscriptionService.getSiteOptions(),
        subscriptionService.getCountryOptions(),
        subscriptionService.getEventTypeOptions(),
        subscriptionService.getCriticalityOptions(),
      ]);
      setSubscriptions(subs);
      setSupplierOptions(suppliers);
      setSiteOptions(sites);
      setCountryOptions(countries);
      setEventTypeOptions(eventTypes);
      setCriticalityOptions(criticalities);
    } catch (err) {
      setError('Erreur lors du chargement des données');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSubscription = async () => {
    setSaving(true);
    setError(null);
    try {
      await subscriptionService.createSubscription(formData);
      setSuccess('Abonnement créé avec succès !');
      setShowNewForm(false);
      resetForm();
      await loadData();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Erreur lors de la création');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateSubscription = async (id: string) => {
    setSaving(true);
    setError(null);
    try {
      await subscriptionService.updateSubscription(id, formData);
      setSuccess('Abonnement mis à jour !');
      setEditingId(null);
      resetForm();
      await loadData();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Erreur lors de la mise à jour');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteSubscription = async (id: string) => {
    if (!confirm('Voulez-vous vraiment supprimer cet abonnement ?')) return;
    
    try {
      await subscriptionService.deleteSubscription(id);
      setSuccess('Abonnement supprimé');
      await loadData();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Erreur lors de la suppression');
    }
  };

  const handleToggleSubscription = async (id: string) => {
    try {
      await subscriptionService.toggleSubscription(id);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Erreur lors du basculement');
    }
  };

  const resetForm = () => {
    setFormData({
      email: userEmail,
      subscription_name: 'Mon abonnement',
      event_types: ['all'],
      supplier_ids: [],
      site_ids: [],
      countries: [],
      min_criticality: 'MOYEN',
      notify_immediately: true,
      include_weather_alerts: true,
      include_regulatory: true,
      include_geopolitical: true,
    });
  };

  const startEditing = (sub: Subscription) => {
    setEditingId(sub.id);
    setFormData({
      email: sub.email,
      subscription_name: sub.subscription_name,
      event_types: sub.event_types,
      supplier_ids: sub.supplier_ids || [],
      site_ids: sub.site_ids || [],
      countries: sub.countries || [],
      min_criticality: sub.min_criticality,
      notify_immediately: sub.notify_immediately,
      include_weather_alerts: sub.include_weather_alerts,
      include_regulatory: sub.include_regulatory,
      include_geopolitical: sub.include_geopolitical,
    });
    setShowNewForm(false);
  };

  const cancelEditing = () => {
    setEditingId(null);
    resetForm();
  };

  // Gestion des multi-select
  const toggleArrayItem = (array: string[], item: string): string[] => {
    if (array.includes(item)) {
      return array.filter(i => i !== item);
    }
    return [...array, item];
  };

  const renderForm = (isNew: boolean) => (
    <div className="bg-gray-50 rounded-lg p-4 mb-4 border border-gray-200">
      <h4 className="font-semibold text-black mb-4">
        {isNew ? 'Nouvel abonnement' : 'Modifier l\'abonnement'}
      </h4>
      
      {/* Nom de l'abonnement */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-black mb-1">
          Nom de l'abonnement
        </label>
        <input
          type="text"
          value={formData.subscription_name}
          onChange={(e) => setFormData({ ...formData, subscription_name: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          placeholder="Ex: Alertes fournisseurs Chine"
        />
      </div>

      {/* Types d'événements */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-black mb-2">
          Types d'alertes
        </label>
        <div className="grid grid-cols-2 gap-2">
          {eventTypeOptions.map((opt) => (
            <label
              key={opt.value}
              className={`flex items-center p-2 rounded-md cursor-pointer border ${
                formData.event_types?.includes(opt.value)
                  ? 'bg-blue-50 border-blue-300'
                  : 'bg-white border-gray-200 hover:bg-gray-50'
              }`}
            >
              <input
                type="checkbox"
                checked={formData.event_types?.includes(opt.value)}
                onChange={() => {
                  if (opt.value === 'all') {
                    setFormData({ ...formData, event_types: ['all'] });
                  } else {
                    const newTypes = toggleArrayItem(
                      (formData.event_types || []).filter(t => t !== 'all'),
                      opt.value
                    );
                    setFormData({ ...formData, event_types: newTypes.length ? newTypes : ['all'] });
                  }
                }}
                className="mr-2"
              />
              <div>
                <span className="text-sm font-medium text-black">{opt.label}</span>
                <p className="text-xs text-gray-700">{opt.description}</p>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Niveau de criticité minimum */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-black mb-2">
          Niveau de criticité minimum
        </label>
        <div className="grid grid-cols-2 gap-2">
          {criticalityOptions.map((opt) => (
            <label
              key={opt.value}
              className={`flex items-center p-2 rounded-md cursor-pointer border ${
                formData.min_criticality === opt.value
                  ? 'bg-blue-50 border-blue-300'
                  : 'bg-white border-gray-200 hover:bg-gray-50'
              }`}
            >
              <input
                type="radio"
                name="criticality"
                checked={formData.min_criticality === opt.value}
                onChange={() => setFormData({ ...formData, min_criticality: opt.value })}
                className="mr-2"
              />
              <div>
                <span className="text-sm font-medium text-black">{opt.label}</span>
                <p className="text-xs text-gray-700">{opt.description}</p>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Fournisseurs */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-black mb-2">
          Fournisseurs spécifiques (laisser vide = tous)
        </label>
        {supplierOptions.length > 0 ? (
          <div className="max-h-40 overflow-y-auto border border-gray-200 rounded-md p-2 bg-white">
            {supplierOptions.map((supplier) => (
              <label
                key={supplier.id}
                className="flex items-center p-1 hover:bg-gray-50 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={formData.supplier_ids?.includes(supplier.id)}
                  onChange={() =>
                    setFormData({
                      ...formData,
                      supplier_ids: toggleArrayItem(formData.supplier_ids || [], supplier.id),
                    })
                  }
                  className="mr-2"
                />
                <span className="text-sm text-black">
                  {supplier.name} <span className="text-gray-600">({supplier.country})</span>
                </span>
              </label>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500 italic">Aucun fournisseur disponible</p>
        )}
      </div>

      {/* Sites */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-black mb-2">
          Sites Hutchinson spécifiques (laisser vide = tous)
        </label>
        {siteOptions.length > 0 ? (
          <div className="max-h-40 overflow-y-auto border border-gray-200 rounded-md p-2 bg-white">
            {siteOptions.map((site) => (
              <label
                key={site.id}
                className="flex items-center p-1 hover:bg-gray-50 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={formData.site_ids?.includes(site.id)}
                  onChange={() =>
                    setFormData({
                      ...formData,
                      site_ids: toggleArrayItem(formData.site_ids || [], site.id),
                    })
                  }
                  className="mr-2"
                />
                <span className="text-sm text-black">
                  {site.name} <span className="text-gray-600">({site.city}, {site.country})</span>
                </span>
              </label>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500 italic">Aucun site disponible</p>
        )}
      </div>

      {/* Pays */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-black mb-2">
          Pays spécifiques (laisser vide = tous)
        </label>
        {countryOptions.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {countryOptions.map((country) => (
              <label
                key={country}
                className={`px-3 py-1 rounded-full text-sm cursor-pointer border ${
                  formData.countries?.includes(country)
                    ? 'bg-blue-100 border-blue-300 text-blue-800'
                    : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                }`}
              >
                <input
                  type="checkbox"
                  checked={formData.countries?.includes(country)}
                  onChange={() =>
                    setFormData({
                      ...formData,
                      countries: toggleArrayItem(formData.countries || [], country),
                    })
                  }
                  className="sr-only"
                />
                {country}
              </label>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500 italic">Aucun pays disponible</p>
        )}
      </div>

      {/* Options de notification */}
      <div className="mb-4 p-3 bg-white rounded-md border border-gray-200">
        <h5 className="font-medium text-black mb-2">Options de notification</h5>
        <div className="space-y-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={formData.notify_immediately}
              onChange={(e) => setFormData({ ...formData, notify_immediately: e.target.checked })}
              className="mr-2"
            />
            <span className="text-sm text-black">Notification immédiate</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={formData.include_weather_alerts}
              onChange={(e) => setFormData({ ...formData, include_weather_alerts: e.target.checked })}
              className="mr-2"
            />
            <span className="text-sm text-black">Inclure les alertes météo</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={formData.include_regulatory}
              onChange={(e) => setFormData({ ...formData, include_regulatory: e.target.checked })}
              className="mr-2"
            />
            <span className="text-sm text-black">Inclure les alertes réglementaires</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={formData.include_geopolitical}
              onChange={(e) => setFormData({ ...formData, include_geopolitical: e.target.checked })}
              className="mr-2"
            />
            <span className="text-sm text-black">Inclure les alertes géopolitiques</span>
          </label>
        </div>
      </div>

      {/* Boutons */}
      <div className="flex gap-2">
        <button
          onClick={() => isNew ? handleCreateSubscription() : handleUpdateSubscription(editingId!)}
          disabled={saving || !formData.subscription_name}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Enregistrement...' : isNew ? 'Créer l\'abonnement' : 'Enregistrer'}
        </button>
        <button
          onClick={() => isNew ? setShowNewForm(false) : cancelEditing()}
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
        >
          Annuler
        </button>
      </div>
    </div>
  );

  const renderSubscriptionCard = (sub: Subscription) => {
    const isEditing = editingId === sub.id;
    
    if (isEditing) {
      return <div key={sub.id}>{renderForm(false)}</div>;
    }

    return (
      <div
        key={sub.id}
        className={`bg-white rounded-lg p-4 border ${
          sub.is_active ? 'border-green-200' : 'border-gray-200 opacity-60'
        } mb-3`}
      >
        <div className="flex justify-between items-start mb-2">
          <div>
            <h4 className="font-semibold text-gray-800 flex items-center gap-2">
              {sub.subscription_name}
              {sub.is_active ? (
                <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">Actif</span>
              ) : (
                <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded-full">Inactif</span>
              )}
            </h4>
            <p className="text-sm text-gray-500">{sub.email}</p>
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => handleToggleSubscription(sub.id)}
              className={`p-1.5 rounded ${
                sub.is_active ? 'hover:bg-yellow-50 text-yellow-600' : 'hover:bg-green-50 text-green-600'
              }`}
              title={sub.is_active ? 'Désactiver' : 'Activer'}
            >
              {sub.is_active ? 'Pause' : 'Play'}
            </button>
            <button
              onClick={() => startEditing(sub)}
              className="p-1.5 rounded hover:bg-blue-50 text-blue-600"
              title="Modifier"
            >
              Modifier
            </button>
            <button
              onClick={() => handleDeleteSubscription(sub.id)}
              className="p-1.5 rounded hover:bg-red-50 text-red-600"
              title="Supprimer"
            >
              Suppr
            </button>
          </div>
        </div>

        {/* Filtres appliqués */}
        <div className="flex flex-wrap gap-2 text-xs">
          {/* Types d'événements */}
          <div className="flex items-center gap-1">
            <span className="text-gray-500">Types:</span>
            {sub.event_types.includes('all') ? (
              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">Tous</span>
            ) : (
              sub.event_types.map((t) => (
                <span key={t} className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                  {t}
                </span>
              ))
            )}
          </div>

          {/* Criticité */}
          <span className="px-2 py-0.5 bg-orange-100 text-orange-700 rounded">
            Criticité: {sub.min_criticality}+
          </span>

          {/* Fournisseurs */}
          {sub.supplier_names && sub.supplier_names.length > 0 && (
            <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded">
              {sub.supplier_names.length} fournisseur(s)
            </span>
          )}

          {/* Sites */}
          {sub.site_names && sub.site_names.length > 0 && (
            <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded">
              {sub.site_names.length} site(s)
            </span>
          )}

          {/* Pays */}
          {sub.countries && sub.countries.length > 0 && (
            <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded">
              {sub.countries.length} pays
            </span>
          )}
        </div>

        {/* Stats */}
        <div className="mt-2 pt-2 border-t border-gray-100 flex justify-between text-xs text-gray-500">
          <span>{sub.notification_count} notifications reçues</span>
          {sub.last_notified_at && (
            <span>Dernière: {new Date(sub.last_notified_at).toLocaleDateString('fr-FR')}</span>
          )}
        </div>
      </div>
    );
  };

  return (
    <div 
      className="fixed inset-0 flex items-center justify-center p-4"
      style={{ zIndex: 9999, backgroundColor: 'rgba(0, 0, 0, 0.6)' }}
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col relative" style={{ zIndex: 10000 }}>
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-gradient-to-r from-blue-600 to-blue-700">
          <div>
            <h2 className="text-xl font-bold text-white">Mes abonnements aux alertes</h2>
            <p className="text-blue-100 text-sm">Personnalisez les notifications que vous recevez</p>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-blue-500 rounded-full p-2 transition-colors"
          >
            X
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 bg-white">
          {/* Messages */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md">
              {error}
            </div>
          )}
          {success && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-md">
              {success}
            </div>
          )}

          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-2"></div>
              <p className="text-gray-500">Chargement...</p>
            </div>
          ) : (
            <>
              {/* Bouton nouveau */}
              {!showNewForm && !editingId && (
                <button
                  onClick={() => {
                    resetForm();
                    setShowNewForm(true);
                  }}
                  className="w-full mb-4 px-4 py-3 border-2 border-dashed border-blue-300 text-blue-600 rounded-lg hover:bg-blue-50 hover:border-blue-400 transition-colors"
                >
                  + Créer un nouvel abonnement
                </button>
              )}

              {/* Formulaire nouveau */}
              {showNewForm && renderForm(true)}

              {/* Liste des abonnements */}
              {subscriptions.length === 0 && !showNewForm ? (
                <div className="text-center py-8 text-gray-500">
                  <p className="text-4xl mb-2"></p>
                  <p>Vous n'avez pas encore d'abonnement.</p>
                  <p className="text-sm">Créez-en un pour recevoir des alertes personnalisées !</p>
                </div>
              ) : (
                <div>
                  {subscriptions.map(renderSubscriptionCard)}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <p className="text-xs text-gray-500 text-center">
            Conseil: Créez plusieurs abonnements avec des filtres différents pour organiser vos alertes.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionSettings;
