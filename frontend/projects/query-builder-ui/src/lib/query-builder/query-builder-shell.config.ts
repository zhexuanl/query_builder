import type {
  QuerySpecDialectDraft,
  QuerySpecJoinDraft,
  QuerySpecSelectFieldDraft,
  QuerySpecSortDraft
} from './queryspec-draft.models';

// Bounded shell options prove the draft contract without pretending to be a catalog browser.
export type BuilderSectionId =
  | 'start'
  | 'related-data'
  | 'columns'
  | 'filters'
  | 'parameters'
  | 'sort-limit';

export type PreviewMode = 'empty' | 'data' | 'sql';

export interface BuilderSection {
  readonly id: BuilderSectionId;
  readonly title: string;
  readonly eyebrow: string;
  readonly summary: string;
}

export interface SourceOption {
  readonly label: string;
  readonly table: string;
  readonly connectionId: string;
}

export const BUILDER_SECTIONS: readonly BuilderSection[] = [
  {
    id: 'start',
    title: 'Start with',
    eyebrow: 'Primary dataset',
    summary: 'Choose the governed source that anchors the query.'
  },
  {
    id: 'related-data',
    title: 'Add related data',
    eyebrow: 'Relationship path',
    summary: 'Join trusted customer context without exposing join syntax.'
  },
  {
    id: 'columns',
    title: 'Choose columns',
    eyebrow: 'Readable output',
    summary: 'Keep the result focused on metrics an analyst can act on.'
  },
  {
    id: 'filters',
    title: 'Filter rows',
    eyebrow: 'Business rules',
    summary: 'Constrain the slice before expensive preview execution.'
  },
  {
    id: 'parameters',
    title: 'Parameters',
    eyebrow: 'Reusable inputs',
    summary: 'Promote runtime values to named controls for repeat runs.'
  },
  {
    id: 'sort-limit',
    title: 'Sort & Limit',
    eyebrow: 'Result guardrails',
    summary: 'Make the preview deterministic and bounded.'
  }
];

export const SOURCE_OPTIONS: readonly SourceOption[] = [
  { label: 'Orders', table: 'orders', connectionId: 'revenue-warehouse' },
  { label: 'Invoices', table: 'invoices', connectionId: 'finance-warehouse' }
];

export const CUSTOMER_JOIN: QuerySpecJoinDraft = {
  type: 'left',
  table: 'customers',
  alias: 'c',
  on: [
    {
      left: { kind: 'column', alias: 'o', name: 'customer_id' },
      op: '=',
      right: { kind: 'column', alias: 'c', name: 'id' }
    }
  ]
};

export const SELECT_FIELDS: readonly QuerySpecSelectFieldDraft[] = [
  { kind: 'column', source: { kind: 'column', alias: 'o', name: 'order_date' }, label: 'Order date' },
  { kind: 'column', source: { kind: 'column', alias: 'c', name: 'segment' }, label: 'Segment' },
  { kind: 'column', source: { kind: 'column', alias: 'o', name: 'region' }, label: 'Region' },
  { kind: 'agg', source: { kind: 'column', alias: 'o', name: 'revenue' }, label: 'Revenue', func: 'sum' },
  { kind: 'agg', source: { kind: 'column', alias: 'o', name: 'margin' }, label: 'Margin', func: 'avg' }
];

export const SORT_OPTIONS: readonly QuerySpecSortDraft[] = [
  { label: 'Revenue', direction: 'desc' },
  { label: 'Margin', direction: 'desc' },
  { label: 'Order date', direction: 'asc' }
];

export const DATE_WINDOWS = ['last_90_days', 'last_30_days'] as const;

export type DateWindow = (typeof DATE_WINDOWS)[number];

export const PARAMETER_NAMES = ['region', 'segment'] as const;

export const DIALECT_OPTIONS: readonly QuerySpecDialectDraft[] = ['postgres', 'mssql'];

export const PREVIEW_MODES: readonly PreviewMode[] = ['empty', 'data', 'sql'];
