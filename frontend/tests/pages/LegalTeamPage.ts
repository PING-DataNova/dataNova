import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object Model pour l'interface de l'équipe juridique
 * Gère la validation/rejet des réglementations et l'export des données
 */
export class LegalTeamPage {
  readonly page: Page;
  
  // Header et navigation
  readonly pageTitle: Locator;
  readonly searchInput: Locator;
  readonly notificationButton: Locator;
  readonly disconnectButton: Locator;
  
  // Sidebar et filtres
  readonly sidebar: Locator;
  readonly searchFilter: Locator;
  readonly dateFilter: Locator;
  readonly typeFilter: Locator;
  readonly ncCodeFilter: Locator;
  readonly confidenceSlider: Locator;
  readonly resetFiltersButton: Locator;
  
  // Liste des réglementations
  readonly regulationsList: Locator;
  readonly regulationCards: Locator;
  readonly loadingIndicator: Locator;
  
  // Compteurs
  readonly totalCounter: Locator;
  readonly pendingCounter: Locator;
  readonly validatedCounter: Locator;
  readonly rejectedCounter: Locator;
  
  // Export
  readonly exportSection: Locator;
  readonly downloadJsonButton: Locator;
  readonly copyToClipboardButton: Locator;
  readonly showConsoleButton: Locator;

  constructor(page: Page) {
    this.page = page;
    
    // Header
    this.pageTitle = page.locator('h1').first();
    this.searchInput = page.locator('.search-input');
    this.notificationButton = page.locator('.notification-btn');
    this.disconnectButton = page.locator('.disconnect-btn');
    
    // Sidebar
    this.sidebar = page.locator('.sidebar');
    this.searchFilter = page.locator('input[placeholder*="Rechercher"]');
    this.dateFilter = page.locator('select[data-testid="date-filter"]');
    this.typeFilter = page.locator('select[data-testid="type-filter"]');
    this.ncCodeFilter = page.locator('select[data-testid="nc-code-filter"]');
    this.confidenceSlider = page.locator('input[type="range"]');
    this.resetFiltersButton = page.locator('button').filter({ hasText: 'Reset' });
    
    // Liste
    this.regulationsList = page.locator('.regulations-list');
    this.regulationCards = page.locator('.regulation-card');
    this.loadingIndicator = page.locator('.loading-indicator');
    
    // Compteurs
    this.totalCounter = page.locator('[data-testid="total-count"]');
    this.pendingCounter = page.locator('[data-testid="pending-count"]');
    this.validatedCounter = page.locator('[data-testid="validated-count"]');
    this.rejectedCounter = page.locator('[data-testid="rejected-count"]');
    
    // Export
    this.exportSection = page.locator('.export-section');
    this.downloadJsonButton = page.locator('button').filter({ hasText: 'Télécharger JSON' });
    this.copyToClipboardButton = page.locator('button').filter({ hasText: 'Copier' });
    this.showConsoleButton = page.locator('button').filter({ hasText: 'Console' });
  }

  async goto() {
    await this.page.goto('/legal-team');
  }

  // Actions sur les réglementations
  async validateRegulation(regulationTitle: string) {
    const card = this.regulationCards.filter({ hasText: regulationTitle });
    const validateButton = card.locator('button').filter({ hasText: 'Valider' });
    await validateButton.click();
  }

  async rejectRegulation(regulationTitle: string) {
    const card = this.regulationCards.filter({ hasText: regulationTitle });
    const rejectButton = card.locator('button').filter({ hasText: 'Rejeter' });
    await rejectButton.click();
  }

  async getRegulationStatus(regulationTitle: string): Promise<string> {
    const card = this.regulationCards.filter({ hasText: regulationTitle });
    const statusBadge = card.locator('.status-badge');
    return await statusBadge.textContent() || '';
  }

  // Filtres
  async searchRegulations(searchTerm: string) {
    await this.searchFilter.fill(searchTerm);
    // Attendre le debounce
    await this.page.waitForTimeout(500);
  }

  async filterByDateRange(dateRange: string) {
    await this.dateFilter.selectOption(dateRange);
  }

  async filterByType(type: string) {
    await this.typeFilter.selectOption(type);
  }

  async filterByNcCode(ncCode: string) {
    await this.ncCodeFilter.selectOption(ncCode);
  }

  async setConfidenceRange(minValue: number) {
    await this.confidenceSlider.fill(minValue.toString());
  }

  async resetAllFilters() {
    await this.resetFiltersButton.click();
  }

  // Export
  async downloadJson() {
    const downloadPromise = this.page.waitForEvent('download');
    await this.downloadJsonButton.click();
    const download = await downloadPromise;
    return download;
  }

  async copyToClipboard() {
    await this.copyToClipboardButton.click();
  }

  async showInConsole() {
    await this.showConsoleButton.click();
  }

  // Assertions
  async expectRegulationsCount(expectedCount: number) {
    await expect(this.regulationCards).toHaveCount(expectedCount);
  }

  async expectRegulationVisible(title: string) {
    await expect(this.regulationCards.filter({ hasText: title })).toBeVisible();
  }

  async expectRegulationStatus(title: string, status: 'Pending' | 'Validated' | 'Rejected') {
    const card = this.regulationCards.filter({ hasText: title });
    await expect(card.locator('.status-badge')).toContainText(status);
  }

  async expectCounterValue(counter: 'total' | 'pending' | 'validated' | 'rejected', value: number) {
    const counterLocator = counter === 'total' ? this.totalCounter :
                          counter === 'pending' ? this.pendingCounter :
                          counter === 'validated' ? this.validatedCounter :
                          this.rejectedCounter;
    
    await expect(counterLocator).toContainText(value.toString());
  }

  async expectSearchResultsFiltered(searchTerm: string) {
    const allCards = await this.regulationCards.all();
    for (const card of allCards) {
      const text = await card.textContent();
      expect(text?.toLowerCase()).toContain(searchTerm.toLowerCase());
    }
  }
}