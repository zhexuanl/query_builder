import {
  CUSTOMER_JOIN,
  SELECT_FIELDS,
} from './query-builder-shell.config';
import type { DateWindow, SourceOption } from './query-builder-shell.config';
import type {
  QuerySpecDialectDraft,
  QuerySpecDraft,
  QuerySpecFilterGroupDraft,
  QuerySpecOperandDraft,
  QuerySpecParamRefDraft,
  QuerySpecPredicateDraft,
  QuerySpecSelectFieldDraft,
  QuerySpecSortDraft
} from './queryspec-draft.models';

// Pure draft mutations live here so Angular components stay thin and service-free.
export function updateDraftSource(draft: QuerySpecDraft, option: SourceOption): QuerySpecDraft {
  return {
    ...draft,
    connection_id: option.connectionId,
    source: {
      ...draft.source,
      table: option.table
    }
  };
}

export function updateCustomerJoin(draft: QuerySpecDraft, enabled: boolean): QuerySpecDraft {
  return {
    ...draft,
    joins: enabled ? [CUSTOMER_JOIN] : []
  };
}

export function isCustomerJoinEnabled(draft: QuerySpecDraft): boolean {
  return (draft.joins ?? []).some((join) => join.table === CUSTOMER_JOIN.table);
}

export function updateSelectedField(draft: QuerySpecDraft, label: string): QuerySpecDraft {
  const selected = draft.select.some((field) => field.label === label);
  const nextSelect = selected
    ? draft.select.filter((field) => field.label !== label)
    : [...draft.select, findSelectField(label)];

  // QuerySpec requires at least one selected field; the UI should never emit an invalid empty select.
  if (nextSelect.length === 0) {
    return draft;
  }

  return {
    ...draft,
    select: nextSelect
  };
}

export function isSelectFieldEnabled(draft: QuerySpecDraft, label: string): boolean {
  return draft.select.some((field) => field.label === label);
}

export function updateDateWindow(draft: QuerySpecDraft, window: DateWindow): QuerySpecDraft {
  return updateWhere(draft, (where) => ({
    ...where,
    items: where.items.map((item) =>
      isPredicateForColumn(item, 'order_date')
        ? {
            ...item,
            right: { kind: 'value', value: window }
          }
        : item
    )
  }));
}

export function currentDateWindow(draft: QuerySpecDraft): string {
  const right = findPredicate(draft, 'order_date')?.right;

  return isValueOperand(right) && typeof right.value === 'string' ? right.value : 'runtime parameter';
}

export function updateRegionParameter(draft: QuerySpecDraft, parameterName: string): QuerySpecDraft {
  return updateWhere(draft, (where) => ({
    ...where,
    items: where.items.map((item) =>
      isPredicateForColumn(item, 'region')
        ? {
            ...item,
            right: { kind: 'param', name: parameterName }
          }
        : item
    )
  }));
}

export function currentRegionParameter(draft: QuerySpecDraft): string {
  const right = findPredicate(draft, 'region')?.right;

  return isParamOperand(right) ? right.name : 'region';
}

export function updateSort(draft: QuerySpecDraft, sort: QuerySpecSortDraft): QuerySpecDraft {
  return {
    ...draft,
    order_by: [sort]
  };
}

export function updateLimit(draft: QuerySpecDraft, limit: number): QuerySpecDraft {
  if (!Number.isFinite(limit) || limit < 1) {
    return draft;
  }

  return {
    ...draft,
    limit
  };
}

export function updateDialect(draft: QuerySpecDraft, dialect: QuerySpecDialectDraft): QuerySpecDraft {
  return {
    ...draft,
    dialect
  };
}

function updateWhere(
  draft: QuerySpecDraft,
  update: (where: QuerySpecFilterGroupDraft) => QuerySpecFilterGroupDraft
): QuerySpecDraft {
  return {
    ...draft,
    where: update(draft.where ?? { op: 'and', items: [] })
  };
}

function findSelectField(label: string): QuerySpecSelectFieldDraft {
  const field = SELECT_FIELDS.find((item) => item.label === label);

  if (!field) {
    throw new Error(`Unknown select field: ${label}`);
  }

  return field;
}

function findPredicate(draft: QuerySpecDraft, columnName: string): QuerySpecPredicateDraft | undefined {
  return draft.where?.items.find((item): item is QuerySpecPredicateDraft => isPredicateForColumn(item, columnName));
}

function isPredicateForColumn(
  item: QuerySpecPredicateDraft | QuerySpecFilterGroupDraft,
  columnName: string
): item is QuerySpecPredicateDraft {
  return 'left' in item && item.left.name === columnName;
}

function isValueOperand(right: QuerySpecPredicateDraft['right']): right is Extract<QuerySpecOperandDraft, { kind: 'value' }> {
  if (!right || Array.isArray(right)) {
    return false;
  }

  return (right as QuerySpecOperandDraft).kind === 'value';
}

function isParamOperand(right: QuerySpecPredicateDraft['right']): right is QuerySpecParamRefDraft {
  if (!right || Array.isArray(right)) {
    return false;
  }

  return (right as QuerySpecOperandDraft).kind === 'param';
}
