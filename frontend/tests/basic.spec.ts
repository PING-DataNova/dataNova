import { test, expect } from '@playwright/test';

/**
 * Tests de base pour vérifier le fonctionnement de l'application
 */

test.describe('Plateforme de Veille Réglementaire - Tests de base', () => {
  
  test.beforeEach(async ({ page }) => {
    // Démarrer sur la page de connexion
    await page.goto('http://localhost:3006');
  });

  test('Page de connexion s\'affiche correctement', async ({ page }) => {
    // Vérifier que les éléments de connexion sont présents
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    
    console.log('✅ Page de connexion affichée correctement');
  });

  test('Connexion juridique fonctionne', async ({ page }) => {
    // Se connecter avec un profil juridique
    await page.fill('input[type="email"]', 'juriste@hutchinson.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Vérifier la redirection vers interface juridique
    await expect(page).toHaveURL(/.*legal-team/);
    
    // Vérifier que les éléments de l'interface juridique sont présents
    await expect(page.locator('h1')).toContainText('Équipe Juridique');
    
    console.log('✅ Connexion juridique réussie');
  });

  test('Connexion décideur fonctionne', async ({ page }) => {
    // Se connecter avec un profil décideur
    await page.fill('input[type="email"]', 'decideur@hutchinson.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Vérifier la redirection vers dashboard
    await expect(page).toHaveURL(/.*dashboard/);
    
    // Vérifier que les KPIs sont affichés
    await expect(page.locator('.kpi-card')).toHaveCount(4);
    
    console.log('✅ Connexion décideur réussie');
  });

  test('Liste des réglementations s\'affiche', async ({ page }) => {
    // Se connecter en tant que juriste
    await page.fill('input[type="email"]', 'juriste@hutchinson.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Attendre que la page se charge
    await page.waitForSelector('.regulation-card');
    
    // Vérifier qu'il y a des réglementations
    const regulationCards = page.locator('.regulation-card');
    await expect(regulationCards).toHaveCountGreaterThan(0);
    
    // Vérifier les éléments de chaque carte
    const firstCard = regulationCards.first();
    await expect(firstCard.locator('.regulation-title')).toBeVisible();
    await expect(firstCard.locator('.status-badge')).toBeVisible();
    
    console.log('✅ Liste des réglementations affichée');
  });

  test('Recherche fonctionne', async ({ page }) => {
    // Se connecter et aller à l'interface juridique
    await page.fill('input[type="email"]', 'juriste@hutchinson.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Attendre le chargement
    await page.waitForSelector('.search-input');
    
    // Effectuer une recherche
    await page.fill('input[placeholder*="Rechercher"]', 'CBAM');
    
    // Attendre le filtrage (debounce)
    await page.waitForTimeout(1000);
    
    // Vérifier que les résultats sont filtrés
    const cards = page.locator('.regulation-card');
    const cardCount = await cards.count();
    
    if (cardCount > 0) {
      // Vérifier que les cartes visibles contiennent le terme recherché
      const firstCardText = await cards.first().textContent();
      expect(firstCardText?.toLowerCase()).toContain('cbam');
    }
    
    console.log('✅ Recherche fonctionne');
  });
});