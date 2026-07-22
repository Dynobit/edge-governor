#!/usr/bin/env python3
"""gate.py — the Meaningfulness Gate. The single truth filter every candidate edge
passes through before the system may call it real.

A candidate PASSES only if it clears ALL hard gates: real (strict/executable net > 0,
not an artifact), transactable (not phantom), landable (no builder seat), sized at
real capital, non-toxic, AND meaningful (clears the $/day bar OR is a proven,
capital-scaling, benchmark-beating high-% edge). Anything else is REJECTED — with the
exact reasons and, constructively, what it would NEED to pass (so the hunt is guided,
not just blocked). This is where the 108-score backrun and the 57x HIP-3 headline die.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from knowledge import KNOWLEDGE, FALSE_GREEN_PATTERNS


@dataclass
class Check:
    name: str
    passed: bool
    detail: str
    hard: bool = True


@dataclass
class Verdict:
    lane_id: str
    family: str
    venue: str
    passed: bool
    honest_net_usd_day: float
    headline_net_usd_day: float
    daily_pct: float
    capital_at_risk_usd: float
    beats_benchmark: bool
    checks: list[Check] = field(default_factory=list)
    false_greens: list[dict] = field(default_factory=list)
    rejection_reasons: list[str] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)
    closeness: float = 0.0
    capture_ready: bool = False
    known_dead: dict | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lane_id": self.lane_id, "family": self.family, "venue": self.venue,
            "passed": self.passed, "capture_ready": self.capture_ready,
            "honest_net_usd_day": round(self.honest_net_usd_day, 4),
            "headline_net_usd_day": round(self.headline_net_usd_day, 4),
            "daily_pct": round(self.daily_pct, 5),
            "capital_at_risk_usd": round(self.capital_at_risk_usd, 2),
            "beats_benchmark": self.beats_benchmark,
            "closeness": round(self.closeness, 3),
            "checks": [vars(c) for c in self.checks],
            "false_greens": self.false_greens,
            "rejection_reasons": self.rejection_reasons,
            "needs": self.needs,
            "known_dead": self.known_dead,
        }


def evaluate(c: dict[str, Any], k=KNOWLEDGE) -> Verdict:
    """Evaluate one normalized candidate. `c` fields (all optional, safe defaults):
    lane_id, family, venue, honest_net_usd_day, headline_net_usd_day, capital_at_risk_usd,
    landable(bool), proven(bool), capital_scaling(bool), toxic(bool), min_pool_depth_usd,
    capital_assumed_usd, sample_hours, blockers(list), phantom_flag(bool)."""
    honest = float(c.get("honest_net_usd_day") or 0.0)
    headline = c.get("headline_net_usd_day")
    headline = float(headline) if headline is not None else honest
    cap = float(c.get("capital_at_risk_usd") or k.real_capital_usd)
    daily_pct = (honest / cap) if cap > 0 else 0.0
    beats_bench = daily_pct >= k.benchmark_daily_pct * k.benchmark_margin

    # 1) run all false-green detectors
    fgs = []
    for name, fn in FALSE_GREEN_PATTERNS:
        tripped, detail = fn(c)
        if tripped:
            fgs.append({"pattern": name, "detail": detail})

    checks: list[Check] = []

    # 2) HARD gates
    checks.append(Check("real_net_positive", honest > 0,
                        f"strict/executable net ${honest:.4f}/day"))
    hard_artifact = honest <= 0 < headline
    soft_artifact = honest > 0 and headline > honest * k.artifact_ratio
    checks.append(Check(
        "not_artifact_inflated", not hard_artifact,
        (f"positive claim depends on optimistic model: strict ${honest:.4f} <= 0 < headline ${headline:.2f}")
        if hard_artifact else
        (f"headline ${headline:.2f}/d is {headline/max(honest,1e-9):.0f}x strict ${honest:.2f}/d — governed on strict")
        if soft_artifact else "headline consistent with strict/executable"))
    lw = next((f for f in fgs if f["pattern"] == "landing_or_seat_wall"), None)
    checks.append(Check("landable_no_seat", lw is None and bool(c.get("landable", True)),
                        lw["detail"] if lw else "landable at our access"))
    ph = next((f for f in fgs if f["pattern"] == "phantom_depth"), None)
    checks.append(Check("transactable_depth", ph is None,
                        ph["detail"] if ph else "real depth or n/a"))
    cf = next((f for f in fgs if f["pattern"] == "capital_fantasy"), None)
    checks.append(Check("real_capital_sized", cf is None,
                        cf["detail"] if cf else "sized at real capital"))
    checks.append(Check("non_toxic", not bool(c.get("toxic", False)),
                        "extracts from users" if c.get("toxic") else "non-toxic"))

    # meaningfulness: absolute bar OR proven+scaling+beats-benchmark
    scaling = bool(c.get("capital_scaling", False))
    proven = bool(c.get("proven", False))
    meaningful = (honest >= k.meaningful_usd_day) or (beats_bench and scaling and proven)
    on_scaling_track = beats_bench and scaling   # path (b) minus the proof
    if honest >= k.meaningful_usd_day:
        mdetail = f"${honest:.2f}/day >= ${k.meaningful_usd_day:.0f}/day bar"
    elif on_scaling_track and proven:
        mdetail = f"{daily_pct*100:.2f}%/day beats {k.benchmark_daily_pct*100:.3f}%/day HLP x{k.benchmark_margin:.0f}, proven+scaling"
    elif on_scaling_track and not proven:
        # capital-scaling high-% edge, benchmark-clearing — the ONLY live blocker is the
        # realized proof. Do NOT cite the absolute $/day bar: path (b) does not require it.
        mdetail = (f"PROOF-GATED only: {daily_pct*100:.3f}%/day beats HLP x{k.benchmark_margin:.0f} "
                   f"({k.benchmark_daily_pct*k.benchmark_margin*100:.2f}%/day) at ${cap:,.0f} risk capital + scaling; "
                   f"needs realized proof, not more $/day")
    else:
        gaps = []
        # only cite the absolute-$ bar when the capital-scaling path is NOT open
        if honest < k.meaningful_usd_day:
            gaps.append(f"${honest:.2f}/d < ${k.meaningful_usd_day:.0f}/d bar")
        if not beats_bench:
            gaps.append(f"{daily_pct*100:.3f}%/d < HLP x{k.benchmark_margin:.0f} ({k.benchmark_daily_pct*k.benchmark_margin*100:.2f}%/d)")
        if not scaling:
            gaps.append("capital-invariant (not scaling)")
        if not proven:
            gaps.append("unproven")
        mdetail = "; ".join(gaps)
    checks.append(Check("meaningful", meaningful, mdetail))

    hard = [c_ for c_ in checks if c_.hard]
    passed = all(c_.passed for c_ in hard)
    rejection = [f"{c_.name}: {c_.detail}" for c_ in hard if not c_.passed]
    needs = _needs(hard)
    closeness = sum(1 for c_ in hard if c_.passed) / max(1, len(hard))
    # nudge closeness by how near honest net is to the bar (only if net>0)
    if honest > 0 and k.meaningful_usd_day > 0:
        closeness = min(1.0, closeness + 0.1 * min(1.0, honest / k.meaningful_usd_day) / len(hard))

    known_dead = k.is_known_dead(c.get("family", ""))
    v = Verdict(
        lane_id=c.get("lane_id", "?"), family=c.get("family", "?"), venue=c.get("venue", "?"),
        passed=passed, honest_net_usd_day=honest, headline_net_usd_day=headline,
        daily_pct=daily_pct, capital_at_risk_usd=cap, beats_benchmark=beats_bench,
        checks=checks, false_greens=fgs, rejection_reasons=rejection, needs=needs,
        closeness=round(closeness, 3), known_dead=known_dead,
    )
    # capture-ready = passes the gate AND is arm-safe (proven or an absolute-$ clear)
    v.capture_ready = passed and (proven or honest >= k.meaningful_usd_day)
    return v


def _needs(hard_checks: list[Check]) -> list[str]:
    m = {
        "real_net_positive": "a strictly positive net after ALL costs (fees/gas/refund/slippage)",
        "not_artifact_inflated": "the honest number to use strict/executable fills, not a touch/gross model",
        "landable_no_seat": "a way to land WITHOUT a builder seat (CLOB order or a chain we control)",
        "transactable_depth": "real two-sided depth we can size into (not a phantom pool)",
        "real_capital_sized": "the $/day restated at our real capital, not scaled up",
        "non_toxic": "a non-predatory capture (no sandwiching users)",
        "meaningful": "either >= the $/day bar, or become a proven capital-scaling high-% edge",
    }
    return [m[c.name] for c in hard_checks if not c.passed and c.name in m]
