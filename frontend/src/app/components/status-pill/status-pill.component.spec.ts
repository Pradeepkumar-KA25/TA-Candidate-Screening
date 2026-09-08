/// <reference types="jasmine" />

import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StatusPillComponent } from './status-pill.component';

describe('StatusPillComponent', () => {
  let component: StatusPillComponent;
  let fixture: ComponentFixture<StatusPillComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StatusPillComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(StatusPillComponent);
    component = fixture.componentInstance;
  });

  it('should render connected state text and class', () => {
    component.labelPrefix = 'Zoho Recruit';
    component.state = 'connected';
    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;
    const pill = element.querySelector('.status-pill');
    expect(pill?.textContent).toContain('Zoho Recruit: Connected');
    expect(pill?.classList.contains('state-connected')).toBeTrue();
  });

  it('should render disconnected state text and class', () => {
    component.labelPrefix = 'Zoho Recruit';
    component.state = 'disconnected';
    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;
    const pill = element.querySelector('.status-pill');
    expect(pill?.textContent).toContain('Zoho Recruit: Disconnected');
    expect(pill?.classList.contains('state-disconnected')).toBeTrue();
  });
});
