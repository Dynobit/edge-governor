#!/usr/bin/env python3
"""capture.py — turn a gate-PASSING verdict into an actionable, FAIL-CLOSED capture
packet. This is the "capture a live edge" step: it specifies exactly what to do,
the honest expected net, the capital at risk, and an arm gate that requires an
explicit operator sign-off (deploy capital / sign). It NEVER executes and NEVER
deploys capital on its own — a passing verdict produces a packet, not a trade.
"""
from __future__ import annotations

from typing import Any


def capture_packet(verdict, candidate: dict[str, Any]) -> dict[str, Any] | None:
    """Emit a capture packet for a capture-ready verdict, else None."""
    if not getattr(verdict, "capture_ready", False):
        return None
    return {
        "kind": "capture_packet",
        "lane_id": verdict.lane_id,
        "family": verdict.family,
        "venue": verdict.venue,
        "honest_net_usd_day": round(verdict.honest_net_usd_day, 4),
        "daily_pct": round(verdict.daily_pct, 5),
        "capital_at_risk_usd": round(verdict.capital_at_risk_usd, 2),
        "beats_benchmark": verdict.beats_benchmark,
        "source_surface": candidate.get("source_path"),
        "action": _action_for(verdict.family),
        # FAIL-CLOSED: nothing is armed. The operator must explicitly authorize.
        "arm_gate": {
            "armed": False,
            "requires": [
                "operator authorization (deploy capital / sign) — this is the ONLY human step",
                "live signer wired + testnet-proven for the venue",
                "kill criteria set (max drawdown, stale-quote bound, position cap)",
            ],
            "irreversible": True,
            "note": "governor produces the packet; it does not execute or move capital.",
        },
    }


def _action_for(family: str) -> str:
    f = (family or "").lower()
    if "market_making" in f or "_mm" in f or "spread" in f:
        return "post two-sided quotes on the CLOB with inventory governor; capture spread; flatten on markout breach."
    if "carry" in f or "funding" in f:
        return "open the delta-neutral leg pair; collect funding; disarm on spread compression."
    if "arb" in f:
        return "execute the atomic round-trip via the arb contract; receipt-truth gate on realized delta."
    return "execute per the lane's proven playbook behind its arm gate."


def build_captures(verdicts: list, candidates_by_id: dict[str, dict]) -> list[dict]:
    out = []
    for v in verdicts:
        pkt = capture_packet(v, candidates_by_id.get(v.lane_id, {}))
        if pkt:
            out.append(pkt)
    return out
