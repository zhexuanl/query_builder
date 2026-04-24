import { ComponentFixture, TestBed } from '@angular/core/testing';

import { QueryBuilderComponent } from './query-builder.component';

describe('QueryBuilderComponent', () => {
  let fixture: ComponentFixture<QueryBuilderComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QueryBuilderComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(QueryBuilderComponent);
    fixture.detectChanges();
  });

  it('renders the business-language builder sections', () => {
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.textContent).toContain('Start with');
    expect(compiled.textContent).toContain('Add related data');
    expect(compiled.textContent).toContain('Choose columns');
    expect(compiled.textContent).toContain('Filter rows');
    expect(compiled.textContent).toContain('Parameters');
    expect(compiled.textContent).toContain('Sort & Limit');
  });

  it('starts mostly expanded', () => {
    const expandedTriggers = fixture.nativeElement.querySelectorAll(
      '.qb-section__trigger[aria-expanded="true"]'
    ) as NodeListOf<HTMLButtonElement>;

    expect(expandedTriggers.length).toBe(4);
  });

  it('switches preview modes with local component state', () => {
    const buttons = fixture.nativeElement.querySelectorAll('.qb-mode-button') as NodeListOf<HTMLButtonElement>;

    buttons[2].click();
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.qb-sql')?.textContent).toContain('select');
  });
});
