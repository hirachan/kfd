# Parking Lot and Checkpoint reference

## Parking Lot

`parking-lot.md` is pre-Knowledge. It preserves valuable intent or observations that are not part of current implementation work.

Good Parking Lot entries are:

- short;
- coarse;
- useful later;
- clearly outside the current implementation slice.

Typical categories include future product intent, suspected bugs, refactor opportunities, missing tests, design inconsistencies, and unresolved questions.

Parking Lot entries are not approved requirements and do not authorize implementation.

Do not use checkboxes, done/pending states, complete task inventories, or detailed implementation plans. When an item becomes current work, refine the relevant meaning into Knowledge and remove or rewrite the parked entry.

The agent may append useful side discoveries without asking for permission merely to record them, but must not expand current scope because of them.

See `examples/parking-lot.md` for a worked example.

## Checkpoint

`checkpoint.yaml` is optional short-term resume memory for interrupted agent work.

Use it only when a future session would materially benefit from knowing the active area and a small amount of resume context.

Recommended shape:

```yaml
focus: participant-order-history
note: 注文履歴の表示実装を確認中。次は返金状態の表示経路から再開する。
```

Do not put these into a Checkpoint:

- complete or partial status lists;
- completed-task inventories;
- copies of Knowledge rules;
- implementation summaries that can be rediscovered cheaply;
- progress-ledger data.

Clear the Checkpoint when there is no meaningful interrupted context to preserve.
