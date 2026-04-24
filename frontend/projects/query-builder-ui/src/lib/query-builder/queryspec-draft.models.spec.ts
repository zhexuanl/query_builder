import {
  QuerySpecDialectDraft,
  QuerySpecDraft,
  QuerySpecOperandDraft
} from './queryspec-draft.models';
import { createDefaultQuerySpecDraft } from './queryspec-draft.defaults';

describe('QuerySpecDraft model contract', () => {
  it('uses discriminated operand kinds', () => {
    const operands: readonly QuerySpecOperandDraft[] = [
      { kind: 'column', alias: 'o', name: 'region' },
      { kind: 'param', name: 'region' },
      { kind: 'value', value: 'APAC' }
    ];

    expect(operands.map((operand) => operand.kind)).toEqual(['column', 'param', 'value']);
  });

  it('narrows dialect values to supported compiler targets', () => {
    const dialects: readonly QuerySpecDialectDraft[] = ['postgres', 'mssql'];

    expect(dialects).toEqual(['postgres', 'mssql']);
  });

  it('creates a JSON-serializable representative draft shape', () => {
    const draft = createDefaultQuerySpecDraft() satisfies QuerySpecDraft;
    const parsed = JSON.parse(JSON.stringify(draft)) as QuerySpecDraft;

    expect(parsed.version).toBe(1);
    expect(parsed.connection_id).toBe('revenue-warehouse');
    expect(parsed.source.table).toBe('orders');
    expect('on' in parsed.source).toBeFalse();
    expect('type' in parsed.source).toBeFalse();
    expect(parsed.joins?.[0].type).toBe('left');
    expect(parsed.select.length).toBeGreaterThan(0);
    expect(parsed.where?.items.length).toBeGreaterThan(0);
    expect(parsed.where?.items[0]).toEqual(
      jasmine.objectContaining({
        right: { kind: 'param', name: 'start_date' }
      })
    );
    expect(parsed.order_by?.[0]).toEqual({ label: 'Revenue', direction: 'desc' });
  });
});
