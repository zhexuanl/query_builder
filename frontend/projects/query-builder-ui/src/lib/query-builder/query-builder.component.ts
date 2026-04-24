import { ChangeDetectionStrategy, Component, signal } from '@angular/core';

type BuilderSectionId =
  | 'start'
  | 'related-data'
  | 'columns'
  | 'filters'
  | 'parameters'
  | 'sort-limit';

type PreviewMode = 'empty' | 'data' | 'sql';

interface BuilderSection {
  readonly id: BuilderSectionId;
  readonly title: string;
  readonly eyebrow: string;
  readonly summary: string;
  readonly chips: readonly string[];
  readonly details: readonly string[];
}

@Component({
  selector: 'qb-query-builder',
  standalone: true,
  templateUrl: './query-builder.component.html',
  styleUrl: './query-builder.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class QueryBuilderComponent {
  protected readonly sections: readonly BuilderSection[] = [
    {
      id: 'start',
      title: 'Start with',
      eyebrow: 'Primary dataset',
      summary: 'Choose the governed source that anchors the query.',
      chips: ['Orders', 'Production', 'Certified'],
      details: ['Dataset: Orders', 'Owner: Revenue Operations', 'Freshness: 12 minutes']
    },
    {
      id: 'related-data',
      title: 'Add related data',
      eyebrow: 'Relationship path',
      summary: 'Join trusted customer context without exposing join syntax.',
      chips: ['Customers', 'Left join'],
      details: ['Orders.customer_id -> Customers.id', 'Relationship quality: verified']
    },
    {
      id: 'columns',
      title: 'Choose columns',
      eyebrow: 'Readable output',
      summary: 'Keep the result focused on metrics an analyst can act on.',
      chips: ['6 fields', '2 metrics'],
      details: ['Order date, customer segment, region', 'Revenue, margin, fulfilment status']
    },
    {
      id: 'filters',
      title: 'Filter rows',
      eyebrow: 'Business rules',
      summary: 'Constrain the slice before expensive preview execution.',
      chips: ['Last 90 days', 'Active regions'],
      details: ['Order date is within the last 90 days', 'Region is not archived']
    },
    {
      id: 'parameters',
      title: 'Parameters',
      eyebrow: 'Reusable inputs',
      summary: 'Promote common values to named controls for repeat runs.',
      chips: ['Region', 'Minimum margin'],
      details: ['region = APAC', 'minimum_margin = 18%']
    },
    {
      id: 'sort-limit',
      title: 'Sort & Limit',
      eyebrow: 'Result guardrails',
      summary: 'Make the preview deterministic and bounded.',
      chips: ['Revenue desc', '500 rows'],
      details: ['Sort by revenue descending', 'Limit preview to 500 rows']
    }
  ];

  protected readonly previewModes: readonly PreviewMode[] = ['empty', 'data', 'sql'];
  protected readonly expandedSections = signal<ReadonlySet<BuilderSectionId>>(
    new Set(['start', 'related-data', 'columns', 'filters'])
  );
  protected readonly previewMode = signal<PreviewMode>('data');

  protected readonly previewRows = [
    ['2026-04-22', 'Enterprise', 'APAC', '$428,900', '31.4%', 'Approved'],
    ['2026-04-21', 'Strategic', 'EMEA', '$392,180', '28.9%', 'Review'],
    ['2026-04-20', 'Commercial', 'AMER', '$241,760', '24.2%', 'Approved']
  ] as const;

  protected readonly previewSql = [
    'select',
    '  o.order_date,',
    '  c.segment,',
    '  o.region,',
    '  sum(o.revenue) as revenue,',
    '  avg(o.margin) as margin',
    'from orders o',
    'left join customers c on o.customer_id = c.id',
    'where o.order_date >= current_date - interval \'90 days\'',
    'order by revenue desc',
    'limit 500;'
  ].join('\n');

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

  protected selectPreviewMode(mode: PreviewMode): void {
    this.previewMode.set(mode);
  }
}
