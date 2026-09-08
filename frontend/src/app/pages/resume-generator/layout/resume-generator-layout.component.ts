import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-resume-generator-layout',
  standalone: true,
  imports: [RouterOutlet],
  template: `
    <div class="resume-generator-layout">
      <router-outlet></router-outlet>
    </div>
  `,
  styles: [`
    .resume-generator-layout {
      background-color: var(--page-bg);
    }
  `],
})
export class ResumeGeneratorLayoutComponent {}
