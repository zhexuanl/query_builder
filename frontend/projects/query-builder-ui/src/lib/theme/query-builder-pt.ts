export const QUERY_BUILDER_PT = {
  button: {
    root: [
      'inline-flex items-center justify-center gap-2',
      'rounded-[14px] border border-transparent',
      'bg-[var(--qb-accent-primary)] px-4 py-2',
      'font-semibold text-white shadow-sm',
      'transition-colors duration-150',
      'hover:bg-[var(--qb-accent-primary-hover)]',
      'focus-visible:outline focus-visible:outline-2',
      'focus-visible:outline-offset-2',
      'focus-visible:outline-[var(--qb-accent-primary)]',
      'disabled:pointer-events-none disabled:opacity-50'
    ].join(' '),
    label: 'text-sm leading-5 tracking-[-0.01em]',
    icon: 'text-current'
  }
} as const;
