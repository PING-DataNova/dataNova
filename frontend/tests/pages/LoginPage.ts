import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object Model pour la page de connexion
 * Gère l'authentification et le routage selon le profil utilisateur
 */
export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly togglePasswordButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.locator('input[type="email"]');
    this.passwordInput = page.locator('input[type="password"]');
    this.loginButton = page.locator('button[type="submit"]');
    this.togglePasswordButton = page.locator('button[aria-label="Afficher le mot de passe"]');
    this.errorMessage = page.locator('.error-message');
  }

  async goto() {
    await this.page.goto('/');
  }

  async loginAsJuriste(password: string = 'password123') {
    await this.emailInput.fill('juriste@hutchinson.com');
    await this.passwordInput.fill(password);
    await this.loginButton.click();
    
    // Vérifier redirection vers interface juridique
    await this.page.waitForURL('/legal-team');
  }

  async loginAsDecideur(password: string = 'password123') {
    await this.emailInput.fill('decideur@hutchinson.com');
    await this.passwordInput.fill(password);
    await this.loginButton.click();
    
    // Vérifier redirection vers dashboard
    await this.page.waitForURL('/dashboard');
  }

  async togglePasswordVisibility() {
    await this.togglePasswordButton.click();
  }

  async expectPasswordVisible() {
    await expect(this.passwordInput).toHaveAttribute('type', 'text');
  }

  async expectPasswordHidden() {
    await expect(this.passwordInput).toHaveAttribute('type', 'password');
  }

  async expectErrorMessage(message: string) {
    await expect(this.errorMessage).toContainText(message);
  }
}