# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---

## 5. Phase-Gated Development

Each milestone (M0, M1, M2 …) is a discrete shipping unit. Never blend phases.

**Per-phase workflow:**
```
1. Implement the phase scope — nothing beyond it
2. Run adversarial review (§6) on all changed files
3. Fix any blockers surfaced by review
4. Commit — message scoped to the phase, e.g. "M1: compiler spike – SQLAlchemy Core + golden tests"
5. Proceed to next phase only after commit is clean
```

Each commit should be self-contained: tests green, no TODOs introduced, no commented-out code.

---

## 6. Adversarial Review (required before every phase commit)

Before committing, spawn a `code-reviewer` agent or adversarial `Agent` pass over all files touched in the phase. The review must cover:

**Clean Architecture violations**
- Domain (`domain/`) importing from `adapters/` or `infrastructure/`
- Use cases holding HTTP, ORM, or framework knowledge
- ORM models or Pydantic validators appearing inside `domain/`
- Ports (interfaces) referencing concrete types from adapters

**Domain design anti-patterns**
- Anemic domain model — entities with no behaviour, all logic in use cases
- Missing invariants — value objects that allow invalid state to be constructed
- Mutable state where frozen/immutable is correct
- Overly broad port interfaces (one method per port is a smell)

**General anti-patterns**
- God objects / god use cases doing too many things
- Feature envy — a class operating mostly on another class's data
- Primitive obsession — raw strings/ints where a value object belongs
- Speculative generality — abstractions with no second implementation

**Performance**
- N+1 query patterns in repository adapters
- Redundant validation passes (validate once at the boundary, trust inside)
- Unnecessary allocations in hot compilation paths

If the review finds a **design-level issue** (not just a code smell) that requires choosing between two approaches, invoke the `decision-gate` skill before making the change (see §7).

---

## 7. Decision Gate

Use the `decision-gate` skill before committing to any choice that would be **expensive to reverse**:

| Trigger | Example |
|---|---|
| New port in `domain/interfaces/` | Adding `IQueryOptimizer` vs folding into `IQueryCompiler` |
| QuerySpec AST shape change | Adding a new field that changes the serialised contract |
| Cross-layer contract change | Changing `CompiledQuery` NamedTuple fields |
| Two viable adapter implementations | SQLAlchemy Core vs SQLGlot as primary compiler |
| Schema migration on the app DB | Altering audit or catalog tables |

**Skip the decision gate for:** trivial implementation choices, style preferences, adding a method to an existing port that has only one implementation.

The gate output must be recorded in a comment in the PR or plan file — not lost in chat.

---

## 8. OpenSpec Workflow

Every milestone uses the OpenSpec system for structured change management. Four skills cover the full lifecycle:

| Skill | Command | When |
|---|---|---|
| `openspec-explore` | `/opsx:explore` | Before proposing — think, diagram, diagnose. No code. |
| `openspec-propose` | `/opsx:propose` | Start of every milestone — generates all artifacts before a line is written. |
| `openspec-apply-change` | `/opsx:apply` | Implementation — works through `tasks.md` task by task. |
| `openspec-archive-change` | `/opsx:archive` | After the phase commit — archives and syncs delta specs to main specs. |

### Full per-milestone sequence

```
1.  /opsx:explore <milestone>        ← optional; think before proposing
2.  /opsx:propose <milestone>        ← generates proposal.md, design.md, tasks.md
    └─ if design.md requires an expensive choice → invoke decision-gate (§7)
3.  /opsx:apply <milestone>          ← implements all tasks in tasks.md
4.  Adversarial review (§6)          ← spawn code-reviewer agent over all changed files
5.  Fix blockers from review
6.  git commit "MN: …"
7.  /opsx:archive <milestone>        ← archives change; optionally syncs delta specs
```

### Artifact locations

```
openspec/
├── config.yaml                      ← project context fed to AI on every artifact creation
├── specs/<capability>/spec.md       ← canonical capability specs (long-lived)
└── changes/
    ├── <name>/
    │   ├── .openspec.yaml
    │   ├── proposal.md              ← what & why
    │   ├── design.md                ← how (ports, data shapes, key decisions)
    │   ├── tasks.md                 ← implementation checklist
    │   └── specs/                   ← delta specs merged into openspec/specs/ on archive
    └── archive/
        └── YYYY-MM-DD-<name>/       ← immutable record after archival
```

### CLI reference

```bash
openspec list --json                                    # list active changes
openspec new change "<name>"                            # scaffold a new change
openspec status --change "<name>" --json                # artifact completion graph
openspec instructions <artifact-id> --change "<name>" --json   # generation instructions
openspec instructions apply --change "<name>" --json    # apply/task instructions
```

### Project context

Keep `openspec/config.yaml` current. The `context:` field is injected into every artifact generation prompt — stale context produces misaligned artifacts.

```yaml
# openspec/config.yaml
schema: spec-driven
context: |
  Python 3.12, FastAPI, SQLAlchemy Core (primary compiler), SQLGlot (lint)
  Clean Architecture: domain / use_cases / adapters / infrastructure
  Target dialects: Postgres + SQL Server (both first-party SQLAlchemy dialects)
  Angular frontend, custom components (no query-builder library)
  Google-style docstrings. No decorative inline comments.
  Commits scoped to milestone: "MN: <description>"
```

### Rules for `openspec-apply-change`

- Mark each task `- [x]` immediately after completion — never batch.
- If a task reveals a design issue, pause and update `design.md` before continuing.
- If a task is ambiguous, pause and ask — don't guess.
- Apply the adversarial review (§6) and commit only after all tasks are `- [x]`.