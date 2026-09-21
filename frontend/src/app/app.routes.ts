import { Routes } from '@angular/router';

import { authGuard } from './guards/auth.guard';
import { AppLayoutComponent } from './components/app-layout/app-layout.component';
import { CandidateFieldsViewComponent } from './pages/candidate-fields-view/candidate-fields-view.component';
import { CandidatesComponent } from './pages/candidates/candidates.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { DuplicatesComponent } from './pages/duplicates/duplicates.component';
import { ExportSuccessComponent } from './pages/export-success/export-success.component';
import { FiltersComponent } from './pages/filters/filters.component';
import { LoginComponent } from './pages/login/login.component';
import { RankingComponent } from './pages/ranking/ranking.component';
import { ShortlistsComponent } from './pages/shortlists/shortlists.component';
import { SettingsComponent } from './pages/settings/settings.component';
import { SyncCandidatesComponent } from './pages/sync-candidates/sync-candidates.component';
import { SyncCompleteComponent } from './pages/sync-complete/sync-complete.component';
import { ResumeGeneratorLayoutComponent } from './pages/resume-generator/layout/resume-generator-layout.component';
import { ResumeUploadComponent } from './pages/resume-generator/upload/resume-upload.component';
import { ResumeReviewComponent } from './pages/resume-generator/review/resume-review.component';
import { TemplateSelectionComponent } from './pages/resume-generator/templates/template-selection.component';
import { ResumePreviewComponent } from './pages/resume-generator/preview/resume-preview.component';
import { MyResumesComponent } from './pages/my-resumes/my-resumes.component';
import { CreateTemplateComponent } from './pages/create-template/create-template.component';

export const routes: Routes = [
	{
		path: '',
		redirectTo: 'login',
		pathMatch: 'full',
	},
	{
		path: 'login',
		component: LoginComponent,
	},
	{
		path: '',
		component: AppLayoutComponent,
		canActivate: [authGuard],
		children: [
			{ path: 'dashboard', component: DashboardComponent },
			{ path: 'candidates', component: CandidatesComponent },
			{ path: 'candidates/:id', component: CandidateFieldsViewComponent },
			{ path: 'filters', component: FiltersComponent },
			{ path: 'ranking', component: RankingComponent },
			{ path: 'shortlists', component: ShortlistsComponent },
			{ path: 'export-success', component: ExportSuccessComponent },
			{ path: 'duplicates', component: DuplicatesComponent },
			{ path: 'my-resumes', component: MyResumesComponent },
			{ path: 'create-template', component: CreateTemplateComponent },
			{
				path: 'resume-generator',
				component: ResumeGeneratorLayoutComponent,
				children: [
					{ path: '', redirectTo: 'upload', pathMatch: 'full' },
					{ path: 'upload', component: ResumeUploadComponent },
					{ path: 'review/:resumeId', component: ResumeReviewComponent },
					{ path: 'templates/:resumeId', component: TemplateSelectionComponent },
					{ path: 'preview/:resumeId/:templateId', component: ResumePreviewComponent },
				],
			},
			{ path: 'settings', component: SettingsComponent },
			{ path: 'sync-candidates', component: SyncCandidatesComponent },
			{ path: 'sync-complete/:syncId', component: SyncCompleteComponent },
		],
	},
	{
		path: '**',
		redirectTo: 'login',
	},
];
