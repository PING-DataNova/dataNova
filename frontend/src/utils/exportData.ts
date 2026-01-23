/**
 * Utilitaires pour exporter les données validées
 */

import { getValidatedRegulationsJSON, exportValidatedRegulationsJSON } from '../data/mockData';

/**
 * Télécharge les données validées en fichier JSON
 */
export const downloadValidatedRegulationsJSON = () => {
  const jsonString = exportValidatedRegulationsJSON();
  const blob = new Blob([jsonString], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `regulations-validees-${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Copie les données JSON dans le presse-papier
 */
export const copyValidatedRegulationsJSON = async (): Promise<boolean> => {
  try {
    const jsonString = exportValidatedRegulationsJSON();
    await navigator.clipboard.writeText(jsonString);
    return true;
  } catch (error) {
    console.error('Erreur lors de la copie:', error);
    return false;
  }
};

/**
 * Affiche les données JSON dans la console
 */
export const logValidatedRegulationsJSON = () => {
  const data = getValidatedRegulationsJSON();
  console.log('=== RÉGLEMENTATIONS VALIDÉES (Format Backend) ===');
  console.log(JSON.stringify(data, null, 2));
  console.log(`Total: ${data.length} réglementation(s) validée(s)`);
};
