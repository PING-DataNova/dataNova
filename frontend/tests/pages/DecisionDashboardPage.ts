import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object Model pour le dashboard décideur
 * Gère la consultation des KPIs et la navigation profil
 */
export class DecisionDashboardPage {
  readonly page: Page;
  
  // Sidebar
  readonly sidebar: Locator;
  readonly logo: Locator;
  readonly userName: Locator;
  readonly dashboardTab: Locator;
  readonly profileTab: Locator;
  readonly disconnectButton: Locator;
  
  // Dashboard KPIs
  readonly mainContent: Locator;
  readonly kpiCards: Locator;
  readonly totalRegulationsKPI: Locator;
  readonly progressPercentageKPI: Locator;
  readonly highRisksKPI: Locator;
  readonly deadlinesKPI: Locator;
  
  // Graphiques
  readonly chartsSection: Locator;
  readonly timelineChart: Locator;
  readonly processChart: Locator;
  
  // Actions
  readonly exportPdfButton: Locator;
  readonly refreshButton: Locator;
  
  // Profil (vue alternative)
  readonly profileSection: Locator;
  readonly profileInfo: Locator;
  readonly personalStats: Locator;
  readonly connectionsCount: Locator;
  readonly exportsCount: Locator;
  readonly consultationsCount: Locator;

  constructor(page: Page) {
    this.page = page;
    
    // Sidebar
    this.sidebar = page.locator('.decision-sidebar');
    this.logo = page.locator('.decision-logo');
    this.userName = page.locator('.decision-user-name');
    this.dashboardTab = page.locator('a[href="#dashboard"]');
    this.profileTab = page.locator('a[href="#profile"]');
    this.disconnectButton = page.locator('.disconnect-btn');
    
    // Dashboard principal
    this.mainContent = page.locator('.decision-main-content');
    this.kpiCards = page.locator('.kpi-card');
    this.totalRegulationsKPI = page.locator('[data-testid="total-regulations-kpi"]');
    this.progressPercentageKPI = page.locator('[data-testid="progress-percentage-kpi"]');
    this.highRisksKPI = page.locator('[data-testid="high-risks-kpi"]');
    this.deadlinesKPI = page.locator('[data-testid="deadlines-kpi"]');
    
    // Graphiques
    this.chartsSection = page.locator('.charts-section');
    this.timelineChart = page.locator('.timeline-chart');
    this.processChart = page.locator('.process-chart');
    
    // Actions
    this.exportPdfButton = page.locator('button').filter({ hasText: 'Export PDF' });
    this.refreshButton = page.locator('button').filter({ hasText: 'Actualiser' });
    
    // Profil
    this.profileSection = page.locator('.profile-section');
    this.profileInfo = page.locator('.profile-info');
    this.personalStats = page.locator('.personal-stats');
    this.connectionsCount = page.locator('[data-testid="connections-count"]');
    this.exportsCount = page.locator('[data-testid="exports-count"]');
    this.consultationsCount = page.locator('[data-testid="consultations-count"]');
  }

  async goto() {
    await this.page.goto('/dashboard');
  }

  // Navigation
  async switchToDashboard() {
    await this.dashboardTab.click();
    await expect(this.kpiCards.first()).toBeVisible();
  }

  async switchToProfile() {
    await this.profileTab.click();
    await expect(this.profileSection).toBeVisible();
  }

  async disconnect() {
    await this.disconnectButton.click();
  }

  // Actions dashboard
  async exportToPdf() {
    const downloadPromise = this.page.waitForEvent('download');
    await this.exportPdfButton.click();
    const download = await downloadPromise;
    return download;
  }

  async refreshData() {
    await this.refreshButton.click();
    // Attendre le rechargement des données
    await this.page.waitForTimeout(1000);
  }

  // Getters pour les valeurs KPI
  async getTotalRegulations(): Promise<number> {
    const text = await this.totalRegulationsKPI.textContent();
    return parseInt(text?.match(/\d+/)?.[0] || '0');
  }

  async getProgressPercentage(): Promise<number> {
    const text = await this.progressPercentageKPI.textContent();
    return parseInt(text?.match(/\d+/)?.[0] || '0');
  }

  async getHighRisksCount(): Promise<number> {
    const text = await this.highRisksKPI.textContent();
    return parseInt(text?.match(/\d+/)?.[0] || '0');
  }

  async getDeadlinesCount(): Promise<number> {
    const text = await this.deadlinesKPI.textContent();
    return parseInt(text?.match(/\d+/)?.[0] || '0');
  }

  // Getters pour les stats personnelles
  async getConnectionsCount(): Promise<number> {
    const text = await this.connectionsCount.textContent();
    return parseInt(text?.match(/\d+/)?.[0] || '0');
  }

  async getExportsCount(): Promise<number> {
    const text = await this.exportsCount.textContent();
    return parseInt(text?.match(/\d+/)?.[0] || '0');
  }

  async getConsultationsCount(): Promise<number> {
    const text = await this.consultationsCount.textContent();
    return parseInt(text?.match(/\d+/)?.[0] || '0');
  }

  // Assertions
  async expectKPIsVisible() {
    await expect(this.kpiCards).toHaveCount(4);
    await expect(this.totalRegulationsKPI).toBeVisible();
    await expect(this.progressPercentageKPI).toBeVisible();
    await expect(this.highRisksKPI).toBeVisible();
    await expect(this.deadlinesKPI).toBeVisible();
  }

  async expectChartsVisible() {
    await expect(this.chartsSection).toBeVisible();
    await expect(this.timelineChart).toBeVisible();
    await expect(this.processChart).toBeVisible();
  }

  async expectProfileInfoVisible() {
    await expect(this.profileSection).toBeVisible();
    await expect(this.profileInfo).toBeVisible();
    await expect(this.personalStats).toBeVisible();
  }

  async expectUserName(expectedName: string) {
    await expect(this.userName).toContainText(expectedName);
  }

  async expectKPIValue(kpiType: 'total' | 'progress' | 'risks' | 'deadlines', expectedValue: number) {
    const kpiLocator = kpiType === 'total' ? this.totalRegulationsKPI :
                      kpiType === 'progress' ? this.progressPercentageKPI :
                      kpiType === 'risks' ? this.highRisksKPI :
                      this.deadlinesKPI;
    
    await expect(kpiLocator).toContainText(expectedValue.toString());
  }
}