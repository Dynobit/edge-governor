# The MEV Edge Atlas
*A measured, receipt-backed map of where on-chain MEV value is and isn't capturable at residential access. Living document — regenerated from a live truth-gate. Updated 2026-07-22.*

## Thesis: the fee-floor / gated-access theorem

Across 15+ rigorously measured lanes, one law holds: **value in on-chain markets
accrues to whoever controls *inclusion* or is *structurally embedded* in the flow --
never to whoever merely *computes* the edge.** Every residential taker edge is
competed to the fee floor (deep markets) or is phantom-thin (wide gaps); the ones
that clear the math are seat-walled at the point of landing. The sharpest proof is
the cross-chain lead-lag lane: a genuinely real predictive signal (out-of-sample
t-stat 6.0) that still *loses money*, because the captured edge (0.5-1.8bp) is a
fraction of the fee it costs to trade (10bp). Knowing first is not the moat.
Landing is. This is why extraction, at residential access and small capital, has a
hard ROI ceiling below a passive HLP deposit -- and why the productive move is a
larger *position* (capital + inclusion power), not a cleverer edge.

## The map

15 lanes tested: 7 structurally dead, 3 real-but-sub-meaningful, 3 gated (seat/capital/whitelist), 2 real-but-latent.

| Lane | Verdict | Binding constraint | Receipt |
|---|---|---|---|
| HIP-3 thin-market MM | **LATENT** | unproven; needs a 72h tape + inventory control | the closest real candidate: strict $2.24/day at $150 (63x touch-model artifact stripped), capital-scaling; unproven (4.9/72h tape), epoch-1 blew up on adverse selection. |
| HIP-4 multi-bracket dutch-book arb | **LATENT** | no live trigger (waiting for the game) | novelty 5/5: sum(YES) < 1 is risk-free, no seat, no latency race. Full stack built + born-disarmed -- but no multi-outcome market has shipped on HL builder DEXs yet. |
| Cross-chain lead-lag (ETH -> Base WETH) | **THIN** | real predictive edge, killed by the fee | genuinely real signal: OOS t-stat 6.0, 64-69% directional hit at 3 blocks -- but captured edge 0.5-1.8bp << 10bp round-trip fee = -$130-460/day if traded. |
| Copy-trading vetted leaders | **THIN** | sub-meaningful + survivorship | robust survivorship-free OOS ~0.09-0.19%/day, bootstrap p5 < 0 (not distinguishable from zero), hinges on one leader; capital-invariant. |
| Delta-neutral funding carry | **THIN** | beaten by the passive benchmark | live acct realizes ~5-8% APR (not the 22% headline), HYPE-dependent, ADL tail; loses to a passive HLP deposit. |
| Cross-chain sandwich (bridge source-event leak) | **GATED** | builder seat + toxic | verified live+unpatched on our node (arxiv 2511.15245); $5.27M/2mo -- but landing needs a BSC private-builder seat (48Club/Blockrazor 90% MEV); predatory. |
| Uniswap v4 hook | **GATED** | whitelist + audit + liquidity | the router ships a curated hook ALLOWLIST; non-whitelisted hooks get zero routing; aggregators skip unknown hooks (Bunni $8.4M, Cork $11M). |
| HL vault (self-distributing strategy) | **GATED** | $10k fee + discovery | on-chain PnL is self-proving + native profit-share, but 10k USDC creation fee (venue-refused at $163) and 66% of aged >20%-APR vaults are <$10k TVL = discovery-gated. |
| Convex-optimal N-hop cyclic arb (Angeris routing) | **DEAD** | fee floor over an efficient market | 0 of 738 cycles / 3888 on-chain quotes positive; cross-venue prices agree ~2bps < 7bps 3-leg fee floor. Killed a $1.54M phantom (UniV3 balances != v2 reserves). |
| LST/LRT redemption NAV vs AMM | **DEAD** | arbed to fee-width; wide gaps are phantom-thin | wstETH basis -1.0bp / cbETH -0.8bp on deep pools; the only wide gap (+25bp) was a $0.74-TVL phantom pool. |
| StableSwap invariant micro-depeg | **DEAD** | efficiently priced to the real peg | invariant rebuilt to wei-accuracy; best net +0.035bp. Rule: internal discount ~= external depeg + O(fee). |
| Uniswap V3 cross-tick misquote | **DEAD** | capital + competition | $500 swap crosses ZERO initialized ticks in deep pools -> true == naive to the wei; only bites at $50k+ where pro routers already compute it exactly. |
| Stale push-oracle lending liquidation | **DEAD** | no exploitable staleness + keeper race | Moonwell oracle tracks DEX to 1-2bp, max staleness ~20min < liq buffer; capture is a keeper race (HyperLend 0/23). |
| Multi-block mean-reversion (statistical) | **DEAD** | edge < fee; reversion taken inside the shock block | first on-chain measurement: half-life >20 blocks, edge ~+1bp vs >=10bp fee floor, N=27, t-stat 0.24 (noise). |
| Private-orderflow backrun (MEV-Share) | **DEAD** | 90% refund + no builder seat | 4000 live events, 0 positive-net after the 90% user refund + gas; max backrunnable user swap $3.5k vs ~$37k needed. 42,857 submissions / 0 landings. |

## The live truth-gate (governor)

Every candidate is machine-gated: it is only a real edge if it is simultaneously net-positive after ALL costs (not a touch/gross artifact), transactable (not phantom), landable without a builder seat, sized at real capital, non-toxic, and meaningful (clears a $/day bar or is a proven capital-scaling edge that beats HLP). The gate kills false-greens at the source and directs the hunt to the only structurally-open lane: earliness in a fresh, uncontested market.

**Current live verdict (2026-07-22T11:45:00Z):** NO EDGE PASSES. Closest: hip3_thin_market_mm ($1.09/day, closeness 0.859) — needs: either >= the $/day bar, or become a proven capital-scaling high-% edge. Do NOT arm.

False-greens caught this run (headline inflated vs strict/executable):
- `hip3_thin_market_mm`: headline $93.15/d → governed $1.0942/d (85.1x)

Live hunt — fresh markets ranked by measured edge: xyz:CRWV ($+0.83), xyz:BE ($+0.66), xyz:KIOXIA ($+0.63)

## Method

Every number here is reproducible against live full nodes (Ethereum/Base) and the Hyperliquid API. No claim survives without a receipt: executable quotes not account-decodes, strict fills not touch models, net-after-refund not gross, out-of-sample not in-sample, and measured landings not submissions. The governor (`governor.py`, 11/11 tests) enforces it continuously.

---
*Built by an independent residential MEV researcher. The tooling is open. The edges are mapped. The constraint was never the edge — it was the seat.*
