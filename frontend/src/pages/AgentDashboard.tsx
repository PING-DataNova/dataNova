import React, { useState } from 'react';
import { User } from '../types';
import { apiCall } from '../services/api';

interface AgentDashboardProps {
  user: User;
  onNavigate: (page: 'landing' | 'login' | 'register' | 'dashboard' | 'agent') => void;
}

const AgentDashboard: React.FC<AgentDashboardProps> = ({ user: _user, onNavigate }) => {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center">
      <div className="max-w-2xl w-full p-10 bg-white rounded-3xl shadow-lg text-center">
        <h2 className="text-2xl font-black text-slate-900 mb-4">Agent d'analyse</h2>
        <p className="text-sm text-slate-500 mb-8">Lancer notre agent pour démarrer une analyse automatique sur vos dossiers et réglementations.</p>

        <button
          onClick={async () => {
            try {
              setRunning(true);
              setResult(null);
              const resp = await apiCall('/pipeline/agent1/trigger', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keyword: 'CBAM' })
              });
              setResult(resp.message || 'Agent démarré');
            } catch (err: any) {
              setResult('Erreur démarrage agent: ' + (err.message || String(err)));
            } finally {
              setRunning(false);
            }
          }}
          className="w-full px-8 py-6 rounded-full bg-lime-400 text-slate-950 font-black text-lg uppercase tracking-widest hover:bg-white hover:scale-105 transition-all shadow-[0_0_30px_rgba(163,230,53,0.3)]"
        >
          {running ? 'Démarrage...' : "Lancer l'agent"}
        </button>

        {result && <p className="mt-4 text-sm text-slate-600">{result}</p>}

        <div className="mt-6">
          <button onClick={() => onNavigate('dashboard')} className="text-sm text-slate-500 hover:text-slate-900">Retour au tableau de bord</button>
        </div>
      </div>
    </div>
  );
};

export default AgentDashboard;

