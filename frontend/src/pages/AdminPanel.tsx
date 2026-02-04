/**
 * Panel d'Administration
 * 
 * Permet aux administrateurs d'approuver ou rejeter les demandes
 * de création de comptes utilisateurs.
 */

import React, { useState } from 'react';

interface PendingUser {
  id: string;
  fullName: string;
  email: string;
  role: string;
  department?: string;
  requestDate: Date;
  status: 'pending' | 'approved' | 'rejected';
}

interface AdminPanelProps {
  onBack: () => void;
}

// Données mock des utilisateurs en attente
const MOCK_PENDING_USERS: PendingUser[] = [
  {
    id: '1',
    fullName: 'Marie Dupont',
    email: 'marie.dupont@hutchinson.com',
    role: 'Analyste',
    department: 'Supply Chain',
    requestDate: new Date('2026-02-03T14:30:00'),
    status: 'pending',
  },
  {
    id: '2',
    fullName: 'Pierre Martin',
    email: 'pierre.martin@hutchinson.com',
    role: 'Manager',
    department: 'Achats',
    requestDate: new Date('2026-02-02T09:15:00'),
    status: 'pending',
  },
  {
    id: '3',
    fullName: 'Sophie Bernard',
    email: 'sophie.bernard@hutchinson.com',
    role: 'Analyste',
    department: 'Qualité',
    requestDate: new Date('2026-02-01T16:45:00'),
    status: 'pending',
  },
  {
    id: '4',
    fullName: 'Lucas Petit',
    email: 'lucas.petit@hutchinson.com',
    role: 'Viewer',
    department: 'Production',
    requestDate: new Date('2026-01-31T11:20:00'),
    status: 'pending',
  },
  {
    id: '5',
    fullName: 'Emma Leroy',
    email: 'emma.leroy@hutchinson.com',
    role: 'Analyste',
    department: 'R&D',
    requestDate: new Date('2026-01-30T08:00:00'),
    status: 'approved',
  },
  {
    id: '6',
    fullName: 'Thomas Moreau',
    email: 'thomas.moreau@external.com',
    role: 'Viewer',
    department: 'Externe',
    requestDate: new Date('2026-01-29T15:30:00'),
    status: 'rejected',
  },
];

const AdminPanel: React.FC<AdminPanelProps> = ({ onBack }) => {
  const [users, setUsers] = useState<PendingUser[]>(MOCK_PENDING_USERS);
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending');
  const [searchQuery, setSearchQuery] = useState('');
  const [showConfirmModal, setShowConfirmModal] = useState<{ action: 'approve' | 'reject'; user: PendingUser } | null>(null);

  const handleApprove = (userId: string) => {
    setUsers(prev => prev.map(u => 
      u.id === userId ? { ...u, status: 'approved' as const } : u
    ));
    setShowConfirmModal(null);
  };

  const handleReject = (userId: string) => {
    setUsers(prev => prev.map(u => 
      u.id === userId ? { ...u, status: 'rejected' as const } : u
    ));
    setShowConfirmModal(null);
  };

  const filteredUsers = users.filter(u => {
    const matchesFilter = filter === 'all' || u.status === filter;
    const matchesSearch = u.fullName.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         (u.department?.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  const pendingCount = users.filter(u => u.status === 'pending').length;
  const approvedCount = users.filter(u => u.status === 'approved').length;
  const rejectedCount = users.filter(u => u.status === 'rejected').length;

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('fr-FR', { 
      day: '2-digit', 
      month: 'short', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      {/* Header avec flèche retour */}
      <header className="bg-white border-b border-slate-100 px-8 py-4 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto flex items-center gap-4">
          <button 
            onClick={onBack}
            className="p-2 hover:bg-slate-100 rounded-xl transition-colors group"
            title="Retour au dashboard"
          >
            <svg className="w-6 h-6 text-slate-400 group-hover:text-slate-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
            </svg>
          </button>
          <div className="flex-1">
            <h1 className="text-xl font-black text-slate-900 tracking-tight">Administration</h1>
            <p className="text-xs text-slate-400">Gestion des demandes d'accès</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1.5 bg-amber-100 text-amber-700 rounded-full text-sm font-bold">
              {pendingCount} en attente
            </span>
          </div>
        </div>
      </header>

      {/* Contenu principal */}
      <div className="max-w-6xl mx-auto px-8 py-10">
        
        {/* Stats cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <div>
                <p className="text-3xl font-black text-slate-900">{pendingCount}</p>
                <p className="text-sm text-slate-500 font-medium">En attente</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <div>
                <p className="text-3xl font-black text-slate-900">{approvedCount}</p>
                <p className="text-sm text-slate-500 font-medium">Approuvés</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <div>
                <p className="text-3xl font-black text-slate-900">{rejectedCount}</p>
                <p className="text-sm text-slate-500 font-medium">Rejetés</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filtres et recherche */}
        <div className="bg-white rounded-[2rem] p-6 border border-slate-100 shadow-sm mb-6">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            {/* Onglets de filtre */}
            <div className="flex gap-2">
              {[
                { key: 'pending', label: 'En attente', count: pendingCount },
                { key: 'approved', label: 'Approuvés', count: approvedCount },
                { key: 'rejected', label: 'Rejetés', count: rejectedCount },
                { key: 'all', label: 'Tous', count: users.length },
              ].map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setFilter(tab.key as any)}
                  className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${
                    filter === tab.key
                      ? 'bg-slate-900 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {tab.label} ({tab.count})
                </button>
              ))}
            </div>
            
            {/* Barre de recherche */}
            <div className="relative">
              <svg className="w-5 h-5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
              </svg>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Rechercher..."
                className="pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-lime-400 w-64"
              />
            </div>
          </div>
        </div>

        {/* Liste des utilisateurs */}
        <div className="bg-white rounded-[2rem] border border-slate-100 shadow-sm overflow-hidden">
          {filteredUsers.length === 0 ? (
            <div className="p-12 text-center">
              <svg className="w-16 h-16 mx-auto text-slate-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
              </svg>
              <p className="text-slate-400 font-medium">Aucune demande trouvée</p>
              <p className="text-slate-300 text-sm mt-1">Modifiez vos filtres ou votre recherche</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {filteredUsers.map(user => (
                <div key={user.id} className="p-6 hover:bg-slate-50 transition-colors">
                  <div className="flex items-center justify-between gap-4">
                    {/* Info utilisateur */}
                    <div className="flex items-center gap-4 flex-1">
                      <div className="w-12 h-12 bg-gradient-to-br from-slate-700 to-slate-900 rounded-xl flex items-center justify-center text-white font-bold text-lg">
                        {user.fullName.split(' ').map(n => n[0]).join('')}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-bold text-slate-900 truncate">{user.fullName}</h3>
                        <p className="text-sm text-slate-500 truncate">{user.email}</p>
                      </div>
                    </div>

                    {/* Détails */}
                    <div className="hidden md:flex items-center gap-6 text-sm">
                      <div className="text-center">
                        <p className="text-slate-400 text-xs uppercase font-bold">Rôle</p>
                        <p className="text-slate-700 font-medium">{user.role}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-slate-400 text-xs uppercase font-bold">Département</p>
                        <p className="text-slate-700 font-medium">{user.department || '-'}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-slate-400 text-xs uppercase font-bold">Date</p>
                        <p className="text-slate-700 font-medium whitespace-nowrap">{formatDate(user.requestDate)}</p>
                      </div>
                    </div>

                    {/* Statut et actions */}
                    <div className="flex items-center gap-3">
                      {user.status === 'pending' ? (
                        <>
                          <button
                            onClick={() => setShowConfirmModal({ action: 'approve', user })}
                            className="px-4 py-2 bg-emerald-500 text-white rounded-xl font-bold text-sm hover:bg-emerald-600 transition-colors flex items-center gap-2"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Approuver
                          </button>
                          <button
                            onClick={() => setShowConfirmModal({ action: 'reject', user })}
                            className="px-4 py-2 bg-red-100 text-red-600 rounded-xl font-bold text-sm hover:bg-red-200 transition-colors flex items-center gap-2"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                            Rejeter
                          </button>
                        </>
                      ) : (
                        <span className={`px-4 py-2 rounded-xl font-bold text-sm ${
                          user.status === 'approved' 
                            ? 'bg-emerald-100 text-emerald-700' 
                            : 'bg-red-100 text-red-700'
                        }`}>
                          {user.status === 'approved' ? '✓ Approuvé' : '✗ Rejeté'}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modal de confirmation */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => setShowConfirmModal(null)}>
          <div 
            className="bg-white rounded-3xl shadow-2xl max-w-md w-full mx-4 overflow-hidden"
            onClick={e => e.stopPropagation()}
          >
            <div className={`p-6 ${showConfirmModal.action === 'approve' ? 'bg-emerald-500' : 'bg-red-500'}`}>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                  {showConfirmModal.action === 'approve' ? (
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                    </svg>
                  ) : (
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                  )}
                </div>
                <div>
                  <h2 className="text-xl font-black text-white">
                    {showConfirmModal.action === 'approve' ? 'Approuver l\'accès' : 'Rejeter la demande'}
                  </h2>
                  <p className="text-white/80 text-sm">{showConfirmModal.user.fullName}</p>
                </div>
              </div>
            </div>
            
            <div className="p-6">
              <p className="text-slate-600 mb-6">
                {showConfirmModal.action === 'approve' 
                  ? `Voulez-vous accorder l'accès à ${showConfirmModal.user.email} ? Cette personne pourra se connecter à la plateforme.`
                  : `Voulez-vous rejeter la demande de ${showConfirmModal.user.email} ? Cette personne ne pourra pas accéder à la plateforme.`
                }
              </p>
              
              <div className="flex gap-3">
                <button
                  onClick={() => setShowConfirmModal(null)}
                  className="flex-1 px-4 py-3 bg-slate-100 text-slate-700 rounded-xl font-bold hover:bg-slate-200 transition-colors"
                >
                  Annuler
                </button>
                <button
                  onClick={() => showConfirmModal.action === 'approve' 
                    ? handleApprove(showConfirmModal.user.id)
                    : handleReject(showConfirmModal.user.id)
                  }
                  className={`flex-1 px-4 py-3 rounded-xl font-bold transition-colors ${
                    showConfirmModal.action === 'approve'
                      ? 'bg-emerald-500 text-white hover:bg-emerald-600'
                      : 'bg-red-500 text-white hover:bg-red-600'
                  }`}
                >
                  Confirmer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPanel;
