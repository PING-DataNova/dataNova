import { useState, useEffect, useCallback } from 'react';
import { regulationsService, RegulationResponse } from '../services/regulationsService';
import { Regulation } from '../types';

interface UseRegulationsState {
  regulations: Regulation[];
  loading: boolean;
  error: string | null;
  total: number;
  refetch: () => void;
}

interface UseRegulationsFilters {
  status?: string;
  search?: string;
  page?: number;
  limit?: number;
}

export const useRegulations = (filters: UseRegulationsFilters = {}): UseRegulationsState => {
  const [regulations, setRegulations] = useState<Regulation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const fetchRegulations = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response: RegulationResponse = await regulationsService.getRegulations(filters);
      setRegulations(response.regulations);
      setTotal(response.total);
    } catch (err) {
      console.error('Erreur API:', err);
      setError(err instanceof Error ? err.message : 'Erreur de connexion au serveur');
      setRegulations([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [filters.status, filters.search, filters.page, filters.limit]);

  useEffect(() => {
    fetchRegulations();
  }, [fetchRegulations]);

  return {
    regulations,
    loading,
    error,
    total,
    refetch: fetchRegulations,
  };
};

interface UseRegulationActionsState {
  updating: boolean;
  error: string | null;
  updateStatus: (id: string, status: 'validated' | 'rejected' | 'to-review', comment?: string) => Promise<void>;
}

export const useRegulationActions = (onSuccess?: () => void): UseRegulationActionsState => {
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateStatus = useCallback(async (
    id: string, 
    status: 'validated' | 'rejected' | 'to-review',
    comment?: string
  ) => {
    setUpdating(true);
    setError(null);

    try {
      await regulationsService.updateRegulationStatus({ id, status, comment });
      onSuccess?.();
    } catch (err) {
      console.warn('API non disponible pour la mise à jour, simulation locale:', err);
      // Simuler une mise à jour réussie en mode mock
      setTimeout(() => {
        onSuccess?.();
      }, 500);
      setError('Mode démo - Mise à jour simulée');
    } finally {
      setUpdating(false);
    }
  }, [onSuccess]);

  return {
    updating,
    error,
    updateStatus,
  };
};