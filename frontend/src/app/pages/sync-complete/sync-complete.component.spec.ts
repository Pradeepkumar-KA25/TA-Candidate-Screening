import { of } from 'rxjs';

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { SyncService } from '../../services/sync.service';
import { SyncCompleteComponent } from './sync-complete.component';

describe('SyncCompleteComponent', () => {
  let fixture: ComponentFixture<SyncCompleteComponent>;
  let component: SyncCompleteComponent;
  let syncService: jasmine.SpyObj<SyncService>;

  beforeEach(async () => {
    syncService = jasmine.createSpyObj<SyncService>('SyncService', ['getSyncSummary']);
    syncService.getSyncSummary.and.returnValue(
      of({
        sync_id: 'sync-1',
        status: 'completed',
        started_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
        records_fetched: 2,
        records_new: 1,
        records_updated: 1,
        records_failed: 0,
        duplicate_matches: 0,
        normalized_records: 2,
        normalization_examples: [
          {
            field: 'location',
            raw_value: 'Bangalore',
            normalized_value: 'Bengaluru',
          },
        ],
        error_message: null,
      })
    );

    await TestBed.configureTestingModule({
      imports: [SyncCompleteComponent, RouterTestingModule],
      providers: [
        { provide: SyncService, useValue: syncService },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: {
                get: () => 'sync-1',
              },
            },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SyncCompleteComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should load and render normalization examples', () => {
    expect(syncService.getSyncSummary).toHaveBeenCalledWith('sync-1');
    const html = fixture.nativeElement as HTMLElement;
    expect(html.textContent).toContain('Normalization Examples');
    expect(html.textContent).toContain('Bangalore -> Bengaluru');
  });

  it('should expose successful state', () => {
    expect(component.isSuccessful).toBeTrue();
  });
});
