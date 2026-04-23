# CLAUDE.md

Behavioral guidelines. Bias toward caution over speed — use judgment for trivial tasks.

## 1. Think Before Coding

- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so and push back.

## 2. Simplicity First

- No features beyond what was asked. No speculative abstractions.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

## 3. Surgical Changes

- Touch only what you must. Don't improve adjacent code.
- Match existing style. Remove only imports/symbols YOUR changes made unused.

## 4. Goal-Driven Execution

Transform tasks into verifiable goals: "Add validation" → write failing tests, make them pass.
State a brief plan with verify steps before starting any multi-step task.

---

## 5. Phase-Gated Development

Each milestone (M0–M6) is a discrete shipping unit. Never blend phases.

```
1. Implement phase scope — nothing beyond it
2. Adversarial review §6 on all changed files
3. Fix blockers
4. Commit — "MN: description" — tests green, no TODOs, no commented-out code
5. Archive with /opsx:archive (§8)
```

---

## 6. Adversarial Review (required before every phase commit)

Spawn a `code-reviewer` agent over all files touched in the phase. Cover:

- **Clean Architecture**: domain importing adapters/infra; ORM models in domain; ports referencing concrete types
- **Domain design**: anemic model; missing invariants; mutable where frozen is correct; overly broad ports
- **Anti-patterns**: god objects; feature envy; primitive obsession; speculative generality
- **Performance**: N+1 queries; redundant validation; unnecessary allocations in hot paths

Design-level issues requiring a choice between two approaches → invoke decision-gate §7 first.

---

## 7. Decision Gate

Use the `decision-gate` skill before any choice that is expensive to reverse:

| Trigger | Example |
|---|---|
| New port in `domain/interfaces/` | `IQueryOptimizer` vs fold into `IQueryCompiler` |
| QuerySpec AST shape change | New field alters the serialised contract |
| Two viable adapter implementations | SQLAlchemy Core vs SQLGlot as primary compiler |
| App DB schema migration | Altering audit or catalog tables |

Skip for style preferences or adding a method with only one implementation.
Record the gate output in the PR description or plan file — not lost in chat.

---

## 8. OpenSpec Workflow

| Skill | Command | When |
|---|---|---|
| `openspec-explore` | `/opsx:explore` | Think/diagram before proposing. No code. |
| `openspec-propose` | `/opsx:propose` | Start of milestone — generates proposal.md, design.md, tasks.md. |
| `openspec-apply-change` | `/opsx:apply` | Implement tasks one by one. |
| `openspec-archive-change` | `/opsx:archive` | After commit — archives and syncs delta specs to main specs. |

Per-milestone sequence:
```
1. /opsx:explore <milestone>          ← optional
2. /opsx:propose <milestone>          ← artifacts before any code
   └─ expensive design choice → decision-gate §7
3. /opsx:apply <milestone>            ← implement all tasks
4. Adversarial review §6 → fix blockers
5. git commit "MN: …"
6. /opsx:archive <milestone>
```

Apply rules: mark `- [x]` immediately after each task; pause on design issues or ambiguity; never commit with open `- [ ]` tasks.
