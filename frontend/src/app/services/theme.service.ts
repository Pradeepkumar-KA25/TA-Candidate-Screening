import { Injectable } from '@angular/core';

export type AppTheme = 'light' | 'dark';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly storageKey = 'talent-acquisition-theme';
  private currentTheme: AppTheme = this.loadTheme();

  constructor() {
    this.applyTheme(this.currentTheme);
  }

  get theme(): AppTheme {
    return this.currentTheme;
  }

  isDarkMode(): boolean {
    return this.currentTheme === 'dark';
  }

  setTheme(theme: AppTheme): void {
    this.currentTheme = theme;
    localStorage.setItem(this.storageKey, theme);
    this.applyTheme(theme);
  }

  toggleTheme(): void {
    this.setTheme(this.currentTheme === 'dark' ? 'light' : 'dark');
  }

  private loadTheme(): AppTheme {
    const saved = localStorage.getItem(this.storageKey);
    return saved === 'dark' ? 'dark' : 'light';
  }

  private applyTheme(theme: AppTheme): void {
    document.body.setAttribute('data-theme', theme);
  }
}
