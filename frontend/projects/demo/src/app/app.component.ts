import { Component } from '@angular/core';
import { QueryBuilderComponent } from '@query-builder/ui';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [QueryBuilderComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {}
