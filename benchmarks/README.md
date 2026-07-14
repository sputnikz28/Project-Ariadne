# benchmarks/

Structure only — no benchmark runner exists yet. This is scaffolding
for comparing faction/strategy performance against a neutral baseline,
once that runner is built.

- `random/` — baseline runs from pure random key selection, for
  comparison against every faction's actual performance.
- `reports/` — human-readable benchmark comparison reports.
- `rankings/` — machine-readable faction/strategy leaderboards.

Nothing here is generated automatically today. `experiments/` remains
the home for actual simulation and Axiomantes-ritual outputs;
`benchmarks/` is specifically for strategy-vs-strategy comparison
results once that infrastructure is implemented.
