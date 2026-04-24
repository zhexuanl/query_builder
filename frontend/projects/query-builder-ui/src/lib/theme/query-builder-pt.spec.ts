import { QUERY_BUILDER_PT } from './query-builder-pt';

describe('QUERY_BUILDER_PT', () => {
  it('applies the primary query builder button foundation', () => {
    const buttonRoot = QUERY_BUILDER_PT.button?.root ?? '';

    expect(buttonRoot).toContain('rounded-[14px]');
    expect(buttonRoot).toContain('bg-[var(--qb-accent-primary)]');
  });
});
