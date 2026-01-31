
import React from 'react';
import { RiskData, ImpactLevel } from '../types';

interface RiskTableProps {
  risks: RiskData[];
}

const ImpactBadge: React.FC<{ level: ImpactLevel }> = ({ level }) => {
  const styles = {
    faible: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    moyen: 'bg-amber-50 text-amber-600 border-amber-100',
    eleve: 'bg-orange-50 text-orange-600 border-orange-100',
    critique: 'bg-red-50 text-red-600 border-red-100',
  };

  return (
    <span className={`px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest border ${styles[level]}`}>
      {level}
    </span>
  );
};

const RiskTable: React.FC<RiskTableProps> = ({ risks }) => {
  return (
    <div className="bg-white rounded-[2.5rem] shadow-sm border border-slate-100 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/50 border-b border-slate-100">
              <th className="p-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">Identification</th>
              <th className="p-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">Gravité</th>
              <th className="p-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">Modalité</th>
              <th className="p-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">Échéance</th>
              <th className="p-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">Raisonnement Stratégique</th>
              <th className="p-6 text-[10px] font-black text-slate-400 uppercase tracking-widest text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {risks.map((risk) => (
              <tr key={risk.id} className="hover:bg-slate-50/30 transition-all duration-300 group">
                <td className="p-6">
                  <div className="flex flex-col">
                    <span className="font-black text-slate-900 text-sm tracking-tight mb-1">{risk.risk_main}</span>
                    <span className="text-[10px] text-slate-400 font-medium truncate max-w-[200px]" title={risk.risk_details}>{risk.risk_details}</span>
                  </div>
                </td>
                <td className="p-6">
                  <ImpactBadge level={risk.impact_level} />
                </td>
                <td className="p-6">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-slate-200 rounded-full"></div>
                    <span className="text-xs font-bold text-slate-600 uppercase tracking-tighter">{risk.modality}</span>
                  </div>
                </td>
                <td className="p-6 font-black text-xs text-slate-900 tracking-widest">
                  {risk.deadline}
                </td>
                <td className="p-6">
                  <p className="text-xs text-slate-500 font-medium leading-relaxed max-w-sm italic">"{risk.llm_reasoning}"</p>
                </td>
                <td className="p-6 text-right">
                  <button className="p-2 rounded-xl bg-slate-50 text-slate-400 hover:bg-slate-900 hover:text-white transition-all">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"/></svg>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="p-6 bg-slate-50/30 flex justify-between items-center text-[10px] font-black uppercase tracking-widest text-slate-400">
        <span>Affichage de {risks.length} entrées stratégiques</span>
        <div className="flex space-x-4">
           <button className="hover:text-slate-900 transition-colors">Précédent</button>
           <button className="hover:text-slate-900 transition-colors">Suivant</button>
        </div>
      </div>
    </div>
  );
};

export default RiskTable;
