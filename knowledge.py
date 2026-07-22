#!/usr/bin/env python3
"""knowledge.py — the accumulated MEV/DeFi edge knowledge, made machine-readable.

This is the "knowledge constructed to find and capture a live edge." It encodes,
as executable rules, everything the operator's edge hunt has established:

  1. WHERE EDGES DIE  — the false-green patterns + the fee-floor/seat-wall theorem.
     Used by gate.py to REJECT anything that reduces to a known-dead shape.
  2. THE BENCHMARK    — the passive alternative (HLP). Any active edge must beat it.
  3. WHERE EDGES CAN LIVE — the inverse of (1): the positive criteria a real,
     capturable, residential edge must satisfy. Used by scanner.py to HUNT.

Grounded in: finding_fee_floor_theorem_edge_hunt_2026_07_21, feedback_no_propping_
submeaningful_roi, finding_hip3_thin_market_mm_edge, the OFA-backrun 108-false-green,
and the HIP-3 57x touch/strict artifact. Pure data + pure functions, stdlib only.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable


# --- The bar. Sub-meaningful lanes are dead for purposes of effort (operator rule). ---
# A lane is MEANINGFUL if it clears an absolute $/day floor OR is a proven,
# capital-scaling, high-% edge (small $ now but real alpha that grows with capital).
MEANINGFUL_USD_DAY = float(os.environ.get("GOV_MEANINGFUL_USD_DAY", "10.0"))
# The passive alternative: depositing in HLP. Every active edge must beat the house
# by a margin, else "why not just park in HLP". ~18% APR mid-estimate.
HLP_APR = float(os.environ.get("GOV_BENCHMARK_APR", "0.18"))
BENCHMARK_DAILY_PCT = HLP_APR / 365.0            # ~0.049%/day
BENCHMARK_MARGIN = float(os.environ.get("GOV_BENCHMARK_MARGIN", "5.0"))  # must beat house 5x
# Artifact tripwire: optimistic model / gross vs strict-executable divergence.
ARTIFACT_RATIO = float(os.environ.get("GOV_ARTIFACT_RATIO", "3.0"))
# Real capital. Never scale ROI to capital we do not have.
REAL_CAPITAL_USD = float(os.environ.get("GOV_REAL_CAPITAL_USD", "560.0"))


# --- WHERE EDGES DIE: the measured-dead lane families + the exact killing gate. ---
# The scanner will not resurrect these; the gate cites them when it rejects a match.
DEAD_LANES: dict[str, dict[str, str]] = {
    "private_orderflow_backrun": {
        "why": "MEV-Share refunds ~90% to the user; searcher keeps ~10% and pays gas "
               "from it. Only >$8M swaps clear; observed max user swap ~$3.5k. No "
               "positive gross on landable pools (deep=arbed to 0, thin=phantom).",
        "gate": "landable + net_positive + not_phantom",
        "evidence": "4000 MEV-Share events, 0 positive-net; 42857 submissions/0 lands",
    },
    "latency_race_mev": {
        "why": "residential loses every inclusion race; builders/Timeboost win.",
        "gate": "landable", "evidence": "42857 submissions / 0 landings",
    },
    "cross_chain_sandwich": {
        "why": "landing on BSC needs a private-builder seat (48Club/Blockrazor 90% MEV); "
               "predatory + seat-walled; post-BUSD flow thin.",
        "gate": "landable + non_toxic", "evidence": "arxiv 2511.15245; gas-0 private builders",
    },
    "atomic_cross_dex_arb": {
        "why": "deep pools efficient to a fee-width (~2bps < 7bps 3-leg floor); "
               "wide gaps are phantom-thin.",
        "gate": "net_positive + not_phantom", "evidence": "738 cycles/3888 quotes, 0 positive",
    },
    "lst_nav / stableswap / v3_tick / stale_oracle / reversion / twamm": {
        "why": "all fee-floored or phantom-depth at residential size.",
        "gate": "net_positive + not_phantom", "evidence": "10-probe fee-floor theorem",
    },
    "copy_trading": {
        "why": "robust survivorship-free OOS ~0.09-0.19%/day, CI includes zero, hinges "
               "on one leader; capital-invariant; below the bar.",
        "gate": "meaningful + proven_oos", "evidence": "130-leader OOS, bootstrap p5<0",
    },
    "delta_neutral_carry": {
        "why": "~5-8% APR realized, HYPE-dependent, ADL tail; loses to HLP.",
        "gate": "beats_benchmark", "evidence": "live acct $0.04/day funding",
    },
}


# --- FALSE-GREEN PATTERNS: detectors the gate runs over every candidate. ---
# Each takes the normalized candidate dict and returns (tripped: bool, detail: str).
def _fg_touch_vs_strict(c: dict[str, Any]) -> tuple[bool, str]:
    strict = c.get("honest_net_usd_day")
    head = c.get("headline_net_usd_day")
    if strict is None or head is None:
        return (False, "no strict/headline pair")
    if strict <= 0 and head > 0:
        return (True, f"headline ${head:.2f}/d positive but strict/executable ${strict:.2f}/d <= 0")
    if strict > 0 and head > strict * ARTIFACT_RATIO:
        return (True, f"headline ${head:.2f}/d is {head/strict:.0f}x the strict ${strict:.2f}/d (optimistic fill/gross model)")
    return (False, "headline consistent with strict")


def _fg_landing_wall(c: dict[str, Any]) -> tuple[bool, str]:
    blob = " ".join(str(b) for b in c.get("blockers", [])).lower()
    for tok in ("landing", "bundle_builder", "not_connected", "42857", "seat", "builder_seat"):
        if tok in blob:
            return (True, f"landing/seat blocker present: '{tok}'")
    if c.get("family") in ("private_orderflow_backrun", "latency_race_mev", "cross_chain_sandwich"):
        if not c.get("landable", False):
            return (True, "family is inclusion/seat-gated and not landable at our access")
    return (False, "no landing/seat wall")


def _fg_phantom_depth(c: dict[str, Any]) -> tuple[bool, str]:
    d = c.get("min_pool_depth_usd")
    if d is not None and d < float(os.environ.get("GOV_MIN_DEPTH_USD", "10000")):
        return (True, f"transactable depth ${d:.0f} below floor (phantom)")
    if c.get("phantom_flag"):
        return (True, "lane self-reports a phantom/thin-pool flag")
    return (False, "depth ok or unknown")


def _fg_capital_fantasy(c: dict[str, Any]) -> tuple[bool, str]:
    cap = c.get("capital_assumed_usd")
    if cap is not None and cap > REAL_CAPITAL_USD * 3:
        return (True, f"$/day assumes ${cap:,.0f} capital, {cap/REAL_CAPITAL_USD:.0f}x our real ${REAL_CAPITAL_USD:,.0f}")
    return (False, "sized at real capital")


def _fg_extrapolation(c: dict[str, Any]) -> tuple[bool, str]:
    # a /day figure extrapolated from a tiny window is not proof.
    hrs = c.get("sample_hours")
    if hrs is not None and hrs < 1.0 and (c.get("honest_net_usd_day") or 0) > 0:
        return (True, f"$/day extrapolated from only {hrs:.2f}h of sample")
    return (False, "sample window adequate or n/a")


FALSE_GREEN_PATTERNS: list[tuple[str, Callable[[dict], tuple[bool, str]]]] = [
    ("touch_vs_strict_artifact", _fg_touch_vs_strict),
    ("landing_or_seat_wall", _fg_landing_wall),
    ("phantom_depth", _fg_phantom_depth),
    ("capital_fantasy", _fg_capital_fantasy),
    ("tiny_window_extrapolation", _fg_extrapolation),
]


# --- WHERE EDGES CAN LIVE: the inverse criteria the scanner hunts for. ---
# A residential edge is only real if it is uncontested (fresh/thin competition),
# transactable, landable without a seat, and meaningful-or-scaling. This is the
# constructive half: the map of where to look, derived from where everything died.
EDGE_CAN_LIVE = {
    "uncontested": "in a FRESHNESS window (new market type / venue / mechanism) before "
                   "pros index it — earliness is the only residential moat.",
    "transactable": "real two-sided depth we can size into (not phantom, not so deep it is "
                    "already efficient to the fee floor).",
    "landable": "captured via a CLOB order or a chain we can land on WITHOUT a builder seat.",
    "meaningful_or_scaling": "clears the $/day bar OR is a proven high-% edge that scales "
                             "with capital (MM/provision), not capital-invariant cents.",
    "persistent": "holds for many blocks / is a valuation or provision edge — NOT a "
                  "sub-second inclusion race.",
    "non_toxic": "does not extract from ordinary users (no sandwich).",
}

# Live sources the scanner reads to find fresh/uncontested candidates.
FRESH_FLOW_SOURCES = [
    os.path.expanduser("~/topology/hip3-mm/state/fresh_flow_targets.json"),
    os.path.expanduser("~/topology/hip3-mm/state/flow_seen.json"),
    os.path.expanduser("~/topology/venue-youth-radar/state/radar.json"),
]


@dataclass
class Knowledge:
    meaningful_usd_day: float = MEANINGFUL_USD_DAY
    benchmark_daily_pct: float = BENCHMARK_DAILY_PCT
    benchmark_margin: float = BENCHMARK_MARGIN
    artifact_ratio: float = ARTIFACT_RATIO
    real_capital_usd: float = REAL_CAPITAL_USD
    dead_lanes: dict = field(default_factory=lambda: DEAD_LANES)

    def is_known_dead(self, family: str) -> dict | None:
        for k, v in DEAD_LANES.items():
            if family and family in k:
                return {"family": k, **v}
        return None


KNOWLEDGE = Knowledge()
