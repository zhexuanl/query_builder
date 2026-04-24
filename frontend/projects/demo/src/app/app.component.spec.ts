import { TestBed } from '@angular/core/testing';
import { AppComponent } from './app.component';

describe('AppComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AppComponent],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should render the query builder shell', () => {
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('qb-query-builder')).toBeTruthy();
  });

  it('should capture emitted draft output locally', () => {
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    const select = fixture.nativeElement.querySelector(
      'select[aria-label="Primary dataset"]'
    ) as HTMLSelectElement;

    select.value = 'invoices';
    select.dispatchEvent(new Event('change'));
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('finance-warehouse');
    expect(fixture.nativeElement.textContent).toContain('invoices');
  });
});
