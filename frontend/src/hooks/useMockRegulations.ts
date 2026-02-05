import { useState, useCallback, useMemo } from 'react';
import { mockRegulations } from '../data/mockData';
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

export const useMockRegulations = (filters: UseRegulationsFilters = {}): UseRegulationsState => {
  const [regulations] = useState<Regulation[]>(mockRegulations);
  const [loading, setLoading] = useState(false);

  const filteredRegulations = useMemo(() => {
    let filtered = regulations;

    // Filtrer par statut
    if (filters.status && filters.status !== 'all') {
      filtered = filtered.filter(reg => reg.status === filters.status);
    }

    // Filtrer par recherche
    if (filters.search && filters.search.trim()) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(reg =>
        reg.title.toLowerCase().includes(searchLower) ||
        reg.description.toLowerCase().includes(searchLower)
      );
    }

    return filtered;
  }, [regulations, filters.status, filters.search]);

  const refetch = useCallback(() => {
    // Simuler un rechargement
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
    }, 300);
  }, []);

  return {
    regulations: filteredRegulations,
    loading,
    error: null,
    total: filteredRegulations.length,
    refetch,
  };
};

interface UseRegulationActionsState {
  updating: boolean;
  error: string | null;
  updateStatus: (id: string, status: 'validated' | 'rejected' | 'to-review', comment?: string) => Promise<void>;
}

export const useMockRegulationActions = (onSuccess?: () => void): UseRegulationActionsState => {
  const [updating, setUpdating] = useState(false);

  const updateStatus = useCallback(async (
    _id: string, 
    _status: 'validated' | 'rejected' | 'to-review',
    _comment?: string
  ) => {
    setUpdating(true);

    // Simuler une API call
    await new Promise(resolve => setTimeout(resolve, 800));

    onSuccess?.();
    setUpdating(false);
  }, [onSuccess]);

  return {
    updating,
    error: null,
    updateStatus,
  };
};