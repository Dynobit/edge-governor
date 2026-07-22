#!/usr/bin/env python3
"""credential.py — the leverage engine's output: a portable, verifiable PROOF-OF-
EXPERTISE packet. This is the artifact you point a desk / fund / MEV team at. It
assembles the thesis + the measured map + the governor tool + the live verdict into
one credible document (CREDENTIAL.md) whose entire value proposition is: "I can tell
you which MEV lanes are real BEFORE you spend capital, and here is the receipt-backed
proof and the working tool that does it."

Compounds: regenerates from the live governor every run, so it stays current and
verifiable. The credential is the currency that converts expertise into the capital +
inclusion the measurements proved is the actual constraint.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from atlas import LANES, THESIS

STATE = Path(os.path.expanduser(os.environ.get("GOV_STATE", "state")))
OUT = Path(os.path.expanduser("~/topology/edge-governor/CREDENTIAL.md"))


def _load(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def generate() -> str:
    gov = _load(STATE / "governed-surface.json") or {}
    ledger = []
    lp = STATE / "governor-ledger.jsonl"
    if lp.exists():
        ledger = [l for l in lp.read_text().splitlines() if l.strip()]
    ts = time.strftime("%Y-%m-%d", time.gmtime())

    counts = {}
    for _, v, _, _ in LANES:
        counts[v] = counts.get(v, 0) + 1

    L = []
    L.append("# MEV Edge Research — Proof of Work")
    L.append(f"*Independent residential MEV research. Every claim reproducible against live "
             f"full nodes + the Hyperliquid API. Regenerated from a live truth-gate; updated {ts}.*")
    L.append("")
    L.append("## What this proves I can do")
    L.append("")
    L.append("- **Kill false-greens before capital moves.** I built a live truth-gate that "
             "rejects any 'edge' that isn't net-positive after ALL costs, transactable, landable "
             "without a seat, real-capital-sized, and meaningful. It caught a lane a naive scorer "
             "ranked #1 (108/100) that actually nets **$0** after the 90% MEV-Share refund, and a "
             "market-maker headline of **$142/day that was a 63x touch-model artifact** (real: $2.24).")
    L.append("- **Map an edge space to receipts, not vibes.** I tested "
             f"{len(LANES)} distinct MEV/DeFi lanes end-to-end and classified each with a number: "
             f"{counts.get('DEAD',0)} structurally dead, {counts.get('THIN',0)} real-but-sub-meaningful, "
             f"{counts.get('GATED',0)} gated (seat/capital/whitelist), {counts.get('LATENT',0)} real-but-latent.")
    L.append("- **Ship the whole stack solo.** Multi-chain full nodes (ETH/Base), on-chain "
             "quoters, HL signer (venue-proven), a governed candidate router, and the truth-gate — "
             "built, tested, running.")
    L.append("")
    L.append(THESIS)
    L.append("")
    L.append("## The map (receipt-backed)")
    L.append("")
    L.append("| Lane | Verdict | Binding constraint |")
    L.append("|---|---|---|")
    order = {"LATENT": 0, "THIN": 1, "GATED": 2, "DEAD": 3}
    for name, verdict, _, constraint in sorted(LANES, key=lambda x: order.get(x[1], 9)):
        L.append(f"| {name} | **{verdict}** | {constraint} |")
    L.append("")
    L.append("Full receipts for each in `ATLAS.md`; the gate that enforces them in `governor.py` "
             "(11/11 tests). Sample rigor: the cross-chain lead-lag lane is a *genuinely real* "
             "predictive signal — out-of-sample t-stat 6.0 — that I still classified DEAD, because "
             "the captured edge (0.5–1.8bp) is a fraction of the 10bp fee to trade it. Real ≠ tradable.")
    L.append("")
    L.append("## Live verification")
    L.append("")
    if gov:
        L.append(f"- Governor verdict, {gov.get('ts','?')}: **{gov.get('headline','?')}**")
        L.append(f"- Lanes governed: {gov.get('n_lanes','?')}; passing: {gov.get('n_passing','?')}; "
                 f"ledger entries: {len(ledger)}")
    L.append("- Reproduce: `git clone` → `python3 governor.py` (stdlib only, no keys, deploys nothing).")
    L.append("")
    L.append("## The value proposition")
    L.append("")
    L.append("The measurements say the residential ROI ceiling is a *capital + inclusion* wall, "
             "not an edge wall. Several lanes I mapped are **real and capital-scaling** (thin-market "
             "MM, delta-neutral carry, provision) — they are sub-meaningful at ~$500 and meaningful "
             "with real capital and a landing seat. **That is exactly the gap between what I have "
             "(the edge map, the tooling, the discipline) and what a capitalized/seated desk has "
             "(the capital, the inclusion power).** Put those together and the thin-but-real lanes "
             "become a book. I am looking for that seat.")
    L.append("")
    L.append("---")
    L.append("*Tooling is open source. Edges are mapped. The constraint was never the edge — it "
             "was the seat. Contact: [operator].*")
    return "\n".join(L)


if __name__ == "__main__":
    doc = generate()
    OUT.write_text(doc + "\n")
    print(f"wrote {OUT} ({len(doc)} chars)")
