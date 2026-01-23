import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { legalTeamPage } from './hooks';

/**
 * STEP DEFINITIONS - INTERFACE JURIDIQUE
 * Gère les étapes liées à la gestion des réglementations
 */

// Variables pour stocker l'état durant les tests
let initialValidatedCount: number = 0;
let initialRejectedCount: number = 0;
let selectedRegulationTitle: string = '';

// =================== GIVEN ===================

Given('que la plateforme contient des réglementations à traiter', async function() {
  // Vérifier qu'il y a au moins des réglementations affichées
  await legalTeamPage.expectRegulationsCount(1); // Au moins 1
  console.log('📋 Réglementations présentes dans la plateforme');
});

Given('que je suis sur la page de l\'équipe juridique', async function() {
  await legalTeamPage.goto();
  await expect(legalTeamPage.pageTitle).toBeVisible();
  console.log('📄 Page équipe juridique affichée');
});

Given('que j\'ai validé au moins {int} réglementations', async function(minCount: number) {
  // Valider quelques réglementations si nécessaire
  const validatedCount = await legalTeamPage.validatedCounter.textContent();
  const currentCount = parseInt(validatedCount?.match(/\d+/)?.[0] || '0');
  
  if (currentCount < minCount) {
    const regulationsToValidate = minCount - currentCount;
    const pendingCards = await legalTeamPage.regulationCards.filter({ hasText: 'Pending' }).all();
    
    for (let i = 0; i < Math.min(regulationsToValidate, pendingCards.length); i++) {
      const card = pendingCards[i];
      const title = await card.locator('.regulation-title').textContent() || '';
      await legalTeamPage.validateRegulation(title);
      await legalTeamPage.page.waitForTimeout(500); // Attendre la mise à jour
    }
  }
  
  console.log(`✅ Au moins ${minCount} réglementations validées`);
});

Given('que je vois une réglementation avec le statut {string}', async function(status: string) {
  const regulationCard = legalTeamPage.regulationCards.filter({ hasText: status }).first();
  await expect(regulationCard).toBeVisible();
  
  // Stocker le titre pour les étapes suivantes
  selectedRegulationTitle = await regulationCard.locator('.regulation-title').textContent() || '';
  console.log(`🔍 Réglementation trouvée avec statut ${status}: ${selectedRegulationTitle}`);
});

// =================== WHEN ===================

When('j\'observe la liste des réglementations', async function() {
  await expect(legalTeamPage.regulationsList).toBeVisible();
  console.log('👀 Liste des réglementations observée');
});

When('je saisis {string} dans le champ de recherche', async function(searchTerm: string) {
  await legalTeamPage.searchRegulations(searchTerm);
  console.log(`🔍 Recherche: ${searchTerm}`);
});

When('je sélectionne le filtre code NC {string}', async function(ncCode: string) {
  await legalTeamPage.filterByNcCode(ncCode);
  console.log(`🏷️ Filtre NC: ${ncCode}`);
});

When('je sélectionne le filtre type {string}', async function(regulationType: string) {
  await legalTeamPage.filterByType(regulationType);
  console.log(`📂 Filtre type: ${regulationType}`);
});

When('je sélectionne la période {string}', async function(dateRange: string) {
  await legalTeamPage.filterByDateRange(dateRange);
  console.log(`📅 Filtre période: ${dateRange}`);
});

When('je règle la confiance minimum à {int}%', async function(minConfidence: number) {
  await legalTeamPage.setConfidenceRange(minConfidence);
  console.log(`📊 Confiance minimum: ${minConfidence}%`);
});

When('je clique sur le bouton {string}', async function(buttonText: string) {
  if (buttonText === 'Valider') {
    // Stocker le compteur initial
    const validatedText = await legalTeamPage.validatedCounter.textContent();
    initialValidatedCount = parseInt(validatedText?.match(/\d+/)?.[0] || '0');
    
    await legalTeamPage.validateRegulation(selectedRegulationTitle);
    console.log(`✅ Validation de: ${selectedRegulationTitle}`);
    
  } else if (buttonText === 'Rejeter') {
    // Stocker le compteur initial
    const rejectedText = await legalTeamPage.rejectedCounter.textContent();
    initialRejectedCount = parseInt(rejectedText?.match(/\d+/)?.[0] || '0');
    
    await legalTeamPage.rejectRegulation(selectedRegulationTitle);
    console.log(`❌ Rejet de: ${selectedRegulationTitle}`);
    
  } else if (buttonText === 'Télécharger JSON') {
    await legalTeamPage.downloadJson();
    console.log('💾 Téléchargement JSON');
    
  } else if (buttonText === 'Copier') {
    await legalTeamPage.copyToClipboard();
    console.log('📋 Copie dans presse-papiers');
    
  } else if (buttonText === 'Reset filtres') {
    await legalTeamPage.resetAllFilters();
    console.log('🔄 Reset des filtres');
  }
});

// =================== THEN ===================

Then('je vois au moins {int} réglementations affichées', async function(minCount: number) {
  const actualCount = await legalTeamPage.regulationCards.count();
  expect(actualCount).toBeGreaterThanOrEqual(minCount);
  console.log(`📊 ${actualCount} réglementations affichées (minimum: ${minCount})`);
});

Then('chaque réglementation affiche son titre, sa source et son statut', async function() {
  const cards = await legalTeamPage.regulationCards.all();
  
  for (const card of cards) {
    await expect(card.locator('.regulation-title')).toBeVisible();
    await expect(card.locator('.regulation-reference')).toBeVisible();
    await expect(card.locator('.status-badge')).toBeVisible();
  }
  
  console.log('✅ Tous les éléments requis sont affichés');
});

Then('je vois les badges de confiance IA colorés', async function() {
  const confidenceBadges = legalTeamPage.regulationCards.locator('.confidence-badge');
  await expect(confidenceBadges.first()).toBeVisible();
  console.log('🎨 Badges de confiance IA visibles');
});

Then('la liste se filtre automatiquement', async function() {
  // Attendre que le filtrage soit appliqué
  await legalTeamPage.page.waitForTimeout(1000);
  console.log('⚡ Filtrage automatique appliqué');
});

Then('je ne vois que les réglementations contenant {string}', async function(searchTerm: string) {
  await legalTeamPage.expectSearchResultsFiltered(searchTerm);
  console.log(`✅ Résultats filtrés pour: ${searchTerm}`);
});

Then('je ne vois que les réglementations avec le code NC {string}', async function(ncCode: string) {
  const cards = await legalTeamPage.regulationCards.all();
  
  for (const card of cards) {
    const cardText = await card.textContent();
    expect(cardText).toContain(ncCode);
  }
  
  console.log(`✅ Seules les réglementations NC ${ncCode} affichées`);
});

Then('le compteur de résultats se met à jour', async function() {
  await expect(legalTeamPage.totalCounter).toBeVisible();
  console.log('📊 Compteur mis à jour');
});

Then('le statut change vers {string} avec un badge {string}', async function(newStatus: string, badgeColor: string) {
  await legalTeamPage.expectRegulationStatus(selectedRegulationTitle, newStatus as any);
  console.log(`✅ Statut changé: ${newStatus} (badge ${badgeColor})`);
});

Then('la réglementation reste visible dans la liste', async function() {
  await legalTeamPage.expectRegulationVisible(selectedRegulationTitle);
  console.log('👁️ Réglementation toujours visible');
});

Then('le compteur {string} s\'incrémente', async function(counterType: string) {
  if (counterType === 'Validées') {
    await legalTeamPage.expectCounterValue('validated', initialValidatedCount + 1);
  } else if (counterType === 'Rejetées') {
    await legalTeamPage.expectCounterValue('rejected', initialRejectedCount + 1);
  }
  
  console.log(`📈 Compteur ${counterType} incrémenté`);
});