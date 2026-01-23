import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { legalTeamPage, page } from './hooks';

/**
 * STEP DEFINITIONS - EXPORT ET DONNÉES
 * Gère les étapes liées à l'export JSON, copie presse-papiers, etc.
 */

// Variables pour stocker les données d'export
let downloadedFile: any = null;
let clipboardContent: string = '';

// =================== WHEN ===================

When('je clique sur {string}', async function(buttonText: string) {
  if (buttonText === 'Télécharger JSON') {
    // Attendre le téléchargement
    const downloadPromise = page.waitForEvent('download');
    await legalTeamPage.downloadJsonButton.click();
    downloadedFile = await downloadPromise;
    console.log('💾 Téléchargement JSON initié');
    
  } else if (buttonText === 'Copier') {
    await legalTeamPage.copyToClipboard();
    
    // Lire le contenu du presse-papiers
    clipboardContent = await page.evaluate(() => navigator.clipboard.readText());
    console.log('📋 Données copiées dans le presse-papiers');
    
  } else if (buttonText === 'Afficher Console') {
    await legalTeamPage.showInConsole();
    console.log('🖥️ Données affichées dans la console');
  }
});

// =================== THEN ===================

Then('un fichier JSON est téléchargé', async function() {
  expect(downloadedFile).toBeTruthy();
  
  // Vérifier l'extension du fichier
  const fileName = downloadedFile.suggestedFilename();
  expect(fileName).toMatch(/\.json$/);
  
  console.log(`📄 Fichier téléchargé: ${fileName}`);
});

Then('le fichier contient uniquement les réglementations validées', async function() {
  // Sauvegarder le fichier temporairement pour l'analyser
  const path = `./test-results/${downloadedFile.suggestedFilename()}`;
  await downloadedFile.saveAs(path);
  
  // Lire et parser le fichier JSON
  const fs = await import('fs');
  const fileContent = fs.readFileSync(path, 'utf-8');
  const jsonData = JSON.parse(fileContent);
  
  // Vérifier que toutes les réglementations sont validées
  expect(Array.isArray(jsonData.data)).toBe(true);
  
  for (const regulation of jsonData.data) {
    expect(regulation.validation_status || regulation.status).toBe('validated');
  }
  
  console.log(`✅ ${jsonData.data.length} réglementations validées dans le fichier`);
});

Then('chaque réglementation contient tous les champs requis', async function() {
  // Lire le fichier téléchargé
  const path = `./test-results/${downloadedFile.suggestedFilename()}`;
  const fs = await import('fs');
  const fileContent = fs.readFileSync(path, 'utf-8');
  const jsonData = JSON.parse(fileContent);
  
  // Champs requis pour l'export
  const requiredFields = [
    'id', 'title', 'type', 'publication_date', 
    'source_url', 'nc_codes', 'ai_confidence'
  ];
  
  for (const regulation of jsonData.data) {
    for (const field of requiredFields) {
      expect(regulation).toHaveProperty(field);
    }
  }
  
  console.log('✅ Tous les champs requis présents dans l\'export');
});

Then('les données JSON sont copiées dans le presse-papiers', async function() {
  expect(clipboardContent).toBeTruthy();
  
  // Vérifier que c'est du JSON valide
  const parsedData = JSON.parse(clipboardContent);
  expect(parsedData).toBeTruthy();
  
  console.log('📋 Données JSON valides dans le presse-papiers');
});

Then('une notification de succès s\'affiche', async function() {
  // Vérifier qu'un toast/notification apparaît
  const notification = page.locator('.toast, .notification, .alert-success').first();
  await expect(notification).toBeVisible({ timeout: 5000 });
  
  console.log('✅ Notification de succès affichée');
});

Then('les données sont affichées dans la console', async function() {
  // Écouter les messages de la console
  let consoleMessageFound = false;
  
  page.on('console', (msg) => {
    if (msg.text().includes('réglementations') || msg.text().includes('Export')) {
      consoleMessageFound = true;
    }
  });
  
  // Attendre un court instant pour que les messages console arrivent
  await page.waitForTimeout(1000);
  
  expect(consoleMessageFound).toBe(true);
  console.log('🖥️ Données visibles dans la console du navigateur');
});

Then('le format JSON est standardisé', async function() {
  let jsonData;
  
  if (downloadedFile) {
    // Analyser le fichier téléchargé
    const path = `./test-results/${downloadedFile.suggestedFilename()}`;
    const fs = await import('fs');
    const fileContent = fs.readFileSync(path, 'utf-8');
    jsonData = JSON.parse(fileContent);
  } else if (clipboardContent) {
    // Analyser les données du presse-papiers
    jsonData = JSON.parse(clipboardContent);
  }
  
  // Vérifier la structure standardisée
  expect(jsonData).toHaveProperty('export_date');
  expect(jsonData).toHaveProperty('total_regulations');
  expect(jsonData).toHaveProperty('data');
  expect(Array.isArray(jsonData.data)).toBe(true);
  
  console.log('📊 Format JSON standardisé confirmé');
});

Then('les métadonnées d\'export sont incluses', async function() {
  let jsonData;
  
  if (downloadedFile) {
    const path = `./test-results/${downloadedFile.suggestedFilename()}`;
    const fs = await import('fs');
    const fileContent = fs.readFileSync(path, 'utf-8');
    jsonData = JSON.parse(fileContent);
  } else {
    jsonData = JSON.parse(clipboardContent);
  }
  
  // Vérifier les métadonnées
  expect(jsonData.export_date).toMatch(/^\d{4}-\d{2}-\d{2}T/); // Format ISO date
  expect(typeof jsonData.total_regulations).toBe('number');
  expect(jsonData.total_regulations).toBeGreaterThanOrEqual(0);
  
  console.log(`📊 Métadonnées: ${jsonData.total_regulations} réglementations, exporté le ${jsonData.export_date}`);
});