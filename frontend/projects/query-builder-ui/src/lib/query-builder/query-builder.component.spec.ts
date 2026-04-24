import { ComponentFixture, TestBed } from '@angular/core/testing';

import { QueryBuilderComponent } from './query-builder.component';
import { QuerySpecDraft } from './queryspec-draft.models';

describe('QueryBuilderComponent', () => {
  let fixture: ComponentFixture<QueryBuilderComponent>;
  let emissions: QuerySpecDraft[];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QueryBuilderComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(QueryBuilderComponent);
    emissions = [];
    fixture.componentInstance.draftChange.subscribe((draft) => emissions.push(draft));
    fixture.detectChanges();
  });

  it('renders the business-language builder sections with no application provider', () => {
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.textContent).toContain('Start with');
    expect(compiled.textContent).toContain('Add related data');
    expect(compiled.textContent).toContain('Choose columns');
    expect(compiled.textContent).toContain('Filter rows');
    expect(compiled.textContent).toContain('Parameters');
    expect(compiled.textContent).toContain('Sort & Limit');
    expect(compiled.querySelector('select[aria-label="Primary dataset"]')).toBeTruthy();
  });

  it('starts mostly expanded', () => {
    const expandedTriggers = fixture.nativeElement.querySelectorAll(
      '.qb-section__trigger[aria-expanded="true"]'
    ) as NodeListOf<HTMLButtonElement>;

    expect(expandedTriggers.length).toBe(4);
  });

  it('updates source without changing selected fields', () => {
    changeSelect('Primary dataset', 'invoices');

    expect(lastDraft().source.table).toBe('invoices');
    expect(lastDraft().connection_id).toBe('finance-warehouse');
    expect(lastDraft().select.map((field) => field.label)).toContain('Revenue');
  });

  it('updates joins without changing the source', () => {
    click('[data-testid="customer-join-control"]');

    expect(lastDraft().joins).toEqual([]);
    expect(lastDraft().source.table).toBe('orders');
  });

  it('updates selected columns without changing the source', () => {
    clickButton('Margin');

    expect(lastDraft().select.map((field) => field.label)).not.toContain('Margin');
    expect(lastDraft().source.table).toBe('orders');
  });

  it('updates filters and parameter operands', () => {
    clickButton('Last 30 days');
    expandSection('Parameters');
    changeSelect('Region parameter', 'segment');

    const items = lastDraft().where?.items ?? [];

    expect(items).toContain(
      jasmine.objectContaining({
        left: jasmine.objectContaining({ name: 'order_date' }),
        right: { kind: 'value', value: 'last_30_days' }
      })
    );
    expect(items).toContain(
      jasmine.objectContaining({
        left: jasmine.objectContaining({ name: 'region' }),
        right: { kind: 'param', name: 'segment' }
      })
    );
  });

  it('updates sort, limit, and dialect controls', () => {
    expandSection('Sort & Limit');
    changeSelect('Sort result by', 'Margin');
    changeInput('Row limit', '250');
    changeSelect('Dialect', 'mssql');

    expect(lastDraft().order_by).toEqual([{ label: 'Margin', direction: 'desc' }]);
    expect(lastDraft().limit).toBe(250);
    expect(lastDraft().dialect).toBe('mssql');
  });

  it('emits serializable preview and SQL intent payloads without backend references', () => {
    const previewPayloads: unknown[] = [];
    const sqlPayloads: unknown[] = [];
    fixture.componentInstance.previewRequested.subscribe((payload) => previewPayloads.push(payload));
    fixture.componentInstance.sqlRequested.subscribe((payload) => sqlPayloads.push(payload));

    clickButton('data');
    clickButton('sql');

    expect(JSON.parse(JSON.stringify(previewPayloads[0]))).toEqual(previewPayloads[0] as object);
    expect(JSON.parse(JSON.stringify(sqlPayloads[0]))).toEqual(sqlPayloads[0] as object);
    expect(Object.keys(previewPayloads[0] as object)).toEqual(['draft']);
    expect(Object.keys(sqlPayloads[0] as object)).toEqual(['draft']);
  });

  it('does not render fake compiled SQL or fake result data', () => {
    clickButton('sql');
    expect(fixture.nativeElement.textContent).toContain('SQL intent emitted');
    expect(fixture.nativeElement.textContent).not.toContain('from orders');

    clickButton('data');
    expect(fixture.nativeElement.textContent).toContain('Preview intent emitted');
    expect(fixture.nativeElement.textContent).not.toContain('$428,900');
  });

  function changeSelect(label: string, value: string): void {
    const select = fixture.nativeElement.querySelector(`select[aria-label="${label}"]`) as HTMLSelectElement;

    select.value = value;
    select.dispatchEvent(new Event('change'));
    fixture.detectChanges();
  }

  function changeInput(label: string, value: string): void {
    const input = fixture.nativeElement.querySelector(`input[aria-label="${label}"]`) as HTMLInputElement;

    input.value = value;
    input.dispatchEvent(new Event('change'));
    fixture.detectChanges();
  }

  function clickButton(text: string): void {
    const buttons = Array.from(fixture.nativeElement.querySelectorAll('button')) as HTMLButtonElement[];
    const button = buttons.find((item) => item.textContent?.trim() === text);

    if (!button) {
      throw new Error(`Missing button: ${text}`);
    }

    button.click();
    fixture.detectChanges();
  }

  function expandSection(title: string): void {
    const triggers = Array.from(fixture.nativeElement.querySelectorAll('.qb-section__trigger')) as HTMLButtonElement[];
    const trigger = triggers.find((item) => item.textContent?.includes(title));

    if (!trigger) {
      throw new Error(`Missing section: ${title}`);
    }

    if (trigger.getAttribute('aria-expanded') !== 'true') {
      trigger.click();
      fixture.detectChanges();
    }
  }

  function click(selector: string): void {
    const element = fixture.nativeElement.querySelector(selector) as HTMLButtonElement;

    element.click();
    fixture.detectChanges();
  }

  function lastDraft(): QuerySpecDraft {
    return emissions[emissions.length - 1];
  }
});
