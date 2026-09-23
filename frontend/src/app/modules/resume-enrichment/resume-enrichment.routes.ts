import { Routes } from '@angular/router';
import { ResumeBatchListComponent } from '../../components/resume-batch-list/resume-batch-list.component';
import { ResumeBatchDetailComponent } from '../../components/resume-batch-detail/resume-batch-detail.component';
import { CandidateReviewComponent } from '../../components/candidate-review/candidate-review.component';

export const RESUME_ENRICHMENT_ROUTES: Routes = [
  {
    path: 'batches',
    component: ResumeBatchListComponent,
    data: { title: 'Resume Enrichment Batches' },
  },
  {
    path: 'batches/:batchId',
    component: ResumeBatchDetailComponent,
    data: { title: 'Batch Details' },
  },
  {
    path: 'candidates/:candidateReviewId',
    component: CandidateReviewComponent,
    data: { title: 'Candidate Review' },
  },
  {
    path: '',
    redirectTo: 'batches',
    pathMatch: 'full',
  },
];
