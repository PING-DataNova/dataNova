import { Given, When, Then, setWorldConstructor } from '@cucumber/cucumber';
import { Page } from 'playwright';

/**
 * WORLD - Contexte partagé entre les steps
 * Permet de stocker des données temporaires entre les étapes
 */

export class TestWorld {
  public page!: Page;
  public selectedRegulation: string = '';
  public initialCounts: {[key: string]: number} = {};
  public downloadedFiles: any[] = [];
  public clipboardData: string = '';
  public testStartTime: Date = new Date();

  constructor() {
    this.testStartTime = new Date();
  }

  // Méthodes utilitaires
  storeInitialCount(counterType: string, value: number) {
    this.initialCounts[counterType] = value;
  }

  getInitialCount(counterType: string): number {
    return this.initialCounts[counterType] || 0;
  }

  setSelectedRegulation(title: string) {
    this.selectedRegulation = title;
  }

  addDownloadedFile(file: any) {
    this.downloadedFiles.push(file);
  }

  getLatestDownload() {
    return this.downloadedFiles[this.downloadedFiles.length - 1];
  }

  setClipboardData(data: string) {
    this.clipboardData = data;
  }

  getTestDuration(): number {
    return Date.now() - this.testStartTime.getTime();
  }

  reset() {
    this.selectedRegulation = '';
    this.initialCounts = {};
    this.downloadedFiles = [];
    this.clipboardData = '';
  }
}

setWorldConstructor(TestWorld);