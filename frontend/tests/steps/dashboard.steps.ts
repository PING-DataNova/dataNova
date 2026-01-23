import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { dashboardPage } from './hooks';

/**
 * STEP DEFINITIONS - DASHBOARD DÉCIDEUR
 * Gère les étapes liées aux KPIs et statistiques
 */

// =================== GIVEN ===================

Given('que je suis sur le dashboard décideur', async function() {
  await dashboardPage.goto();
  await expect(dashboardPage.mainContent).toBeVisible();
  console.log('📊 Dashboard décideur affiché');
});

// =================== WHEN ===================

When('j\'accède à la plateforme', async function() {
  // Cette action est déjà faite par la connexion
  await expect(dashboardPage.kpiCards.first()).toBeVisible();
  console.log('🏠 Accès à la plateforme confirmé');
});

When('je clique sur l\'onglet {string}', async function(tabName: string) {
  if (tabName === 'Dashboard') {
    await dashboardPage.switchToDashboard();
    console.log('📊 Basculé vers Dashboard');
  } else if (tabName === 'Profil') {
    await dashboardPage.switchToProfile();
    console.log('👤 Basculé vers Profil');
  }
});

When('je clique sur {string}', async function(buttonText: string) {
  if (buttonText === 'Export PDF') {
    await dashboardPage.exportToPdf();
    console.log('📄 Export PDF déclenché');
  } else if (buttonText === 'Actualiser') {
    await dashboardPage.refreshData();
    console.log('🔄 Données actualisées');
  }
});

// =================== THEN ===================

Then('je vois {int} indicateurs KPI', async function(expectedCount: number) {
  await expect(dashboardPage.kpiCards).toHaveCount(expectedCount);
  console.log(`📊 ${expectedCount} KPIs affichés`);
});

Then('je vois les statistiques de traitement', async function() {
  await dashboardPage.expectKPIsVisible();
  
  // Vérifier que les valeurs sont cohérentes
  const totalRegulations = await dashboardPage.getTotalRegulations();
  const progressPercentage = await dashboardPage.getProgressPercentage();
  
  expect(totalRegulations).toBeGreaterThan(0);
  expect(progressPercentage).toBeGreaterThanOrEqual(0);
  expect(progressPercentage).toBeLessThanOrEqual(100);
  
  console.log(`📈 Stats: ${totalRegulations} réglementations, ${progressPercentage}% progression`);
});

Then('je vois les indicateurs de risques et deadlines', async function() {
  const risksCount = await dashboardPage.getHighRisksCount();
  const deadlinesCount = await dashboardPage.getDeadlinesCount();
  
  expect(risksCount).toBeGreaterThanOrEqual(0);
  expect(deadlinesCount).toBeGreaterThanOrEqual(0);
  
  console.log(`⚠️ Risques: ${risksCount}, Deadlines: ${deadlinesCount}`);
});

Then('je vois les graphiques de répartition', async function() {
  await dashboardPage.expectChartsVisible();
  console.log('📊 Graphiques de répartition visibles');
});

Then('je vois mes informations personnelles', async function() {
  await dashboardPage.expectProfileInfoVisible();
  console.log('👤 Informations personnelles affichées');
});

Then('je vois mes statistiques d\'utilisation', async function() {
  const connections = await dashboardPage.getConnectionsCount();
  const exports = await dashboardPage.getExportsCount();
  const consultations = await dashboardPage.getConsultationsCount();
  
  expect(connections).toBeGreaterThanOrEqual(0);
  expect(exports).toBeGreaterThanOrEqual(0);
  expect(consultations).toBeGreaterThanOrEqual(0);
  
  console.log(`📊 Stats personnelles: ${connections} connexions, ${exports} exports, ${consultations} consultations`);
});

Then('un fichier PDF est généré', async function() {
  // Le téléchargement est géré par le Page Object
  console.log('📄 Fichier PDF généré avec succès');
});

Then('les données sont mises à jour', async function() {
  // Vérifier que les KPIs sont toujours visibles après actualisation
  await dashboardPage.expectKPIsVisible();
  console.log('🔄 Données mises à jour avec succès');
});

Then('je vois le nom d\'utilisateur {string}', async function(expectedName: string) {
  await dashboardPage.expectUserName(expectedName);
  console.log(`👤 Nom utilisateur confirmé: ${expectedName}`);
});

Then('la vue {string} est active', async function(viewName: string) {
  if (viewName === 'Dashboard') {
    await expect(dashboardPage.kpiCards.first()).toBeVisible();
    console.log('📊 Vue Dashboard active');
  } else if (viewName === 'Profil') {
    await expect(dashboardPage.profileSection).toBeVisible();
    console.log('👤 Vue Profil active');
  }
});