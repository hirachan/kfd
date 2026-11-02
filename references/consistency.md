# KFD consistency reference

Read this reference before Knowledge Review for any product-meaning change that touches existing rules. Apply the Consistency gate in `SKILL.md`; these procedures keep the check proportional to the affected concepts, not a project-wide inventory or a new mandatory file.

## Related-rule search

Identify the affected business concepts and search for other Knowledge rules describing the same behavior, including rules in the current unit, undeclared dependencies, and relevant maintained product documents. Search narrowly first; expand only where relevant evidence leads. Do not scan unrelated Knowledge Units merely for completeness.

## Rule applicability check

For a product-meaning change affecting an existing business concept, check the related rules before Knowledge Review:

1. For each related rule, decide whether it remains valid under the new requirement, needs a narrower applicability condition, or is superseded. Include rules left unchanged.
2. Check conditions at newly introduced boundaries and across distinct operations invoking the same business behavior (for example, registration, cancellation, and expiration invoking waitlist promotion).
3. Revise or retire any unconditional rule that no longer applies universally. Prefer referencing a shared rule with `uses` over repeating its conditions in separate operation-specific rules.
4. For rules preserved unchanged, confirm a representative situation where they still apply and, when relevant, a boundary case where their applicability changes.
5. If available intent cannot establish which interpretation is current, use **Decision Required**. Do not infer a new exception merely to reconcile conflicting text.

Keep this check proportional to the changed concept. Do not create a project-wide rule inventory or scan unrelated Knowledge Units.

## Saved Knowledge verification

Before Knowledge Review, and again before completing a product-meaning change:

1. Re-read the actual saved Knowledge files for affected concepts; do not rely on planned edits, patch output, or review prose.
2. Verify that each rule marked revised or retired was actually changed, and that preserved rules remain applicable under the new conditions and relevant operations.
3. If an edit failed or did not land, correct it and re-read the files. An editing failure alone is not a product-meaning decision.
4. Compare active saved rules for incompatible behavior under overlapping applicability conditions. Include relevant rules left unchanged and maintained product documents that claim current normative authority.
5. If a genuine conflict remains, emit **Decision Required** with conflicting rule IDs or locations, overlapping conditions, observable consequences, concrete alternatives, and a justified recommendation when available. Do not silently choose one rule, invent an exception, or declare consistency.
6. Block Knowledge Review and dependent Tests/Implementation until the required human decision is approved and reflected in saved Knowledge. Unrelated work may continue when safely independent.
7. After the decision, revise or retire affected rules, re-read saved files, verify consistency, then present the actual resulting Knowledge for Review. If a material edit follows approval, present the revised Review for approval again.
8. When Python is available, run the bundled linter with `uv run <skill-dir>/scripts/kfd_lint.py <project-root>` or `python3 <skill-dir>/scripts/kfd_lint.py <project-root>` (with PyYAML and jsonschema installed), and fix reported errors. It checks structure, IDs, mapping, dependencies, and conformance references; it does not replace these semantic consistency checks.

Keep verification limited to affected concepts. Do not introduce a project-wide inventory or a new mandatory file.

## Supersession versus conflict

A new explicit requirement can unambiguously supersede an old rule: update the obsolete rule and verify the saved result rather than treating a resolved replacement as a conflict. Revise or replace obsolete rules rather than merely adding contradictory exceptions; keep historical rules only with explicit applicability conditions and follow the rule lifecycle guidance in `SKILL.md`.

If two active saved rules still disagree, do not waive Decision Required merely because one interpretation seems preferable. Knowledge Review approval is not approval of an unresolved conflict resolution. Only a human can approve a decision; silence, timeouts, and the absence of a human are never approval. Reconcile conflicting saved rules only after the decision is approved, then re-check consistency.

## Review and re-review

For a change to an existing business rule, the Knowledge Review briefly identifies related rules revised, preserved (and why still applicable), or retired/superseded, including relevant new boundaries and operations sharing the behavior. Base the review on verified saved files, not intended edits. Present Decision Required first if a material conflict exists; do not request approval of conflicting Knowledge.

Approval must cover the actual resulting saved Knowledge. Material later edits require a revised Knowledge Review and fresh human approval. Before completion, repeat saved Knowledge verification and confirm that obsolete unconditional rules have not been left active.

## Knowledge-preserving bug fixes

Before a fix, check actual saved relevant Knowledge for conflicting active rules. If they conflict, issue Decision Required and block dependent fixes until resolved rather than choosing one rule or inventing an exception. The fix proceeds without Knowledge Review only when the decision required no Knowledge edit. If rules were revised or retired, apply saved Knowledge verification step 7: re-read saved files, verify consistency, and present the actual resulting Knowledge Review for human approval before the dependent fix.
