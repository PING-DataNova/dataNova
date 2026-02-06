import React, { useState } from 'react';
import { RiskDetailResponse, AffectedEntity } from '../services/impactsService';
import jsPDF from 'jspdf';

interface RiskDetailModalProps {
  risk: RiskDetailResponse | null;
  isLoading: boolean;
  onClose: () => void;
}

interface ParsedRecommendation {
  id: number;
  title: string;
  urgency: string;
  timeline: string;
  owner: string;
  budget_eur: number;
  context: string;
  risk_if_no_action: string;
  concrete_actions: string;
  expected_impact: string;
  roi: string;
  priority_score: number;
}

const RiskDetailModal: React.FC<RiskDetailModalProps> = ({ risk, isLoading, onClose }) => {
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);

  if (!risk && !isLoading) return null;

  const getRiskLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'critique':
        return 'bg-red-500 text-white';
      case 'eleve':
      case 'élevé':
      case 'fort':
        return 'bg-orange-500 text-white';
      case 'moyen':
        return 'bg-yellow-500 text-white';
      default:
        return 'bg-green-500 text-white';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-red-600';
    if (score >= 50) return 'text-orange-600';
    if (score >= 25) return 'text-yellow-600';
    return 'text-green-600';
  };

  const formatBudget = (budget: number): string => {
    if (budget >= 1000000) return `${(budget / 1000000).toFixed(1)}M€`;
    if (budget >= 1000) return `${(budget / 1000).toFixed(0)}k€`;
    return `${budget}€`;
  };

  // Parse les recommandations JSON - supporte ancien et nouveau format climatique
  const parseRecommendations = (recommendations: string): ParsedRecommendation[] => {
    if (!recommendations || typeof recommendations !== 'string') return [];
    
    // Essayer plusieurs méthodes de parsing
    let parsed: unknown[] | null = null;
    
    // Méthode 1: JSON direct
    try {
      const result = JSON.parse(recommendations);
      if (Array.isArray(result)) parsed = result;
    } catch {
      // Méthode 2: Remplacer les simple quotes
      try {
        const cleaned = recommendations.replace(/'/g, '"');
        const result = JSON.parse(cleaned);
        if (Array.isArray(result)) parsed = result;
      } catch {
        // Continue avec extraction regex
      }
    }
    
    // Si le parsing JSON a réussi
    if (parsed && Array.isArray(parsed) && parsed.length > 0) {
      return parsed.map((item: unknown, idx: number) => {
        const rec = item as Record<string, unknown>;
        
        // Format climatique: action, priority, deadline, rationale
        if ('action' in rec) {
          const priorityStr = String(rec.priority || '').toLowerCase();
          return {
            id: idx + 1,
            title: String(rec.action || `Action ${idx + 1}`), // L'action EST le titre
            urgency: priorityStr === 'critique' ? 'CRITIQUE' : 
                     priorityStr === 'haute' ? 'HAUTE' : 
                     priorityStr === 'moyenne' ? 'MOYENNE' : 'NORMALE',
            timeline: String(rec.deadline || ''),
            owner: '', 
            budget_eur: 0,
            context: String(rec.rationale || ''), // La justification comme contexte
            risk_if_no_action: '',
            concrete_actions: String(rec.action || ''),
            expected_impact: String(rec.rationale || ''),
            roi: '',
            priority_score: priorityStr === 'critique' ? 95 : 
                            priorityStr === 'haute' ? 75 : 
                            priorityStr === 'moyenne' ? 50 : 30
          };
        }
        
        // Format original avec id, title, urgency...
        return {
          id: Number(rec.id) || idx + 1,
          title: String(rec.title || ''),
          urgency: String(rec.urgency || 'MEDIUM'),
          timeline: String(rec.timeline || ''),
          owner: String(rec.owner || ''),
          budget_eur: Number(rec.budget_eur) || 0,
          context: String(rec.context || ''),
          risk_if_no_action: String(rec.risk_if_no_action || ''),
          concrete_actions: String(rec.concrete_actions || ''),
          expected_impact: String(rec.expected_impact || ''),
          roi: String(rec.roi || ''),
          priority_score: Number(rec.priority_score) || 0
        };
      });
    }
    
    // Méthode 3: Extraction regex pour format non-JSON
    const items: ParsedRecommendation[] = [];
    const regex = /\{[^{}]*(?:'id'|"id"):\s*(\d+)[^{}]*\}/g;
    let match;
    
    while ((match = regex.exec(recommendations)) !== null) {
      try {
        const jsonStr = match[0]
          .replace(/'/g, '"')
          .replace(/(\w+):/g, '"$1":')
          .replace(/""(\w+)"":/g, '"$1":');
        const item = JSON.parse(jsonStr) as Record<string, unknown>;
        items.push({
          id: Number(item.id) || items.length + 1,
          title: String(item.title || ''),
          urgency: String(item.urgency || 'MEDIUM'),
          timeline: String(item.timeline || ''),
          owner: String(item.owner || ''),
          budget_eur: Number(item.budget_eur) || 0,
          context: String(item.context || ''),
          risk_if_no_action: String(item.risk_if_no_action || ''),
          concrete_actions: String(item.concrete_actions || ''),
          expected_impact: String(item.expected_impact || ''),
          roi: String(item.roi || ''),
          priority_score: Number(item.priority_score) || 0
        });
      } catch {
        // Ignorer les items mal formés
      }
    }
    
    return items;
  };

  // Parse la description pour extraire les sections
  const parseDescription = (description: string) => {
    const sections: { title: string; content: string; icon: string }[] = [];
    
    // Extraire le résumé global
    const globalMatch = description.match(/1\.\s*ÉVALUATION DU RISQUE GLOBAL\s*[-=]+\s*([\s\S]*?)(?=---|\d\.\s*[A-Z]|$)/);
    if (globalMatch) {
      const content = globalMatch[1]
        .replace(/[-=]+/g, '')
        .trim();
      sections.push({ title: 'Évaluation Globale', content, icon: '' });
    }
    
    // Extraire les sites
    const sitesMatch = description.match(/2\.\s*SITES HUTCHINSON AFFECTÉS[^-]*[-=]+\s*([\s\S]*?)(?=---|\d\.\s*[A-Z]|$)/);
    if (sitesMatch) {
      const sitesContent = sitesMatch[1].replace(/[-=]+/g, '').trim();
      const siteCount = (sitesContent.match(/•/g) || []).length;
      sections.push({ 
        title: `Sites Hutchinson Affectés (${siteCount})`, 
        content: sitesContent, 
        icon: '' 
      });
    }
    
    // Extraire les fournisseurs
    const suppliersMatch = description.match(/3\.\s*FOURNISSEURS AFFECTÉS[^-]*[-=]+\s*([\s\S]*?)(?=---|\d\.\s*[A-Z]|$)/);
    if (suppliersMatch) {
      const suppliersContent = suppliersMatch[1].replace(/[-=]+/g, '').trim();
      const supplierCount = (suppliersContent.match(/•/g) || []).length;
      sections.push({ 
        title: `Fournisseurs Affectés (${supplierCount})`, 
        content: suppliersContent, 
        icon: '' 
      });
    }
    
    // Extraire les risques climatiques
    const weatherMatch = description.match(/4\.\s*ANALYSE DES RISQUES CLIMATIQUES[^-]*[-=]+\s*([\s\S]*?)(?=---|\d\.\s*[A-Z]|$)/);
    if (weatherMatch) {
      sections.push({ 
        title: 'Risques Climatiques', 
        content: weatherMatch[1].replace(/[-=]+/g, '').trim(), 
        icon: '' 
      });
    }
    
    // Extraire l'analyse de criticité
    const criticalMatch = description.match(/5\.\s*ANALYSE DE CRITICITÉ\s*[-=]+\s*([\s\S]*?)(?=[-=]{5,}|FIN DU|$)/);
    if (criticalMatch) {
      sections.push({ 
        title: 'Analyse de Criticité', 
        content: criticalMatch[1].replace(/[-=]+/g, '').trim(), 
        icon: '' 
      });
    }
    
    return sections;
  };

  // Fonction de téléchargement PDF professionnel
  const handleDownloadPdf = async () => {
    if (!risk) return;
    
    setIsGeneratingPdf(true);
    try {
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pageWidth = 210;
      const pageHeight = 297;
      const margin = 20;
      const contentWidth = pageWidth - 2 * margin;
      let y = margin;
      
      // Couleurs
      const primaryColor: [number, number, number] = [30, 41, 59]; // slate-800
      const accentColor: [number, number, number] = [220, 38, 38]; // red-600
      const grayColor: [number, number, number] = [100, 116, 139]; // slate-500
      const lightGray: [number, number, number] = [241, 245, 249]; // slate-100
      
      // Helper pour vérifier si on a besoin d'une nouvelle page
      const checkNewPage = (neededHeight: number) => {
        if (y + neededHeight > pageHeight - margin) {
          pdf.addPage();
          y = margin;
          return true;
        }
        return false;
      };
      
      // Helper pour wrapper le texte
      const wrapText = (text: string, maxWidth: number, fontSize: number): string[] => {
        pdf.setFontSize(fontSize);
        const words = text.split(' ');
        const lines: string[] = [];
        let currentLine = '';
        
        words.forEach(word => {
          const testLine = currentLine ? `${currentLine} ${word}` : word;
          const testWidth = pdf.getTextWidth(testLine);
          if (testWidth > maxWidth && currentLine) {
            lines.push(currentLine);
            currentLine = word;
          } else {
            currentLine = testLine;
          }
        });
        if (currentLine) lines.push(currentLine);
        return lines;
      };

      // ====== EN-TÊTE ======
      // Bandeau supérieur
      pdf.setFillColor(...primaryColor);
      pdf.rect(0, 0, pageWidth, 45, 'F');
      
      // Logo/Titre
      pdf.setTextColor(255, 255, 255);
      pdf.setFontSize(10);
      pdf.setFont('helvetica', 'normal');
      pdf.text('DATANOVA', margin, 12);
      pdf.setFontSize(8);
      pdf.text('Rapport d\'Analyse de Risque Reglementaire', margin, 17);
      
      // Date
      const dateStr = new Date().toLocaleDateString('fr-FR', { 
        day: '2-digit', month: 'long', year: 'numeric' 
      });
      pdf.setFontSize(9);
      pdf.text(dateStr, pageWidth - margin - pdf.getTextWidth(dateStr), 12);
      
      // Titre du règlement
      pdf.setFontSize(14);
      pdf.setFont('helvetica', 'bold');
      const titleLines = wrapText(risk.regulation_title, contentWidth, 14);
      let titleY = 28;
      titleLines.forEach(line => {
        pdf.text(line, margin, titleY);
        titleY += 6;
      });
      
      y = 55;
      
      // ====== RÉSUMÉ EXÉCUTIF ======
      pdf.setFillColor(...lightGray);
      pdf.rect(margin, y, contentWidth, 35, 'F');
      pdf.setDrawColor(200, 200, 200);
      pdf.rect(margin, y, contentWidth, 35, 'S');
      
      y += 8;
      pdf.setTextColor(...primaryColor);
      pdf.setFontSize(12);
      pdf.setFont('helvetica', 'bold');
      pdf.text('RESUME EXECUTIF', margin + 5, y);
      
      y += 10;
      pdf.setFontSize(10);
      pdf.setFont('helvetica', 'normal');
      
      // Niveau de risque avec couleur
      const riskLevel = risk.risk_level.toUpperCase();
      pdf.setTextColor(...grayColor);
      pdf.text('Niveau de risque:', margin + 5, y);
      if (riskLevel === 'CRITIQUE') {
        pdf.setTextColor(220, 38, 38);
      } else if (riskLevel === 'FORT' || riskLevel === 'ELEVE') {
        pdf.setTextColor(234, 88, 12);
      } else {
        pdf.setTextColor(202, 138, 4);
      }
      pdf.setFont('helvetica', 'bold');
      pdf.text(riskLevel, margin + 45, y);
      
      // Score
      pdf.setTextColor(...grayColor);
      pdf.setFont('helvetica', 'normal');
      pdf.text('Score global:', margin + 85, y);
      pdf.setTextColor(...accentColor);
      pdf.setFont('helvetica', 'bold');
      pdf.text(`${risk.risk_score.toFixed(1)}/100`, margin + 115, y);
      
      y += 8;
      // Extraire métriques de la description
      const desc = risk.impacts_description || '';
      const severityMatch = desc.match(/Score de sévérité:\s*([\d.]+)/);
      const urgencyMatch = desc.match(/Score d'urgence:\s*([\d.]+)/);
      const interruptionMatch = desc.match(/Score d'interruption business:\s*([\d.]+)/);
      
      pdf.setTextColor(...grayColor);
      pdf.setFont('helvetica', 'normal');
      if (severityMatch) {
        pdf.text(`Severite: ${parseFloat(severityMatch[1]).toFixed(0)}/100`, margin + 5, y);
      }
      if (urgencyMatch) {
        pdf.text(`Urgence: ${parseFloat(urgencyMatch[1]).toFixed(0)}/100`, margin + 55, y);
      }
      if (interruptionMatch) {
        pdf.text(`Interruption: ${parseFloat(interruptionMatch[1]).toFixed(0)}/100`, margin + 105, y);
      }
      
      y += 20;
      
      // ====== SITES AFFECTÉS ======
      if (risk.affected_sites && risk.affected_sites.length > 0) {
        checkNewPage(50);
        
        pdf.setFillColor(...primaryColor);
        pdf.rect(margin, y, contentWidth, 8, 'F');
        pdf.setTextColor(255, 255, 255);
        pdf.setFontSize(11);
        pdf.setFont('helvetica', 'bold');
        pdf.text(`SITES HUTCHINSON AFFECTES (${risk.affected_sites.length})`, margin + 3, y + 5.5);
        y += 12;
        
        // En-tête tableau
        pdf.setFillColor(248, 250, 252);
        pdf.rect(margin, y, contentWidth, 7, 'F');
        pdf.setTextColor(...grayColor);
        pdf.setFontSize(8);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Site', margin + 3, y + 5);
        pdf.text('Score Risque', margin + 90, y + 5);
        pdf.text('Probabilite', margin + 125, y + 5);
        pdf.text('Duree', margin + 155, y + 5);
        y += 9;
        
        // Lignes
        pdf.setFont('helvetica', 'normal');
        risk.affected_sites.slice(0, 10).forEach((site, idx) => {
          checkNewPage(8);
          
          if (idx % 2 === 0) {
            pdf.setFillColor(255, 255, 255);
          } else {
            pdf.setFillColor(248, 250, 252);
          }
          pdf.rect(margin, y - 1, contentWidth, 7, 'F');
          
          pdf.setTextColor(...primaryColor);
          pdf.setFontSize(8);
          const siteName = site.name.length > 35 ? site.name.substring(0, 35) + '...' : site.name;
          pdf.text(siteName, margin + 3, y + 4);
          
          // Score avec couleur
          const score = site.risk_score;
          if (score >= 75) pdf.setTextColor(220, 38, 38);
          else if (score >= 50) pdf.setTextColor(234, 88, 12);
          else pdf.setTextColor(34, 197, 94);
          pdf.text(`${score.toFixed(1)}/100`, margin + 90, y + 4);
          
          // Extraire probabilité et durée du reasoning
          pdf.setTextColor(...grayColor);
          const probMatch = site.reasoning?.match(/(\d+)%/);
          const durationMatch = site.reasoning?.match(/(\d+)\s*jours/);
          pdf.text(probMatch ? `${probMatch[1]}%` : '-', margin + 125, y + 4);
          pdf.text(durationMatch ? `${durationMatch[1]}j` : '-', margin + 155, y + 4);
          
          y += 7;
        });
        
        y += 8;
      }
      
      // ====== FOURNISSEURS AFFECTÉS ======
      if (risk.affected_suppliers && risk.affected_suppliers.length > 0) {
        checkNewPage(50);
        
        pdf.setFillColor(...primaryColor);
        pdf.rect(margin, y, contentWidth, 8, 'F');
        pdf.setTextColor(255, 255, 255);
        pdf.setFontSize(11);
        pdf.setFont('helvetica', 'bold');
        pdf.text(`FOURNISSEURS AFFECTES (${risk.affected_suppliers.length})`, margin + 3, y + 5.5);
        y += 12;
        
        // En-tête tableau
        pdf.setFillColor(248, 250, 252);
        pdf.rect(margin, y, contentWidth, 7, 'F');
        pdf.setTextColor(...grayColor);
        pdf.setFontSize(8);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Fournisseur', margin + 3, y + 5);
        pdf.text('Score Risque', margin + 90, y + 5);
        pdf.text('Probabilite', margin + 125, y + 5);
        pdf.text('Duree', margin + 155, y + 5);
        y += 9;
        
        // Lignes
        pdf.setFont('helvetica', 'normal');
        risk.affected_suppliers.slice(0, 10).forEach((supplier, idx) => {
          checkNewPage(8);
          
          if (idx % 2 === 0) {
            pdf.setFillColor(255, 255, 255);
          } else {
            pdf.setFillColor(248, 250, 252);
          }
          pdf.rect(margin, y - 1, contentWidth, 7, 'F');
          
          pdf.setTextColor(...primaryColor);
          pdf.setFontSize(8);
          const supplierName = supplier.name.length > 35 ? supplier.name.substring(0, 35) + '...' : supplier.name;
          pdf.text(supplierName, margin + 3, y + 4);
          
          // Score avec couleur
          const score = supplier.risk_score;
          if (score >= 75) pdf.setTextColor(220, 38, 38);
          else if (score >= 50) pdf.setTextColor(234, 88, 12);
          else pdf.setTextColor(34, 197, 94);
          pdf.text(`${score.toFixed(1)}/100`, margin + 90, y + 4);
          
          // Extraire probabilité et durée
          pdf.setTextColor(...grayColor);
          const probMatch = supplier.reasoning?.match(/(\d+)%/);
          const durationMatch = supplier.reasoning?.match(/(\d+)\s*jours/);
          pdf.text(probMatch ? `${probMatch[1]}%` : '-', margin + 125, y + 4);
          pdf.text(durationMatch ? `${durationMatch[1]}j` : '-', margin + 155, y + 4);
          
          y += 7;
        });
        
        y += 8;
      }
      
      // ====== RISQUES MÉTÉOROLOGIQUES ======
      if (risk.weather_risk_summary) {
        checkNewPage(35);
        
        pdf.setFillColor(...primaryColor);
        pdf.rect(margin, y, contentWidth, 8, 'F');
        pdf.setTextColor(255, 255, 255);
        pdf.setFontSize(11);
        pdf.setFont('helvetica', 'bold');
        pdf.text('RISQUES METEOROLOGIQUES', margin + 3, y + 5.5);
        y += 12;
        
        pdf.setTextColor(...primaryColor);
        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');
        pdf.text(`Total alertes: ${risk.weather_risk_summary.total_alerts}`, margin + 5, y);
        pdf.text(`Entites concernees: ${risk.weather_risk_summary.entities_with_alerts}`, margin + 60, y);
        pdf.text(`Severite max: ${risk.weather_risk_summary.max_severity.toUpperCase()}`, margin + 120, y);
        
        y += 15;
      }
      
      // ====== RECOMMANDATIONS ======
      if (risk.recommendations) {
        checkNewPage(40);
        
        pdf.setFillColor(...primaryColor);
        pdf.rect(margin, y, contentWidth, 8, 'F');
        pdf.setTextColor(255, 255, 255);
        pdf.setFontSize(11);
        pdf.setFont('helvetica', 'bold');
        pdf.text('RECOMMANDATIONS', margin + 3, y + 5.5);
        y += 14;
        
        const parsedRecs = parseRecommendations(risk.recommendations);
        
        parsedRecs.slice(0, 5).forEach((rec, idx) => {
          checkNewPage(35);
          
          // Cadre recommandation
          pdf.setDrawColor(200, 200, 200);
          pdf.setFillColor(255, 255, 255);
          pdf.roundedRect(margin, y, contentWidth, 28, 2, 2, 'FD');
          
          // Numéro et titre
          pdf.setTextColor(...primaryColor);
          pdf.setFontSize(10);
          pdf.setFont('helvetica', 'bold');
          const recTitle = rec.title.length > 60 ? rec.title.substring(0, 60) + '...' : rec.title;
          pdf.text(`${idx + 1}. ${recTitle}`, margin + 4, y + 6);
          
          // Badge urgence
          const urgencyText = rec.urgency || 'MEDIUM';
          let urgencyColor: [number, number, number] = [202, 138, 4];
          if (urgencyText === 'IMMEDIATE') urgencyColor = [220, 38, 38];
          else if (urgencyText === 'HIGH') urgencyColor = [234, 88, 12];
          
          pdf.setFillColor(...urgencyColor);
          const urgencyWidth = pdf.getTextWidth(urgencyText) + 6;
          pdf.roundedRect(pageWidth - margin - urgencyWidth - 4, y + 2, urgencyWidth, 6, 1, 1, 'F');
          pdf.setTextColor(255, 255, 255);
          pdf.setFontSize(7);
          pdf.text(urgencyText, pageWidth - margin - urgencyWidth - 1, y + 6);
          
          // Détails
          pdf.setTextColor(...grayColor);
          pdf.setFontSize(8);
          pdf.setFont('helvetica', 'normal');
          
          y += 12;
          if (rec.timeline) pdf.text(`Delai: ${rec.timeline}`, margin + 4, y);
          if (rec.budget_eur) pdf.text(`Budget: ${formatBudget(rec.budget_eur)}`, margin + 45, y);
          if (rec.owner) pdf.text(`Responsable: ${rec.owner.substring(0, 25)}`, margin + 90, y);
          
          y += 6;
          if (rec.roi) {
            pdf.setTextColor(34, 197, 94);
            pdf.text(`ROI: ${rec.roi}`, margin + 4, y);
          }
          if (rec.priority_score) {
            pdf.setTextColor(...grayColor);
            pdf.text(`Priorite: ${rec.priority_score}/100`, margin + 45, y);
          }
          
          y += 14;
        });
      }
      
      // ====== PIED DE PAGE ======
      const totalPages = pdf.getNumberOfPages();
      for (let i = 1; i <= totalPages; i++) {
        pdf.setPage(i);
        
        // Ligne de séparation
        pdf.setDrawColor(200, 200, 200);
        pdf.line(margin, pageHeight - 15, pageWidth - margin, pageHeight - 15);
        
        // Texte pied de page
        pdf.setTextColor(...grayColor);
        pdf.setFontSize(8);
        pdf.setFont('helvetica', 'normal');
        pdf.text('DataNova - Plateforme d\'Intelligence Reglementaire', margin, pageHeight - 10);
        pdf.text(`Page ${i}/${totalPages}`, pageWidth - margin - 20, pageHeight - 10);
        pdf.text(`Genere le ${dateStr}`, pageWidth / 2 - 15, pageHeight - 10);
      }
      
      // Sauvegarde
      const fileName = `Rapport_Risque_${risk.regulation_title.substring(0, 25).replace(/[^a-zA-Z0-9]/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`;
      pdf.save(fileName);
      
    } catch (error) {
      console.error('Erreur generation PDF:', error);
      setPdfError('Erreur lors de la generation du PDF. Veuillez reessayer.');
      setTimeout(() => setPdfError(null), 5000);
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  // Render une recommandation formatée
  const renderRecommendation = (rec: ParsedRecommendation) => {
    // Couleurs pour les badges de priorité
    const getPriorityStyle = (urgency: string) => {
      const u = urgency.toUpperCase();
      if (u === 'CRITIQUE' || u === 'IMMEDIATE') return 'bg-red-100 text-red-700 border-red-300';
      if (u === 'HAUTE' || u === 'HIGH') return 'bg-orange-100 text-orange-700 border-orange-300';
      if (u === 'MOYENNE' || u === 'MEDIUM') return 'bg-yellow-100 text-yellow-700 border-yellow-300';
      return 'bg-green-100 text-green-700 border-green-300';
    };

    return (
      <div key={rec.id} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
        <div className="flex items-start justify-between gap-3 mb-3">
          <h4 className="font-bold text-slate-800 text-sm leading-tight flex-1">{rec.title}</h4>
          <span className={`px-2 py-1 rounded-full text-xs font-bold whitespace-nowrap border ${getPriorityStyle(rec.urgency)}`}>
            {rec.urgency}
          </span>
        </div>
        
        {rec.context && (
          <p className="text-slate-600 text-sm mb-3">{rec.context}</p>
        )}
        
        <div className="flex flex-wrap gap-2 text-xs">
          {rec.timeline && (
            <div className="flex items-center gap-1 text-slate-500 bg-slate-100 px-2 py-1 rounded">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span>{rec.timeline}</span>
            </div>
          )}
          {rec.budget_eur > 0 && (
            <div className="flex items-center gap-1 text-emerald-600 bg-emerald-50 px-2 py-1 rounded">
              <span className="font-medium">{formatBudget(rec.budget_eur)}</span>
            </div>
          )}
          {rec.owner && (
            <div className="flex items-center gap-1 text-blue-600 bg-blue-50 px-2 py-1 rounded">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              <span>{rec.owner}</span>
            </div>
          )}
        </div>
        
        {rec.priority_score > 0 && (
          <div className="mt-3 flex items-center gap-2">
            <span className="text-xs text-slate-400">Priorité:</span>
            <div className="flex-1 bg-slate-100 rounded-full h-2">
              <div 
                className={`h-2 rounded-full ${rec.priority_score >= 90 ? 'bg-red-500' : rec.priority_score >= 70 ? 'bg-orange-500' : 'bg-yellow-500'}`}
                style={{ width: `${rec.priority_score}%` }}
              />
            </div>
            <span className="text-xs font-bold text-slate-600">{rec.priority_score}</span>
          </div>
        )}
      </div>
    );
  };

  // Fonction pour extraire les informations clés du reasoning
  const extractKeyInfo = (reasoning: string) => {
    const lines = reasoning.split('\n').filter(l => l.trim());
    const keyInfo: { label: string; value: string }[] = [];
    
    // Chercher les infos importantes
    lines.forEach(line => {
      if (line.includes('PROBABILITÉ D\'IMPACT:')) {
        const match = line.match(/(\d+)%/);
        if (match) keyInfo.push({ label: 'Probabilité', value: match[1] + '%' });
      }
      if (line.includes('DURÉE ESTIMÉE:')) {
        const match = line.match(/(\d+)\s*jours/);
        if (match) keyInfo.push({ label: 'Durée', value: match[1] + ' jours' });
      }
      if (line.includes('Impact financier estimé:')) {
        const match = line.match(/([\d,\.]+[€$])|(\d+[,\.]*\d*\s*(M€|k€|EUR))/);
        if (match) keyInfo.push({ label: 'Impact financier', value: match[0] });
      }
    });
    
    return keyInfo;
  };

  // Extraire la raison d'impact à partir du reasoning
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const extractImpactReason = (reasoning: string | undefined, _type: 'site' | 'supplier'): string | null => {
    if (!reasoning) return null;
    
    // Chercher des phrases clés expliquant pourquoi l'entité est impactée
    const reasonPatterns = [
      /(?:impact[ée]?|affect[ée]?|concern[ée]?|touch[ée]?)(?:[^.]*)((?:car|parce que|du fait|en raison)[^.]+)/i,
      /(?:risque|menace|danger)[^.]*:?\s*([^.]+)/i,
      /(?:exposition|vulnerabilit[ée])[^.]*:?\s*([^.]+)/i,
      /RAISON\s*:?\s*([^.\n]+)/i,
      /IMPACT\s*:?\s*([^.\n]+)/i
    ];
    
    for (const pattern of reasonPatterns) {
      const match = reasoning.match(pattern);
      if (match && match[1]) {
        return match[1].trim().substring(0, 120);
      }
    }
    
    // Si pas de pattern trouvé, extraire la première phrase pertinente
    const sentences = reasoning.split(/[.\n]/).filter(s => s.trim().length > 20);
    if (sentences.length > 0) {
      const relevantSentence = sentences.find(s => 
        /risque|impact|affect|climat|meteo|reglementat|fournisseur|production/i.test(s)
      );
      if (relevantSentence) return relevantSentence.trim().substring(0, 120);
    }
    
    return null;
  };

  const renderAffectedEntity = (entity: AffectedEntity, index: number, type: 'site' | 'supplier') => {
    const typeLabel = type === 'site' ? 'S' : 'F';
    const scoreColor = getScoreColor(entity.risk_score);
    const keyInfo = entity.reasoning ? extractKeyInfo(entity.reasoning) : [];
    const impactReason = extractImpactReason(entity.reasoning, type);
    
    return (
      <div key={entity.id || index} className="bg-slate-50 rounded-lg p-3 mb-2 border border-slate-200 hover:border-slate-300 transition-colors">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`text-xs font-bold px-2 py-0.5 rounded ${
              type === 'site' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
            }`}>{typeLabel}</span>
            <h4 className="font-semibold text-slate-800 text-sm">{entity.name}</h4>
          </div>
          <div className="flex items-center gap-2">
            <span className={`font-bold text-sm ${scoreColor}`}>
              {entity.risk_score.toFixed(1)}/100
            </span>
            {entity.business_interruption_score != null && entity.business_interruption_score > 0 && (
              <span className="text-xs text-slate-500 bg-slate-200 px-2 py-0.5 rounded">
                BI: {entity.business_interruption_score.toFixed(0)}%
              </span>
            )}
          </div>
        </div>
        
        {/* Raison de l'impact - NOUVEAU */}
        {impactReason && (
          <div className="mt-2 text-xs text-slate-600 bg-amber-50 border-l-2 border-amber-400 pl-2 py-1 rounded-r">
            <span className="font-medium text-amber-700">Impact:</span> {impactReason}
          </div>
        )}
        
        {keyInfo.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {keyInfo.map((info, idx) => (
              <span key={idx} className="text-xs bg-white px-2 py-1 rounded border border-slate-200">
                <span className="text-slate-500">{info.label}:</span> <span className="font-medium text-slate-700">{info.value}</span>
              </span>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div 
      className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 overflow-y-auto" 
      style={{ zIndex: 9999 }}
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-2xl w-full max-w-3xl shadow-2xl my-4 flex flex-col max-h-[85vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-800 to-slate-700 text-white p-6 relative">
          <button 
            onClick={onClose}
            className="absolute top-4 right-4 w-10 h-10 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          
          {isLoading ? (
            <div className="animate-pulse">
              <div className="h-8 bg-white/20 rounded w-3/4 mb-3"></div>
              <div className="h-4 bg-white/20 rounded w-1/2"></div>
            </div>
          ) : risk && (
            <>
              <div className="flex items-start gap-4">
                <div className="flex-1">
                  <h2 className="text-2xl font-bold mb-2">{risk.regulation_title}</h2>
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className={`px-3 py-1 rounded-full text-sm font-bold ${getRiskLevelColor(risk.risk_level)}`}>
                      {risk.risk_level.toUpperCase()}
                    </span>
                    <span className="text-white/80">
                      Score: <span className="font-bold">{risk.risk_score.toFixed(1)}/100</span>
                    </span>
                    <span className="text-white/60">
                      {new Date(risk.created_at).toLocaleDateString('fr-FR', {
                        day: 'numeric',
                        month: 'long',
                        year: 'numeric'
                      })}
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Content */}
        <div className="overflow-y-auto flex-1 min-h-0">
          {isLoading ? (
            <div className="p-6 space-y-4 animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-full"></div>
              <div className="h-4 bg-slate-200 rounded w-5/6"></div>
              <div className="h-4 bg-slate-200 rounded w-4/6"></div>
              <div className="h-32 bg-slate-200 rounded mt-6"></div>
            </div>
          ) : risk && (
            <div className="p-6 space-y-6">
              {/* Résumé clé en haut */}
              {risk.impacts_description && (
                <section>
                  <h3 className="text-lg font-bold text-slate-800 mb-3 flex items-center gap-2">
                    Synthèse de l'Impact
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                    {/* Extraire les métriques clés */}
                    {(() => {
                      const desc = risk.impacts_description;
                      const scoreMatch = desc.match(/Score de risque 360°:\s*([\d.]+)/);
                      const severityMatch = desc.match(/Score de sévérité:\s*([\d.]+)/);
                      const urgencyMatch = desc.match(/Score d'urgence:\s*([\d.]+)/);
                      const interruptionMatch = desc.match(/Score d'interruption business:\s*([\d.]+)/);
                      
                      return (
                        <>
                          {scoreMatch && (
                            <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-xl p-3 text-center border border-red-200">
                              <div className="text-2xl font-bold text-red-600">{parseFloat(scoreMatch[1]).toFixed(1)}</div>
                              <div className="text-xs text-red-500 font-medium">Score Global</div>
                            </div>
                          )}
                          {severityMatch && (
                            <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-3 text-center border border-orange-200">
                              <div className="text-2xl font-bold text-orange-600">{parseFloat(severityMatch[1]).toFixed(0)}</div>
                              <div className="text-xs text-orange-500 font-medium">Sévérité</div>
                            </div>
                          )}
                          {urgencyMatch && (
                            <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-xl p-3 text-center border border-yellow-200">
                              <div className="text-2xl font-bold text-yellow-600">{parseFloat(urgencyMatch[1]).toFixed(0)}</div>
                              <div className="text-xs text-yellow-600 font-medium">Urgence</div>
                            </div>
                          )}
                          {interruptionMatch && (
                            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-3 text-center border border-purple-200">
                              <div className="text-2xl font-bold text-purple-600">{parseFloat(interruptionMatch[1]).toFixed(0)}</div>
                              <div className="text-xs text-purple-500 font-medium">Interruption</div>
                            </div>
                          )}
                        </>
                      );
                    })()}
                  </div>
                  
                  {/* Sections parsées de la description */}
                  <div className="space-y-3">
                    {parseDescription(risk.impacts_description).map((section, idx) => (
                      <details key={idx} className="bg-slate-50 rounded-lg border border-slate-200 overflow-hidden group">
                        <summary className="px-4 py-3 cursor-pointer font-medium text-slate-700 hover:bg-slate-100 flex items-center gap-2">
                          <span>{section.icon}</span>
                          <span>{section.title}</span>
                          <svg className="w-4 h-4 ml-auto transform transition-transform group-open:rotate-180 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                          </svg>
                        </summary>
                        <div className="px-4 pb-4 text-sm text-slate-600 whitespace-pre-line">
                          {section.content
                            .split('•').filter(s => s.trim())
                            .map((item, i) => (
                              <div key={i} className="py-2 border-b border-slate-100 last:border-0">
                                {item.trim()}
                              </div>
                            ))
                          }
                        </div>
                      </details>
                    ))}
                  </div>
                </section>
              )}

              {/* Impact Supply Chain */}
              {risk.supply_chain_impact && (
                <section className="flex items-center gap-4">
                  <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
                    Impact Supply Chain
                  </h3>
                  <div className={`px-3 py-1 rounded-lg font-bold text-sm ${
                    risk.supply_chain_impact === 'critique' ? 'bg-red-100 text-red-700' :
                    risk.supply_chain_impact === 'elevé' || risk.supply_chain_impact === 'fort' ? 'bg-orange-100 text-orange-700' :
                    'bg-yellow-100 text-yellow-700'
                  }`}>
                    {risk.supply_chain_impact.toUpperCase()}
                  </div>
                </section>
              )}

              {/* Sites et Fournisseurs en 2 colonnes */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Sites Affectés */}
                {risk.affected_sites && risk.affected_sites.length > 0 && (
                  <section>
                    <h3 className="text-base font-bold text-slate-800 mb-2 flex items-center gap-2">
                      Sites Affectés ({risk.affected_sites.length})
                    </h3>
                    <div className="max-h-60 overflow-y-auto pr-1 space-y-1">
                      {risk.affected_sites.map((site, idx) => renderAffectedEntity(site, idx, 'site'))}
                    </div>
                  </section>
                )}

                {/* Fournisseurs Affectés */}
                {risk.affected_suppliers && risk.affected_suppliers.length > 0 && (
                  <section>
                    <h3 className="text-base font-bold text-slate-800 mb-2 flex items-center gap-2">
                      Fournisseurs ({risk.affected_suppliers.length})
                    </h3>
                    <div className="max-h-60 overflow-y-auto pr-1 space-y-1">
                      {risk.affected_suppliers.map((supplier, idx) => renderAffectedEntity(supplier, idx, 'supplier'))}
                    </div>
                  </section>
                )}
              </div>

              {/* Alertes Météo - Version enrichie avec recommandations */}
              {risk.weather_risk_summary && (
                <section>
                  <h3 className="text-base font-bold text-slate-800 mb-2 flex items-center gap-2">
                    <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                    </svg>
                    Risques Meteorologiques
                  </h3>
                  
                  {/* Stats globales */}
                  <div className="bg-gradient-to-r from-blue-50 to-sky-50 rounded-lg p-3 mb-3 border border-blue-100">
                    <div className="flex flex-wrap items-center gap-4 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xl font-bold text-blue-600">{risk.weather_risk_summary.total_alerts}</span>
                        <span className="text-xs text-slate-600">alertes</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xl font-bold text-blue-600">{risk.weather_risk_summary.entities_with_alerts}</span>
                        <span className="text-xs text-slate-600">entites concernees</span>
                      </div>
                      <div className={`px-2 py-1 rounded text-sm font-bold ${
                        risk.weather_risk_summary.max_severity === 'critical' ? 'bg-red-100 text-red-700' :
                        risk.weather_risk_summary.max_severity === 'high' ? 'bg-orange-100 text-orange-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        Severite {risk.weather_risk_summary.max_severity?.toUpperCase()}
                      </div>
                    </div>
                    
                    {risk.weather_risk_summary.alerts_by_type && Object.keys(risk.weather_risk_summary.alerts_by_type).length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(risk.weather_risk_summary.alerts_by_type).map(([type, count]) => (
                          <span key={type} className="px-2 py-0.5 bg-white rounded text-xs text-slate-700 border border-slate-200">
                            {type === 'extreme_heat' && 'Canicule'}
                            {type === 'extreme_cold' && 'Grand froid'}
                            {type === 'strong_wind' && 'Vents forts'}
                            {type === 'storm' && 'Tempete'}
                            {type === 'snow' && 'Neige'}
                            {type === 'heavy_rain' && 'Fortes pluies'}
                            {!['extreme_heat', 'extreme_cold', 'strong_wind', 'storm', 'snow', 'heavy_rain'].includes(type) && type}
                            {' '}: {String(count)}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Recommandations logistiques detaillees */}
                  {risk.weather_risk_summary.logistics_recommendations && 
                   risk.weather_risk_summary.logistics_recommendations.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                        <svg className="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        Actions recommandees ({risk.weather_risk_summary.logistics_recommendations.length})
                      </h4>
                      <div className="max-h-64 overflow-y-auto space-y-2 pr-1">
                        {risk.weather_risk_summary.logistics_recommendations.map((rec: {
                          entity_name: string;
                          entity_type: string;
                          location: string;
                          alert_type: string;
                          severity: string;
                          date: string;
                          value: string;
                          action: string;
                          deadline: string;
                          priority: string;
                        }, idx: number) => (
                          <div 
                            key={idx} 
                            className={`p-3 rounded-lg border-l-4 ${
                              rec.priority === 'critique' ? 'bg-red-50 border-red-500' :
                              rec.priority === 'haute' ? 'bg-orange-50 border-orange-500' :
                              'bg-amber-50 border-amber-400'
                            }`}
                          >
                            <div className="flex items-start justify-between gap-2 mb-1">
                              <div className="flex items-center gap-2">
                                <span className="font-semibold text-sm text-slate-800">
                                  {rec.entity_name}
                                </span>
                                <span className="text-xs text-slate-500">
                                  ({rec.entity_type})
                                </span>
                              </div>
                              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                                rec.priority === 'critique' ? 'bg-red-200 text-red-800' :
                                rec.priority === 'haute' ? 'bg-orange-200 text-orange-800' :
                                'bg-amber-200 text-amber-800'
                              }`}>
                                {rec.priority?.toUpperCase()}
                              </span>
                            </div>
                            
                            <div className="flex items-center gap-2 text-xs text-slate-600 mb-2">
                              <span className="flex items-center gap-1">
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                </svg>
                                {rec.location}
                              </span>
                              <span className="flex items-center gap-1">
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                                {rec.date}
                              </span>
                              <span className="font-medium text-slate-700">
                                {rec.alert_type} {rec.value && `(${rec.value})`}
                              </span>
                            </div>
                            
                            <p className="text-xs text-slate-700 bg-white/60 p-2 rounded">
                              {rec.action}
                            </p>
                            
                            {rec.deadline && (
                              <div className="mt-2 flex items-center gap-1 text-xs font-medium text-slate-600">
                                <svg className="w-3 h-3 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                Echeance: {rec.deadline}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </section>
              )}

              {/* Recommandations - Format cartes - Seulement si pas de logistics_recommendations (pour éviter doublon) */}
              {risk.recommendations && !risk.weather_risk_summary?.logistics_recommendations?.length && (
                <section>
                  <h3 className="text-lg font-bold text-slate-800 mb-3 flex items-center gap-2">
                    Recommandations
                  </h3>
                  {(() => {
                    const parsedRecs = parseRecommendations(risk.recommendations);
                    if (parsedRecs.length > 0) {
                      return (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {parsedRecs.map(rec => renderRecommendation(rec))}
                        </div>
                      );
                    }
                    // Fallback si le parsing échoue
                    return (
                      <div className="bg-green-50 rounded-lg p-4">
                        <ul className="text-slate-700 space-y-2">
                          {risk.recommendations.split('\n').filter(line => line.trim()).map((line, index) => (
                            <li key={index} className="flex items-start gap-2">
                              <span className="text-green-500 mt-1">•</span>
                              <span>{line.replace(/^-\s*/, '')}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    );
                  })()}
                </section>
              )}

              {/* Source */}
              {risk.source_url && (
                <section>
                  <h3 className="text-lg font-bold text-slate-800 mb-3 flex items-center gap-2">
                    Source
                  </h3>
                  <a 
                    href={risk.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 hover:underline break-all"
                  >
                    {risk.source_url}
                  </a>
                  {risk.source_excerpt && (
                    <div className="mt-3 bg-slate-50 rounded-lg p-4 text-sm text-slate-600 italic">
                      "{risk.source_excerpt.substring(0, 300)}..."
                    </div>
                  )}
                </section>
              )}
            </div>
          )}
        </div>

        {/* Footer avec bouton PDF */}
        <div className="border-t border-slate-200 p-4">
          {/* Message d'erreur PDF */}
          {pdfError && (
            <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
              <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {pdfError}
            </div>
          )}
          
          <div className="flex justify-between items-center">
            <button
              onClick={handleDownloadPdf}
              disabled={isGeneratingPdf || !risk}
              className="px-4 py-2 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isGeneratingPdf ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Generation...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>Telecharger PDF</span>
                </>
              )}
            </button>
            
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="px-6 py-2 bg-slate-100 text-slate-700 rounded-lg font-medium hover:bg-slate-200 transition-colors"
              >
                Fermer
              </button>
              {risk?.source_url && (
                <a
                  href={risk.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-6 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors"
                >
                  Voir la source
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskDetailModal;
