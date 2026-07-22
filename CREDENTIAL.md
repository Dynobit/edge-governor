# MEV Edge Research — Proof of Work
*Independent residential MEV research. Every claim reproducible against live full nodes + the Hyperliquid API. Regenerated from a live truth-gate; updated 2026-07-22.*

## What this proves I can do

- **Kill false-greens before capital moves.** I built a live truth-gate that rejects any 'edge' that isn't net-positive after ALL costs, transactable, landable without a seat, real-capital-sized, and meaningful. It caught a lane a naive scorer ranked #1 (108/100) that actually nets **$0** after the 90% MEV-Share refund, and a market-maker headline of **$142/day that was a 63x touch-model artifact** (real: $2.24).
- **Map an edge space to receipts, not vibes.** I tested 15 distinct MEV/DeFi lanes end-to-end and classified each with a number: 7 structurally dead, 3 real-but-sub-meaningful, 3 gated (seat/capital/whitelist), 2 real-but-latent.
- **Ship the whole stack solo.** Multi-chain full nodes (ETH/Base), on-chain quoters, HL signer (venue-proven), a governed candidate router, and the truth-gate — built, tested, running.

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

## The map (receipt-backed)

| Lane | Verdict | Binding constraint |
|---|---|---|
| HIP-3 thin-market MM | **LATENT** | unproven; needs a 72h tape + inventory control |
| HIP-4 multi-bracket dutch-book arb | **LATENT** | no live trigger (waiting for the game) |
| Cross-chain lead-lag (ETH -> Base WETH) | **THIN** | real predictive edge, killed by the fee |
| Copy-trading vetted leaders | **THIN** | sub-meaningful + survivorship |
| Delta-neutral funding carry | **THIN** | beaten by the passive benchmark |
| Cross-chain sandwich (bridge source-event leak) | **GATED** | builder seat + toxic |
| Uniswap v4 hook | **GATED** | whitelist + audit + liquidity |
| HL vault (self-distributing strategy) | **GATED** | $10k fee + discovery |
| Convex-optimal N-hop cyclic arb (Angeris routing) | **DEAD** | fee floor over an efficient market |
| LST/LRT redemption NAV vs AMM | **DEAD** | arbed to fee-width; wide gaps are phantom-thin |
| StableSwap invariant micro-depeg | **DEAD** | efficiently priced to the real peg |
| Uniswap V3 cross-tick misquote | **DEAD** | capital + competition |
| Stale push-oracle lending liquidation | **DEAD** | no exploitable staleness + keeper race |
| Multi-block mean-reversion (statistical) | **DEAD** | edge < fee; reversion taken inside the shock block |
| Private-orderflow backrun (MEV-Share) | **DEAD** | 90% refund + no builder seat |

Full receipts for each in `ATLAS.md`; the gate that enforces them in `governor.py` (11/11 tests). Sample rigor: the cross-chain lead-lag lane is a *genuinely real* predictive signal — out-of-sample t-stat 6.0 — that I still classified DEAD, because the captured edge (0.5–1.8bp) is a fraction of the 10bp fee to trade it. Real ≠ tradable.

## Live verification

- Governor verdict, 2026-07-22T11:45:00Z: **NO EDGE PASSES. Closest: hip3_thin_market_mm ($1.09/day, closeness 0.859) — needs: either >= the $/day bar, or become a proven capital-scaling high-% edge. Do NOT arm.**
- Lanes governed: 11; passing: 0; ledger entries: 26
- Reproduce: `git clone` → `python3 governor.py` (stdlib only, no keys, deploys nothing).

## The value proposition

The measurements say the residential ROI ceiling is a *capital + inclusion* wall, not an edge wall. Several lanes I mapped are **real and capital-scaling** (thin-market MM, delta-neutral carry, provision) — they are sub-meaningful at ~$500 and meaningful with real capital and a landing seat. **That is exactly the gap between what I have (the edge map, the tooling, the discipline) and what a capitalized/seated desk has (the capital, the inclusion power).** Put those together and the thin-but-real lanes become a book. I am looking for that seat.

---
*Tooling is open source. Edges are mapped. The constraint was never the edge — it was the seat. Contact: [operator].*
