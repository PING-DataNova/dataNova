/**
 * Composant Carte des Fournisseurs à Risque
 * 
 * Affiche une carte Leaflet réaliste avec les localisations des fournisseurs
 * et leur niveau de risque associé.
 */

import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import '../styles/leaflet-custom.css';

export interface SupplierLocation {
  id: string;
  name: string;
  country: string;
  city?: string;
  lat: number;
  lng: number;
  riskLevel: 'faible' | 'moyen' | 'eleve';
  riskCount: number;
  regulations?: string[];
}

interface SupplierMapProps {
  suppliers: SupplierLocation[];
  onSupplierClick?: (supplier: SupplierLocation) => void;
}

// Créer des icônes personnalisées pour chaque niveau de risque
const createCustomIcon = (riskLevel: string, riskCount: number) => {
  const colors: Record<string, { bg: string; border: string; shadow: string }> = {
    eleve: { bg: '#EF4444', border: '#B91C1C', shadow: 'rgba(239, 68, 68, 0.5)' },
    moyen: { bg: '#F59E0B', border: '#D97706', shadow: 'rgba(245, 158, 11, 0.5)' },
    faible: { bg: '#10B981', border: '#059669', shadow: 'rgba(16, 185, 129, 0.5)' },
  };

  const color = colors[riskLevel] || colors.faible;
  const size = riskLevel === 'eleve' ? 32 : riskLevel === 'moyen' ? 28 : 24;
  const pulse = riskLevel === 'eleve' ? `
    <div style="
      position: absolute;
      top: 50%;
      left: 50%;
      width: ${size + 16}px;
      height: ${size + 16}px;
      transform: translate(-50%, -50%);
      background: ${color.shadow};
      border-radius: 50%;
      animation: pulse 2s infinite;
    "></div>
  ` : '';

  const html = `
    <div style="position: relative; width: ${size}px; height: ${size}px;">
      ${pulse}
      <div style="
        position: absolute;
        top: 0;
        left: 0;
        width: ${size}px;
        height: ${size}px;
        background: ${color.bg};
        border: 3px solid ${color.border};
        border-radius: 50%;
        box-shadow: 0 4px 12px ${color.shadow}, 0 0 0 3px rgba(255,255,255,0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: ${size * 0.4}px;
        font-family: system-ui, sans-serif;
      ">
        ${riskCount > 1 ? riskCount : ''}
      </div>
    </div>
    <style>
      @keyframes pulse {
        0% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
        100% { transform: translate(-50%, -50%) scale(2); opacity: 0; }
      }
    </style>
  `;

  return L.divIcon({
    html,
    className: 'custom-marker',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
};

// Composant pour ajuster la vue de la carte et corriger les bugs de rendu
const FitBounds: React.FC<{ suppliers: SupplierLocation[] }> = ({ suppliers }) => {
  const map = useMap();

  useEffect(() => {
    // Force le recalcul de la taille après le montage
    setTimeout(() => {
      map.invalidateSize();
    }, 100);

    // Recalculer aussi lors du redimensionnement
    const handleResize = () => {
      map.invalidateSize();
    };
    window.addEventListener('resize', handleResize);

    if (suppliers.length > 0) {
      const bounds = L.latLngBounds(suppliers.map(s => [s.lat, s.lng]));
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 4 });
    }

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [suppliers, map]);

  // Corriger le bug des tuiles grises lors du zoom
  useEffect(() => {
    const handleZoomEnd = () => {
      setTimeout(() => {
        map.invalidateSize();
      }, 50);
    };
    map.on('zoomend', handleZoomEnd);
    map.on('moveend', handleZoomEnd);

    return () => {
      map.off('zoomend', handleZoomEnd);
      map.off('moveend', handleZoomEnd);
    };
  }, [map]);

  return null;
};

// Couleur selon le niveau de risque
const getRiskLabel = (level: string): string => {
  switch (level) {
    case 'eleve': return 'Risque Élevé';
    case 'moyen': return 'Risque Moyen';
    case 'faible': return 'Risque Faible';
    default: return 'Risque Inconnu';
  }
};

const getRiskBadgeClass = (level: string): string => {
  switch (level) {
    case 'eleve': return 'bg-red-500';
    case 'moyen': return 'bg-amber-500';
    case 'faible': return 'bg-emerald-500';
    default: return 'bg-slate-500';
  }
};

const SupplierMap: React.FC<SupplierMapProps> = ({ suppliers, onSupplierClick }) => {
  // Centre par défaut : Europe/Asie
  const defaultCenter: [number, number] = [30, 50];
  const defaultZoom = 2;

  return (
    <div className="relative w-full rounded-xl overflow-hidden" style={{ height: '100%', minHeight: '280px' }}>
      <MapContainer
        center={defaultCenter}
        zoom={defaultZoom}
        className="w-full"
        style={{ background: '#E2E8F0', height: '100%', minHeight: '280px' }}
        zoomControl={false}
        attributionControl={false}
      >
        {/* Fond clair style Voyager, sans texte */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}{r}.png"
          attribution='&copy; OpenStreetMap'
        />

        {/* Ajuster la vue pour inclure tous les fournisseurs */}
        <FitBounds suppliers={suppliers} />

        {/* Marqueurs des fournisseurs */}
        {suppliers.map(supplier => (
          <Marker
            key={supplier.id}
            position={[supplier.lat, supplier.lng]}
            icon={createCustomIcon(supplier.riskLevel, supplier.riskCount)}
            eventHandlers={{
              click: () => onSupplierClick?.(supplier),
            }}
          >
            <Popup className="custom-popup">
              <div className="min-w-[200px] p-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`w-3 h-3 rounded-full ${getRiskBadgeClass(supplier.riskLevel)}`}></span>
                  <span className="font-bold text-slate-900">{supplier.name}</span>
                </div>
                <p className="text-sm text-slate-600 mb-2">
                  📍 {supplier.city ? `${supplier.city}, ` : ''}{supplier.country}
                </p>
                <div className="flex items-center gap-2 mb-2">
                  <span className={`px-2 py-0.5 text-xs font-bold text-white rounded ${getRiskBadgeClass(supplier.riskLevel)}`}>
                    {getRiskLabel(supplier.riskLevel)}
                  </span>
                  <span className="text-xs text-slate-500">
                    {supplier.riskCount} risque{supplier.riskCount > 1 ? 's' : ''}
                  </span>
                </div>
                {supplier.regulations && supplier.regulations.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {supplier.regulations.slice(0, 3).map((reg, idx) => (
                      <span key={idx} className="px-1.5 py-0.5 bg-slate-100 text-slate-600 text-xs rounded">
                        {reg}
                      </span>
                    ))}
                    {supplier.regulations.length > 3 && (
                      <span className="px-1.5 py-0.5 bg-slate-200 text-slate-500 text-xs rounded">
                        +{supplier.regulations.length - 3}
                      </span>
                    )}
                  </div>
                )}
                <button 
                  onClick={() => onSupplierClick?.(supplier)}
                  className="w-full mt-3 px-3 py-1.5 bg-slate-900 text-white text-xs font-bold rounded-lg hover:bg-slate-800 transition-colors"
                >
                  Voir détails
                </button>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Légende */}
      <div className="absolute bottom-3 left-3 flex items-center gap-3 bg-slate-800/90 backdrop-blur-sm px-3 py-2 rounded-lg border border-slate-600 z-[1000]">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-emerald-500 border-2 border-white shadow-sm"></span>
          <span className="text-[10px] text-slate-200 font-medium">Faible</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-amber-500 border-2 border-white shadow-sm"></span>
          <span className="text-[10px] text-slate-200 font-medium">Moyen</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-red-500 border-2 border-white shadow-sm"></span>
          <span className="text-[10px] text-slate-200 font-medium">Élevé</span>
        </div>
      </div>

      {/* Compteur */}
      <div className="absolute top-3 right-3 bg-slate-800/90 backdrop-blur-sm px-3 py-2 rounded-lg border border-slate-600 z-[1000]">
        <span className="text-xs text-slate-200 font-medium">{suppliers.length} fournisseur{suppliers.length > 1 ? 's' : ''}</span>
      </div>

      {/* Attribution discrète */}
      <div className="absolute bottom-3 right-3 text-[8px] text-slate-500 z-[1000]">
        © OpenStreetMap
      </div>
    </div>
  );
};

export default SupplierMap;
