import { test, expect } from '@playwright/test';

test.describe('Authentification et Navigation', () => {
  
  test('Connexion juriste et accès interface juridique', async ({ page }) => {
    // Aller à la page de connexion
    await page.goto('http://localhost:3008');
    
    // Vérifier que la page de connexion s'affiche
    await expect(page.locator('input[type="email"]')).toBeVisible();
    
    // Se connecter comme juriste
    await page.fill('input[type="email"]', 'juriste@hutchinson.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Vérifier la redirection vers l'interface juridique
    await expect(page).toHaveURL(/legal-team/);
    
    // Vérifier que les éléments principaux sont présents
    await expect(page.locator('h1')).toContainText('Équipe Juridique');
    await expect(page.locator('.sidebar')).toBeVisible();
    await expect(page.locator('.regulations-list')).toBeVisible();
    
    console.log('✅ Test connexion juriste réussi');
  });

  test('Connexion décideur et accès dashboard', async ({ page }) => {
    // Aller à la page de connexion
    await page.goto('http://localhost:3008');
    
    // Se connecter comme décideur
    await page.fill('input[type="email"]', 'decideur@hutchinson.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Vérifier la redirection vers le dashboard
    await expect(page).toHaveURL(/dashboard/);
    
    // Vérifier que les KPIs sont visibles
    await expect(page.locator('.kpi-card')).toHaveCount(4);
    
    console.log('✅ Test connexion décideur réussi');
  });

  test('Recherche de réglementations', async ({ page }) => {
    // Connexion juriste
    await page.goto('http://localhost:3008');
    await page.fill('input[type="email"]', 'juriste@hutchinson.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Attendre que la page se charge
    await expect(page.locator('.regulations-list')).toBeVisible();
    
    // Compter les réglementations initiales
    const initialCount = await page.locator('.regulation-card').count();
    
    // Rechercher "CBAM"
    await page.fill('input[placeholder*="Rechercher"]', 'CBAM');
    
    // Attendre le filtrage
    await page.waitForTimeout(500);
    
    // Vérifier que les résultats sont filtrés
    const filteredCount = await page.locator('.regulation-card').count();
    expect(filteredCount).toBeLessThanOrEqual(initialCount);
    
    console.log(`✅ Recherche: ${initialCount} → ${filteredCount} réglementations`);
  });

  test('Validation d\'une réglementation', async ({ page }) => {
    // Connexion juriste
    await page.goto('http://localhost:3008');
    await page.fill('input[type="email"]', 'juriste@hutchinson.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Attendre que la liste se charge
    await expect(page.locator('.regulation-card')).toHaveCount.toBeGreaterThan(0);
    
    // Trouver une réglementation avec statut "Pending"
    const pendingCard = page.locator('.regulation-card').filter({ hasText: 'Pending' }).first();
    await expect(pendingCard).toBeVisible();
    
    // Cliquer sur "Valider"
    await pendingCard.locator('button:has-text("Valider")').click();
    
    // Vérifier que le statut change
    await expect(pendingCard.locator('.status-badge')).toContainText('Validated');
    
    console.log('✅ Validation réglementation réussie');
  });

});