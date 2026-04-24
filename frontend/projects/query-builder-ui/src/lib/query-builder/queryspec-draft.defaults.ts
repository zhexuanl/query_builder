import { CUSTOMER_JOIN, SELECT_FIELDS, SORT_OPTIONS } from './query-builder-shell.config';
import type { QuerySpecColumnRefDraft, QuerySpecDraft } from './queryspec-draft.models';

// This is a usable starting draft, not persisted sample data or a backend fixture.
export function createDefaultQuerySpecDraft(): QuerySpecDraft {
  const orderDate: QuerySpecColumnRefDraft = { kind: 'column', alias: 'o', name: 'order_date' };
  const region: QuerySpecColumnRefDraft = { kind: 'column', alias: 'o', name: 'region' };
  const segment: QuerySpecColumnRefDraft = { kind: 'column', alias: 'c', name: 'segment' };

  return {
    version: 1,
    connection_id: 'revenue-warehouse',
    dialect: 'postgres',
    source: {
      table: 'orders',
      alias: 'o'
    },
    joins: [CUSTOMER_JOIN],
    select: SELECT_FIELDS,
    where: {
      op: 'and',
      items: [
        {
          left: orderDate,
          op: '>=',
          right: { kind: 'param', name: 'start_date' }
        },
        {
          left: region,
          op: '=',
          right: { kind: 'param', name: 'region' }
        }
      ]
    },
    group_by: [orderDate, segment, region],
    order_by: [SORT_OPTIONS[0]],
    limit: 500
  };
}
