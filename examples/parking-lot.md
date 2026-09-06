# Parking Lot

## Event commerce

The event system should eventually cover insurance, merchandise, refunds,
and administrator operations beyond the currently implemented entry flow.

## Observations

- [risk] 決済Webhookの遅延時に注文確定処理との競合が起きないか確認したい。
- [refactor] 支払いサービスの責務が広がっており、今後の変更で読む範囲が増えそう。
- [missing-test] 返金済み注文の表示について境界ケースのテストが薄い。
