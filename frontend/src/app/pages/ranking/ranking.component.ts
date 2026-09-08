import { CommonModule } from '@angular/common';
import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../services/auth.service';
import { ShortlistService } from '../../services/shortlist.service';

import { CandidateListItem } from '../../models/candidate.models';
import { CandidateService } from '../../services/candidate.service';
import { JobDescriptionListItem } from '../../models/job-description.models';
import { JobDescriptionService } from '../../services/job-description.service';
import { sanitizeCandidateName, sanitizeDisplayText, summarizeSkills } from '../../utils/display-format';

type RankedCandidate = CandidateListItem & {
  computed_match_percentage: number;
  isSelected?: boolean;
};

@Component({
  selector: 'app-ranking',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './ranking.component.html',
  styleUrl: './ranking.component.css',
})
export class RankingComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);

  candidates: RankedCandidate[] = [];
  jobDescriptions: JobDescriptionListItem[] = [];
  selectedJdId: string | null = null;
  loading = false;
  movingToShortlist = false;
  selectedCandidateIds: Set<string> = new Set();
  page = 1;
  pageSize = 10;
  totalItems = 0;
  totalPages = 0;

  constructor(
    private readonly candidateService: CandidateService,
    private readonly jobDescriptionService: JobDescriptionService,
    private readonly authService: AuthService,
    private readonly shortlistService: ShortlistService,
    private readonly router: Router
  ) {}

  ngOnInit(): void {
    this.jobDescriptionService
      .listJobDescriptions()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((items) => {
        this.jobDescriptions = items;
        this.candidates = [];
      });
  }

  onLogout(): void {
    this.authService.logoutFromServer().pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.router.navigate(['/login']);
    });
  }

  goBack(): void {
    window.history.back();
  }

  onJdChange(jdId: string): void {
    this.selectedJdId = jdId || null;
    this.selectedCandidateIds.clear();
    this.loadRankedCandidates(1);
  }

  toggleCandidateSelection(candidateId: string): void {
    if (this.selectedCandidateIds.has(candidateId)) {
      this.selectedCandidateIds.delete(candidateId);
    } else {
      this.selectedCandidateIds.add(candidateId);
    }
    this.updateCandidateSelection();
  }

  toggleSelectAll(): void {
    if (this.isAllSelected()) {
      this.candidates.forEach((candidate) => this.selectedCandidateIds.delete(candidate.id));
    } else {
      this.candidates.forEach((candidate) => this.selectedCandidateIds.add(candidate.id));
    }
    this.updateCandidateSelection();
  }

  isAllSelected(): boolean {
    return this.candidates.length > 0 && this.candidates.every((candidate) => this.selectedCandidateIds.has(candidate.id));
  }

  isIndeterminate(): boolean {
    const selectedOnPage = this.candidates.filter((candidate) => this.selectedCandidateIds.has(candidate.id)).length;
    return selectedOnPage > 0 && selectedOnPage < this.candidates.length;
  }

  getSelectionCount(): number {
    return this.selectedCandidateIds.size;
  }

  async moveSelectedToShortlist(): Promise<void> {
    if (!this.selectedJdId || this.selectedCandidateIds.size === 0 || this.movingToShortlist) {
      return;
    }

    this.movingToShortlist = true;
    try {
      await this.shortlistService
        .createShortlist(this.selectedJdId, Array.from(this.selectedCandidateIds))
        .pipe(takeUntilDestroyed(this.destroyRef))
        .toPromise();
      this.selectedCandidateIds.clear();
      this.router.navigate(['/shortlists'], { queryParams: { jd_id: this.selectedJdId } });
    } finally {
      this.movingToShortlist = false;
    }
  }

  get startItem(): number {
    return this.totalItems ? (this.page - 1) * this.pageSize + 1 : 0;
  }

  get endItem(): number {
    return Math.min(this.page * this.pageSize, this.totalItems);
  }

  get paginationPages(): number[] {
    const totalPages = this.totalPages || 1;
    const visibleWindow = 3;
    if (totalPages <= visibleWindow) {
      return Array.from({ length: totalPages }, (_, index) => index + 1);
    }

    const currentIndex = this.page - 1;
    const halfWindow = Math.floor(visibleWindow / 2);
    let start = Math.max(0, currentIndex - halfWindow);
    const end = Math.min(totalPages, start + visibleWindow);
    start = Math.max(0, end - visibleWindow);

    return Array.from({ length: end - start }, (_, index) => start + index + 1);
  }

  onPageChange(nextPage: number): void {
    if (nextPage < 1 || nextPage > this.totalPages) {
      return;
    }

    this.loadRankedCandidates(nextPage);
  }

  onPageSizeChange(value: string): void {
    const parsed = Number(value);
    if (!Number.isFinite(parsed) || parsed < 1) {
      return;
    }

    this.pageSize = parsed;
    this.loadRankedCandidates(1);
  }

  rank(index: number): string {
    return `#${index + 1}`;
  }

  matchLabel(candidate: RankedCandidate): string {
    return `${Math.round(candidate.computed_match_percentage)}%`;
  }

  safeName(value: string | null | undefined): string {
    return sanitizeCandidateName(value);
  }

  safeText(value: string | null | undefined): string {
    return sanitizeDisplayText(value);
  }

  skillSummary(candidate: CandidateListItem): string {
    return summarizeSkills(candidate.skills);
  }

  get selectedJd(): JobDescriptionListItem | null {
    if (!this.selectedJdId) {
      return null;
    }
    return this.jobDescriptions.find((item) => item.id === this.selectedJdId) ?? null;
  }

  get selectedJdSkills(): string[] {
    const jd = this.selectedJd;
    if (!jd || !Array.isArray(jd.required_skills)) {
      return [];
    }
    return jd.required_skills.filter((item) => item && item.trim().length > 0);
  }

  skillWeightPercent(): number {
    const count = this.selectedJdSkills.length;
    if (!count) {
      return 0;
    }
    return Math.round((100 / count) * 10) / 10;
  }

  private updateCandidateSelection(): void {
    this.candidates = this.candidates.map((candidate) => ({
      ...candidate,
      isSelected: this.selectedCandidateIds.has(candidate.id),
    }));
  }

  private loadRankedCandidates(page = this.page): void {
    if (!this.selectedJdId) {
      this.candidates = [];
      this.totalItems = 0;
      this.totalPages = 0;
      return;
    }

    this.loading = true;
    this.candidateService
      .loadCandidates({
        page,
        pageSize: this.pageSize,
        sortBy: 'full_name',
        sortOrder: 'asc',
        jdId: this.selectedJdId,
      })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((response) => {
        const requiredSkills = this.selectedJdSkills.map((item) => item.trim().toLowerCase()).filter((item) => item.length > 0);
        this.candidates = response.items
          .map((candidate) => ({
            ...candidate,
            computed_match_percentage: this.computeMatchPercentage(candidate, requiredSkills),
            isSelected: this.selectedCandidateIds.has(candidate.id),
          }))
          .sort((a, b) => {
            if (b.computed_match_percentage !== a.computed_match_percentage) {
              return b.computed_match_percentage - a.computed_match_percentage;
            }
            return (b.total_experience_years ?? 0) - (a.total_experience_years ?? 0);
          });
        this.page = response.page;
        this.totalItems = response.total_items;
        this.totalPages = response.total_pages;
        this.loading = false;
      });
  }

  private computeMatchPercentage(candidate: CandidateListItem, requiredSkills: string[]): number {
    if (!requiredSkills.length) {
      return 0;
    }

    const candidateSkills = (candidate.skills ?? []).map((item) => String(item).trim().toLowerCase()).filter((item) => item.length > 0);
    if (!candidateSkills.length) {
      return 0;
    }

    let matches = 0;
    for (const jdSkill of requiredSkills) {
      const found = candidateSkills.some((skill) => skill.includes(jdSkill) || jdSkill.includes(skill));
      if (found) {
        matches += 1;
      }
    }

    return (matches / requiredSkills.length) * 100;
  }
}
