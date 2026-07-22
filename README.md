# edge-governor — the meaningfulness governor + live-edge hunter

One authority that decides whether the live MEV system has a **real, meaningful,
capturable edge** — and if not, **where to hunt for one**. Built to end the
ad-hoc-piecemeal failure mode: sub-meaningful lanes dressed up as progress, and
false-greens (the 108-score backrun that nets $0, the HIP-3 "+$28" that's a 57×
touch-model artifact) surfaced as "top lane."

## What it does

```
ingest.py   read every live lane surface -> normalize (strict-net, capital, landable, proven)
gate.py     the truth filter: a candidate PASSES only if it is real (strict net > 0,
            not an artifact), transactable (not phantom), landable (no builder seat),
            real-capital-sized, non-toxic, AND meaningful (>= $/day bar OR proven +
            capital-scaling + beats HLP by margin). Else REJECTED, with the exact
            reasons and — constructively — what it NEEDS to pass.
scanner.py  the constructive half. EDGE_CAN_LIVE = the inverse of every way edges died.
            Reads live fresh-flow sentinels, ranks fresh/uncontested markets by MEASURED
            edge, and lists the closest existing lanes + their needs. Directs the hunt.
capture.py  on a PASS -> a FAIL-CLOSED capture packet (what/where/net/arm-gate). Never
            executes, never moves capital. Operator arm is the only human step.
knowledge.py the accumulated edge knowledge, machine-readable: DEAD_LANES (+ why/gate),
            FALSE_GREEN_PATTERNS (detectors), the HLP benchmark, the meaningfulness bar,
            and EDGE_CAN_LIVE (the positive hunt profile).
governor.py  end-to-end: ingest -> gate -> scan -> capture -> verdict + ledger + report.
            Supersedes the raw router score; flags any "top lane" it rejects as a false-green.
```

## Run

```
./run.sh                 # run once + human report
./run.sh --json          # machine verdict -> state/governed-surface.json
./run.sh --watch 300     # loop every 300s
python3 test_governor.py # 11 truth tests
```

Outputs: `state/governed-surface.json` (full verdict), `state/governed_top_lane.json`
(the authoritative top-lane, supersedes the router's raw score), `state/governor-ledger.jsonl`.

## The bar (operator rule: no propping sub-meaningful ROI)

- `GOV_MEANINGFUL_USD_DAY` (default $10/day) — the absolute floor, OR
- proven + capital-scaling + beats HLP (`GOV_BENCHMARK_APR` 18%) by `GOV_BENCHMARK_MARGIN` (5×).
- `GOV_REAL_CAPITAL_USD` (default $560) — ROI is never scaled to capital we don't have.
- `GOV_ARTIFACT_RATIO` (3×) — headline > 3× strict/executable ⇒ governed on strict.

## First live verdict (2026-07-22)

`NO EDGE PASSES.` Closest: `hip3_thin_market_mm` ($2.24/day strict, closeness 0.86) —
needs to clear the $10/day bar OR become proven+scaling. Backrun (router's 108 "top
lane") → REJECT ($0 net, seat-walled). HIP-3 63× touch artifact caught → governed on
strict. Hunt: 92 fresh markets ranked by measured net; top real ones = CRWV/BE/KIOXIA,
directive "extend tape to 72h + prove." No capture packet emitted (nothing passes) —
honestly, no propping.

## Where a live edge gets captured

The governor doesn't trade. It finds (hunt), gates (truth), and directs. Capture happens
when a lane proves out (e.g. a fresh HIP-3 market's 72h tape) and passes the gate → a
fail-closed capture packet → operator arm. The one structurally-open lane is EARLINESS in
a fresh, uncontested market — which is exactly what the hunt ranks.
