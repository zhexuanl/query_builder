import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output, computed, signal } from '@angular/core';

import {
  BUILDER_SECTIONS,
  DATE_WINDOWS,
  DIALECT_OPTIONS,
  PARAMETER_NAMES,
  PREVIEW_MODES,
  SORT_OPTIONS,
  SOURCE_OPTIONS,
  SELECT_FIELDS
} from './query-builder-shell.config';
import type { BuilderSectionId } from './query-builder-shell.config';
import { createDefaultQuerySpecDraft } from './queryspec-draft.defaults';
import type { QueryBuilderDraftIntent, QuerySpecDialectDraft, QuerySpecDraft } from './queryspec-draft.models';
import {
  currentDateWindow,
  currentRegionParameter,
  isCustomerJoinEnabled,
  isSelectFieldEnabled,
  updateCustomerJoin,
  updateDateWindow,
  updateDialect,
  updateDraftSource,
  updateLimit,
  updateRegionParameter,
  updateSelectedField,
  updateSort
} from './queryspec-draft.updaters';

@Component({
  selector: 'qb-query-builder',
  standalone: true,
  templateUrl: './query-builder.component.html',
  styleUrl: './query-builder.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class QueryBuilderComponent {
  @Input()
  set draft(value: QuerySpecDraft | null | undefined) {
    if (value) {
      this.draftState.set(value);
    }
  }

  @Output() readonly draftChange = new EventEmitter<QuerySpecDraft>();
  @Output() readonly previewRequested = new EventEmitter<QueryBuilderDraftIntent>();
  @Output() readonly sqlRequested = new EventEmitter<QueryBuilderDraftIntent>();

  protected readonly sections = BUILDER_SECTIONS;
  protected readonly sourceOptions = SOURCE_OPTIONS;
  protected readonly selectFields = SELECT_FIELDS;
  protected readonly previewModes = PREVIEW_MODES;
  protected readonly dateWindows = DATE_WINDOWS;
  protected readonly parameterNames = PARAMETER_NAMES;
  protected readonly sortOptions = SORT_OPTIONS;
  protected readonly dialectOptions = DIALECT_OPTIONS;

  private readonly draftState = signal<QuerySpecDraft>(createDefaultQuerySpecDraft());

  protected readonly currentDraft = computed(() => this.draftState());
  protected readonly expandedSections = signal<ReadonlySet<BuilderSectionId>>(
    new Set(['start', 'related-data', 'columns', 'filters'])
  );
  protected readonly previewMode = signal<(typeof PREVIEW_MODES)[number]>('data');

  protected isSectionExpanded(sectionId: BuilderSectionId): boolean {
    return this.expandedSections().has(sectionId);
  }

  protected toggleSection(sectionId: BuilderSectionId): void {
    const next = new Set(this.expandedSections());

    if (next.has(sectionId)) {
      next.delete(sectionId);
    } else {
      next.add(sectionId);
    }

    this.expandedSections.set(next);
  }

  protected selectPreviewMode(mode: (typeof PREVIEW_MODES)[number]): void {
    this.previewMode.set(mode);

    if (mode === 'data') {
      this.previewRequested.emit({ draft: this.currentDraft() });
    }

    if (mode === 'sql') {
      this.sqlRequested.emit({ draft: this.currentDraft() });
    }
  }

  protected sourceChanged(event: Event): void {
    const table = readValue(event);
    const option = this.sourceOptions.find((item) => item.table === table);

    if (option) {
      this.commitDraft(updateDraftSource(this.currentDraft(), option));
    }
  }

  protected setCustomerJoin(enabled: boolean): void {
    this.commitDraft(updateCustomerJoin(this.currentDraft(), enabled));
  }

  protected isCustomerJoinEnabled(): boolean {
    return isCustomerJoinEnabled(this.currentDraft());
  }

  protected toggleSelectField(label: string): void {
    this.commitDraft(updateSelectedField(this.currentDraft(), label));
  }

  protected isSelectFieldEnabled(label: string): boolean {
    return isSelectFieldEnabled(this.currentDraft(), label);
  }

  protected setDateWindow(window: (typeof DATE_WINDOWS)[number]): void {
    this.commitDraft(updateDateWindow(this.currentDraft(), window));
  }

  protected currentDateWindow(): string {
    return currentDateWindow(this.currentDraft());
  }

  protected parameterChanged(event: Event): void {
    this.commitDraft(updateRegionParameter(this.currentDraft(), readValue(event)));
  }

  protected currentRegionParameter(): string {
    return currentRegionParameter(this.currentDraft());
  }

  protected sortChanged(event: Event): void {
    const label = readValue(event);
    const sort = this.sortOptions.find((item) => item.label === label);

    if (sort) {
      this.commitDraft(updateSort(this.currentDraft(), sort));
    }
  }

  protected limitChanged(event: Event): void {
    this.commitDraft(updateLimit(this.currentDraft(), Number(readValue(event))));
  }

  protected dialectChanged(event: Event): void {
    const dialect = readValue(event) as QuerySpecDialectDraft;

    if (this.dialectOptions.includes(dialect)) {
      this.commitDraft(updateDialect(this.currentDraft(), dialect));
    }
  }

  // Centralize write + emit so future validation can be inserted without hunting through template handlers.
  private commitDraft(next: QuerySpecDraft): void {
    this.draftState.set(next);
    this.draftChange.emit(next);
  }
}

function readValue(event: Event): string {
  return (event.target as HTMLInputElement | HTMLSelectElement).value;
}
