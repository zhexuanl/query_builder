import { JsonPipe } from '@angular/common';
import { Component, signal } from '@angular/core';
import { QueryBuilderComponent, type QueryBuilderDraftIntent, type QuerySpecDraft } from '@query-builder/ui';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [JsonPipe, QueryBuilderComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  readonly latestDraft = signal<QuerySpecDraft | null>(null);
  readonly latestIntent = signal<{ readonly type: 'preview' | 'sql'; readonly payload: QueryBuilderDraftIntent } | null>(
    null
  );

  recordDraft(draft: QuerySpecDraft): void {
    this.latestDraft.set(draft);
  }

  recordPreview(payload: QueryBuilderDraftIntent): void {
    this.latestIntent.set({ type: 'preview', payload });
  }

  recordSql(payload: QueryBuilderDraftIntent): void {
    this.latestIntent.set({ type: 'sql', payload });
  }
}
