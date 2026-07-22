#!/usr/bin/env python3
"""ingest.py — read every live lane surface and normalize it into one candidate
schema the gate understands. Speaks each lane's real field names (strict_net_usd,
summary.est_net_usd_per_day, refund_fraction_assumed, gross_inv_usd, gates...) and
maps them to honest_net / headline_net / capital / landable / proven / scaling.

The honest number always uses the strict/executable figure; the headline captures
the most optimistic figure the lane exposes, so the gate can catch the divergence.
"""
from __future__ import annotations

import glob
import json
import os
from typing import Any

TOPO = os.path.expanduser(os.environ.get("EDGE_TOPO", "~/topology"))
SEAT_GATED = {"private_orderflow_backrun", "latency_race_mev", "cross_chain_sandwich"}
TOXIC = {"cross_chain_sandwich", "sandwich"}
SCALING_HINTS = ("market_making", "_mm", "spread_capture", "carry", "liquidity",
                 "provision", "vault", "funding")


def _load(path: str) -> dict | None:
    try:
        with open(path) as f:
            d = json.load(f)
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def _first_num(d: dict, *keys) -> float | None:
    for k in keys:
        cur: Any = d
        for part in k.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                cur = None
                break
        if isinstance(cur, (int, float)):
            return float(cur)
    return None


def _is_scaling(family: str) -> bool:
    f = (family or "").lower()
    return any(h in f for h in SCALING_HINTS)


def normalize(s: dict, path: str) -> dict | None:
    family = str(s.get("family") or s.get("id") or os.path.basename(path).replace("-surface.json", ""))
    lane_id = str(s.get("id") or s.get("lane_id") or os.path.basename(path).replace("-surface.json", ""))
    venue = str(s.get("venue") or s.get("rpc_url") or "?")
    blockers = list(s.get("blockers") or [])

    honest = None
    headline = None
    capital = None
    sample_hours = None
    min_depth = None

    # --- HIP-3 / MM style: strict vs touch over a tape ---
    if "strict_net_usd" in s and s.get("honest_tape_hours"):
        hrs = float(s["honest_tape_hours"]) or 1.0
        honest = float(s["strict_net_usd"]) / hrs * 24.0
        touch_day = (float(s["touch_net_usd"]) / hrs * 24.0) if s.get("touch_net_usd") is not None else None
        headline = max(x for x in [touch_day, s.get("paper_net_per_day_usd"), honest] if x is not None)
        capital = _first_num(s, "gross_inv_usd", "capital_usd") or None
        sample_hours = hrs
    else:
        honest = _first_num(s, "summary.est_net_usd_per_day", "est_net_usd_per_day",
                            "expected_usd_day", "net_usd_day", "expected_net_usd",
                            "paper_net_per_day_usd")
        headline_candidates = [honest]
        for k in ("headline_net_usd_day", "paper_net_per_day_usd", "gross_usd_day",
                  "summary.best_usd", "expected_usd_day"):
            v = _first_num(s, k)
            if v is not None:
                headline_candidates.append(v)
        headline = max([x for x in headline_candidates if x is not None] or [honest or 0.0])
        min_depth = _first_num(s, "min_pool_depth_usd", "summary.min_depth_usd")

    honest = 0.0 if honest is None else honest
    headline = honest if headline is None else headline

    # landability: seat-gated families + landing/seat blockers
    landable = family not in SEAT_GATED
    if family in SEAT_GATED and "42857" not in " ".join(map(str, blockers)):
        blockers = blockers + ["realized_landing_gate_fail_closed:42857_submissions_0_landings"]
    blob = " ".join(str(b) for b in blockers).lower()
    if any(t in blob for t in ("landing", "bundle_builder", "not_connected", "42857", "seat")):
        landable = False

    # proof: explicit gates all-true, or armed receipts, else unproven for paper lanes
    proven = False
    gates = s.get("gates")
    if isinstance(gates, dict) and gates:
        proven = all(bool(v) for v in gates.values())
    if s.get("armed") or s.get("live_receipts") or (s.get("ready") and not s.get("paper_only") and not s.get("observe_only")):
        proven = proven or bool(s.get("ready"))

    return {
        "lane_id": lane_id, "family": family, "venue": venue,
        "honest_net_usd_day": round(honest, 6),
        "headline_net_usd_day": round(headline, 6),
        "capital_at_risk_usd": capital,
        "capital_scaling": _is_scaling(family),
        "proven": proven,
        "landable": landable,
        "toxic": family in TOXIC,
        "min_pool_depth_usd": min_depth,
        "sample_hours": sample_hours,
        "blockers": blockers,
        "phantom_flag": bool(s.get("phantom") or s.get("phantom_flag")),
        "source_path": path,
        "status": s.get("status"),
        "observe_only": bool(s.get("observe_only") or s.get("paper_only")),
    }


def ingest_all(extra_paths: list[str] | None = None) -> list[dict]:
    paths = set(glob.glob(f"{TOPO}/*/state/*surface*.json"))
    paths |= set(glob.glob(f"{TOPO}/*/state/*/*surface*.json"))
    for p in (extra_paths or []):
        paths.add(p)
    out = []
    for p in sorted(paths):
        if "pycache" in p or "epoch" in p.lower() or "invalid" in p.lower() or "reset" in p.lower():
            continue
        s = _load(p)
        if not s:
            continue
        c = normalize(s, p)
        if c:
            out.append(c)
    # dedup by lane_id, keep the freshest (last)
    by_id: dict[str, dict] = {}
    for c in out:
        by_id[c["lane_id"]] = c
    return list(by_id.values())


if __name__ == "__main__":
    import sys
    cands = ingest_all()
    print(f"ingested {len(cands)} live lane candidates:")
    for c in cands:
        print(f"  {c['lane_id']:<34} honest=${c['honest_net_usd_day']:>10.4f}/d  "
              f"headline=${c['headline_net_usd_day']:>10.2f}/d  landable={c['landable']}  "
              f"proven={c['proven']}  scaling={c['capital_scaling']}")
    if "--json" in sys.argv:
        print(json.dumps(cands, indent=2))
