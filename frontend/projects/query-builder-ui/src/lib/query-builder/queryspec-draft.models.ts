// Keep these types plain and serializable. They mirror the QuerySpec JSON boundary,
// not the Python dataclasses or any generated transport client.
export type QuerySpecDialectDraft = 'postgres' | 'mssql';

export type QuerySpecJoinTypeDraft = 'inner' | 'left';

export type QuerySpecPredicateOperatorDraft =
  | '='
  | '!='
  | '>'
  | '>='
  | '<'
  | '<='
  | 'in'
  | 'not_in'
  | 'like'
  | 'not_like'
  | 'is_null'
  | 'is_not_null'
  | 'between';

export type QuerySpecAggregateFunctionDraft = 'count' | 'count_distinct' | 'sum' | 'avg' | 'min' | 'max';

export type QuerySpecScalarDraft = string | number | boolean | null;

export interface QuerySpecColumnRefDraft {
  readonly kind: 'column';
  readonly alias: string;
  readonly name: string;
}

export interface QuerySpecParamRefDraft {
  readonly kind: 'param';
  readonly name: string;
}

export interface QuerySpecValueRefDraft {
  readonly kind: 'value';
  readonly value: QuerySpecScalarDraft;
}

export type QuerySpecOperandDraft = QuerySpecColumnRefDraft | QuerySpecParamRefDraft | QuerySpecValueRefDraft;

export interface QuerySpecPredicateDraft {
  readonly left: QuerySpecColumnRefDraft;
  readonly op: QuerySpecPredicateOperatorDraft;
  readonly right?: QuerySpecOperandDraft | readonly QuerySpecOperandDraft[] | null;
}

export interface QuerySpecFilterGroupDraft {
  readonly op: 'and' | 'or';
  readonly items: readonly (QuerySpecPredicateDraft | QuerySpecFilterGroupDraft)[];
}

export interface QuerySpecSourceDraft {
  readonly table: string;
  readonly alias: string;
}

export interface QuerySpecJoinDraft {
  readonly type: QuerySpecJoinTypeDraft;
  readonly table: string;
  readonly alias: string;
  readonly on: readonly QuerySpecPredicateDraft[];
}

export interface QuerySpecSelectFieldDraft {
  readonly kind: 'column' | 'agg';
  readonly source: QuerySpecColumnRefDraft;
  readonly label: string;
  readonly func?: QuerySpecAggregateFunctionDraft | null;
}

export interface QuerySpecSortDraft {
  readonly label: string;
  readonly direction?: 'asc' | 'desc';
}

export interface QuerySpecDraft {
  readonly version: 1;
  readonly connection_id: string;
  readonly source: QuerySpecSourceDraft;
  readonly select: readonly QuerySpecSelectFieldDraft[];
  readonly joins?: readonly QuerySpecJoinDraft[];
  readonly where?: QuerySpecFilterGroupDraft | null;
  readonly group_by?: readonly QuerySpecColumnRefDraft[];
  readonly order_by?: readonly QuerySpecSortDraft[];
  readonly limit?: number | null;
  readonly dialect?: QuerySpecDialectDraft;
}

export interface QueryBuilderDraftIntent {
  readonly draft: QuerySpecDraft;
}
