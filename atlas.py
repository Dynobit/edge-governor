#!/usr/bin/env python3
"""atlas.py — the leverage engine's core: a self-updating, public-quality MEV EDGE
ATLAS generated from (a) the measured-lane map (receipts from the edge hunt) and
(b) the governor's LIVE ledger. It turns private knowledge into a verifiable,
compounding credibility artifact — the credential that converts expertise into
capital/access, which every measurement says is the real constraint.

Not marketing. A rigorous, honest, reproducible record: each lane, its verdict, the
number, the method. It sharpens every time the governor runs. Output: ATLAS.md.

  python3 atlas.py            # regenerate ATLAS.md from live governor state + map
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

STATE = Path(os.path.expanduser(os.environ.get("GOV_STATE", "state")))
OUT = Path(os.path.expanduser("~/topology/edge-governor/ATLAS.md"))

# --- The measured map: every lane the hunt tested, with the receipt. Grounded, honest. ---
# verdict: DEAD (structural) | THIN (sub-meaningful) | LATENT (real but no live trigger) | GATED
LANES = [
    ("Convex-optimal N-hop cyclic arb (Angeris routing)", "DEAD",
     "0 of 738 cycles / 3888 on-chain quotes positive; cross-venue prices agree ~2bps < 7bps 3-leg fee floor. Killed a $1.54M phantom (UniV3 balances != v2 reserves).",
     "fee floor over an efficient market"),
    ("LST/LRT redemption NAV vs AMM", "DEAD",
     "wstETH basis -1.0bp / cbETH -0.8bp on deep pools; the only wide gap (+25bp) was a $0.74-TVL phantom pool.",
     "arbed to fee-width; wide gaps are phantom-thin"),
    ("StableSwap invariant micro-depeg", "DEAD",
     "invariant rebuilt to wei-accuracy; best net +0.035bp. Rule: internal discount ~= external depeg + O(fee).",
     "efficiently priced to the real peg"),
    ("Uniswap V3 cross-tick misquote", "DEAD",
     "$500 swap crosses ZERO initialized ticks in deep pools -> true == naive to the wei; only bites at $50k+ where pro routers already compute it exactly.",
     "capital + competition"),
    ("Stale push-oracle lending liquidation", "DEAD",
     "Moonwell oracle tracks DEX to 1-2bp, max staleness ~20min < liq buffer; capture is a keeper race (HyperLend 0/23).",
     "no exploitable staleness + keeper race"),
    ("Multi-block mean-reversion (statistical)", "DEAD",
     "first on-chain measurement: half-life >20 blocks, edge ~+1bp vs >=10bp fee floor, N=27, t-stat 0.24 (noise).",
     "edge < fee; reversion taken inside the shock block"),
    ("Cross-chain lead-lag (ETH -> Base WETH)", "THIN",
     "genuinely real signal: OOS t-stat 6.0, 64-69% directional hit at 3 blocks -- but captured edge 0.5-1.8bp << 10bp round-trip fee = -$130-460/day if traded.",
     "real predictive edge, killed by the fee"),
    ("Private-orderflow backrun (MEV-Share)", "DEAD",
     "4000 live events, 0 positive-net after the 90% user refund + gas; max backrunnable user swap $3.5k vs ~$37k needed. 42,857 submissions / 0 landings.",
     "90% refund + no builder seat"),
    ("Cross-chain sandwich (bridge source-event leak)", "GATED",
     "verified live+unpatched on our node (arxiv 2511.15245); $5.27M/2mo -- but landing needs a BSC private-builder seat (48Club/Blockrazor 90% MEV); predatory.",
     "builder seat + toxic"),
    ("Copy-trading vetted leaders", "THIN",
     "robust survivorship-free OOS ~0.09-0.19%/day, bootstrap p5 < 0 (not distinguishable from zero), hinges on one leader; capital-invariant.",
     "sub-meaningful + survivorship"),
    ("Delta-neutral funding carry", "THIN",
     "live acct realizes ~5-8% APR (not the 22% headline), HYPE-dependent, ADL tail; loses to a passive HLP deposit.",
     "beaten by the passive benchmark"),
    ("HIP-3 thin-market MM", "LATENT",
     "the closest real candidate: strict $2.24/day at $150 (63x touch-model artifact stripped), capital-scaling; unproven (4.9/72h tape), epoch-1 blew up on adverse selection.",
     "unproven; needs a 72h tape + inventory control"),
    ("Uniswap v4 hook", "GATED",
     "the router ships a curated hook ALLOWLIST; non-whitelisted hooks get zero routing; aggregators skip unknown hooks (Bunni $8.4M, Cork $11M).",
     "whitelist + audit + liquidity"),
    ("HL vault (self-distributing strategy)", "GATED",
     "on-chain PnL is self-proving + native profit-share, but 10k USDC creation fee (venue-refused at $163) and 66% of aged >20%-APR vaults are <$10k TVL = discovery-gated.",
     "$10k fee + discovery"),
    ("HIP-4 multi-bracket dutch-book arb", "LATENT",
     "novelty 5/5: sum(YES) < 1 is risk-free, no seat, no latency race. Full stack built + born-disarmed -- but no multi-outcome market has shipped on HL builder DEXs yet.",
     "no live trigger (waiting for the game)"),
]

THESIS = """## Thesis: the fee-floor / gated-access theorem

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
larger *position* (capital + inclusion power), not a cleverer edge."""


def _load(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def generate() -> str:
    gov = _load(STATE / "governed-surface.json") or {}
    ts = time.strftime("%Y-%m-%d", time.gmtime())
    counts = {}
    for _, v, _, _ in LANES:
        counts[v] = counts.get(v, 0) + 1

    L = []
    L.append("# The MEV Edge Atlas")
    L.append(f"*A measured, receipt-backed map of where on-chain MEV value is and isn't "
             f"capturable at residential access. Living document — regenerated from a live "
             f"truth-gate. Updated {ts}.*")
    L.append("")
    L.append(THESIS)
    L.append("")
    L.append("## The map")
    L.append("")
    L.append(f"{len(LANES)} lanes tested: "
             f"{counts.get('DEAD',0)} structurally dead, {counts.get('THIN',0)} real-but-sub-meaningful, "
             f"{counts.get('GATED',0)} gated (seat/capital/whitelist), {counts.get('LATENT',0)} real-but-latent.")
    L.append("")
    L.append("| Lane | Verdict | Binding constraint | Receipt |")
    L.append("|---|---|---|---|")
    order = {"LATENT": 0, "THIN": 1, "GATED": 2, "DEAD": 3}
    for name, verdict, receipt, constraint in sorted(LANES, key=lambda x: order.get(x[1], 9)):
        L.append(f"| {name} | **{verdict}** | {constraint} | {receipt} |")
    L.append("")
    L.append("## The live truth-gate (governor)")
    L.append("")
    L.append("Every candidate is machine-gated: it is only a real edge if it is simultaneously "
             "net-positive after ALL costs (not a touch/gross artifact), transactable (not phantom), "
             "landable without a builder seat, sized at real capital, non-toxic, and meaningful "
             "(clears a $/day bar or is a proven capital-scaling edge that beats HLP). The gate "
             "kills false-greens at the source and directs the hunt to the only structurally-open "
             "lane: earliness in a fresh, uncontested market.")
    L.append("")
    if gov:
        L.append(f"**Current live verdict ({gov.get('ts','?')}):** {gov.get('headline','?')}")
        fg = gov.get("false_greens_caught") or []
        if fg:
            L.append("")
            L.append("False-greens caught this run (headline inflated vs strict/executable):")
            for f in fg:
                L.append(f"- `{f['lane_id']}`: headline ${f['headline_usd_day']}/d → governed "
                         f"${f['governed_honest_usd_day']}/d ({f['inflation_x']}x)")
        hunt = gov.get("hunt", {})
        fresh = hunt.get("fresh_uncontested", [])
        if fresh:
            top = [r for r in fresh if r.get("measured_net_usd") is not None][:3]
            if top:
                L.append("")
                L.append("Live hunt — fresh markets ranked by measured edge: "
                         + ", ".join(f"{r['name']} (${r['measured_net_usd']:+.2f})" for r in top))
    L.append("")
    L.append("## Method")
    L.append("")
    L.append("Every number here is reproducible against live full nodes (Ethereum/Base) and the "
             "Hyperliquid API. No claim survives without a receipt: executable quotes not "
             "account-decodes, strict fills not touch models, net-after-refund not gross, "
             "out-of-sample not in-sample, and measured landings not submissions. The governor "
             "(`governor.py`, 11/11 tests) enforces it continuously.")
    L.append("")
    L.append("---")
    L.append("*Built by an independent residential MEV researcher. The tooling is open. "
             "The edges are mapped. The constraint was never the edge — it was the seat.*")
    return "\n".join(L)


if __name__ == "__main__":
    doc = generate()
    OUT.write_text(doc + "\n")
    print(f"wrote {OUT} ({len(doc)} chars)")
    print("\n" + "=" * 70)
    print(doc[:1600])
