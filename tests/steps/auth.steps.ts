import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { loginPage, legalTeamPage, dashboardPage } from './hooks';

/**
 * STEP DEFINITIONS - AUTHENTIFICATION
 * Gère les étapes liées à la connexion et la navigation
 */

// =================== GIVEN ===================

Given('que je suis un utilisateur juridique connecté', async function() {
  await loginPage.goto();
  await loginPage.loginAsJuriste();
  
  // Vérifier que nous sommes sur la bonne page
  await expect(legalTeamPage.pageTitle).toContainText('Interface Juridique');
  console.log('✅ Connexion juridique réussie');
});

Given('que je suis connecté avec un profil décideur', async function() {
  await loginPage.goto();
  await loginPage.loginAsDecideur();
  
  // Vérifier que nous sommes sur le dashboard
  await expect(dashboardPage.userName).toBeVisible();
  console.log('✅ Connexion décideur réussie');
});

Given('que je suis sur la page de connexion', async function() {
  await loginPage.goto();
  await expect(loginPage.emailInput).toBeVisible();
  console.log('📄 Page de connexion affichée');
});

// =================== WHEN ===================

When('je saisis {string} comme email', async function(email: string) {
  await loginPage.emailInput.fill(email);
  console.log(`📧 Email saisi: ${email}`);
});

When('je saisis {string} comme mot de passe', async function(password: string) {
  await loginPage.passwordInput.fill(password);
  console.log('🔒 Mot de passe saisi');
});

When('je clique sur le bouton de connexion', async function() {
  await loginPage.loginButton.click();
  console.log('🔘 Clic sur connexion');
});

When('je clique sur afficher/masquer le mot de passe', async function() {
  await loginPage.togglePasswordVisibility();
  console.log('👁️ Toggle mot de passe');
});

When('je me déconnecte', async function() {
  // Déconnexion depuis n'importe quelle page
  const currentUrl = await loginPage.page.url();
  
  if (currentUrl.includes('/legal-team')) {
    await legalTeamPage.disconnectButton.click();
  } else if (currentUrl.includes('/dashboard')) {
    await dashboardPage.disconnect();
  }
  
  console.log('🚪 Déconnexion effectuée');
});

// =================== THEN ===================

Then('je suis redirigé vers l\'interface juridique', async function() {
  await loginPage.page.waitForURL('/legal-team');
  await expect(legalTeamPage.pageTitle).toContainText('Équipe Juridique');
  console.log('✅ Redirection juridique confirmée');
});

Then('je suis redirigé vers le dashboard', async function() {
  await loginPage.page.waitForURL('/dashboard');
  await expect(dashboardPage.kpiCards.first()).toBeVisible();
  console.log('✅ Redirection dashboard confirmée');
});

Then('je vois un message d\'erreur {string}', async function(errorMessage: string) {
  await loginPage.expectErrorMessage(errorMessage);
  console.log(`❌ Erreur affichée: ${errorMessage}`);
});

Then('le mot de passe est visible en texte clair', async function() {
  await loginPage.expectPasswordVisible();
  console.log('👁️ Mot de passe visible');
});

Then('le mot de passe est masqué', async function() {
  await loginPage.expectPasswordHidden();
  console.log('🙈 Mot de passe masqué');
});

Then('je suis redirigé vers la page de connexion', async function() {
  await loginPage.page.waitForURL('/');
  await expect(loginPage.loginButton).toBeVisible();
  console.log('🔄 Retour à la page de connexion');
});