import { Given, When, Then, Before, After, setDefaultTimeout } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { chromium, Browser, BrowserContext, Page } from 'playwright';
import { LoginPage } from '../pages/LoginPage';
import { LegalTeamPage } from '../pages/LegalTeamPage';
import { DecisionDashboardPage } from '../pages/DecisionDashboardPage';

// Configuration timeout par défaut
setDefaultTimeout(30 * 1000);

// Variables globales pour les objets Playwright
let browser: Browser;
let context: BrowserContext;
let page: Page;

// Page Objects
let loginPage: LoginPage;
let legalTeamPage: LegalTeamPage;
let dashboardPage: DecisionDashboardPage;

/**
 * HOOKS - Configuration et nettoyage
 */

Before(async function() {
  // Initialiser le navigateur pour chaque scénario
  browser = await chromium.launch({ 
    headless: false, // Afficher le navigateur pendant les tests
    slowMo: 500 // Ralentir pour voir les actions
  });
  
  context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    locale: 'fr-FR'
  });
  
  page = await context.newPage();
  
  // Initialiser les Page Objects
  loginPage = new LoginPage(page);
  legalTeamPage = new LegalTeamPage(page);
  dashboardPage = new DecisionDashboardPage(page);
  
  console.log('🚀 Nouveau scénario démarré');
});

After(async function() {
  // Nettoyer après chaque scénario
  if (page) await page.close();
  if (context) await context.close();
  if (browser) await browser.close();
  
  console.log('✅ Scénario terminé');
});

export { page, loginPage, legalTeamPage, dashboardPage };