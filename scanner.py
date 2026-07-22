#!/usr/bin/env python3
"""scanner.py — the constructive half. The gate says what's dead; the scanner says
WHERE TO LOOK. It encodes EDGE_CAN_LIVE (the inverse of every way edges died) as a
scorer, reads the live fresh-flow sources (newly-born markets/venues = the only
residential moat: earliness in an uncontested game), and produces a ranked HUNT LIST:

  - fresh/uncontested candidates scored against the edge-can-live profile, and
  - the closest gated lanes + the exact thing each needs to become real.

So the knowledge doesn't just block — it directs the next probe toward the one place
a live edge can actually exist.
"""
from __future__ import annotations

import json
import os
from typing import Any

from knowledge import EDGE_CAN_LIVE, FRESH_FLOW_SOURCES, KNOWLEDGE


def _load(path: str) -> Any:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def read_fresh_flow() -> list[dict]:
    """Pull newly-born markets/venues from the live freshness sentinels. Robust to
    list- or dict-shaped sources; returns normalized {name, venue, age_hint, raw}."""
    out: list[dict] = []
    for src in FRESH_FLOW_SOURCES:
        data = _load(src)
        if data is None:
            continue
        rows = data if isinstance(data, list) else (
            data.get("targets") or data.get("fresh") or data.get("markets")
            or data.get("births") or data.get("seen") or [])
        if isinstance(rows, dict):
            rows = [{"name": k, **(v if isinstance(v, dict) else {"value": v})} for k, v in rows.items()]
        for r in (rows or []):
            if isinstance(r, str):
                r = {"name": r}
            if not isinstance(r, dict):
                continue
            out.append({
                "name": str(r.get("name") or r.get("symbol") or r.get("market") or r.get("id") or "?"),
                "venue": str(r.get("venue") or r.get("dex") or os.path.basename(src)),
                "age_hint": r.get("age_h") or r.get("age_hours") or r.get("first_seen"),
                "source": src, "raw": r,
            })
    # dedup by (name, venue)
    seen, uniq = set(), []
    for r in out:
        key = (r["name"], r["venue"])
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    return uniq


def _measured_per_symbol() -> dict[str, float]:
    """Real measured per-market MM net from the live MM surface (short paper sample).
    Lets the hunt point at fresh markets that are actually showing edge, not just names."""
    for p in (os.path.expanduser("~/topology/hip3-mm/state/paper_mm-surface.json"),):
        d = _load(p)
        if isinstance(d, dict) and isinstance(d.get("per_symbol_net"), dict):
            return {k: float(v) for k, v in d["per_symbol_net"].items() if isinstance(v, (int, float))}
    return {}


def edge_can_live_profile() -> dict[str, str]:
    """The positive criteria — where a real residential edge can exist."""
    return dict(EDGE_CAN_LIVE)


def hunt(verdicts: list, fresh: list[dict] | None = None, k=KNOWLEDGE) -> dict[str, Any]:
    """Build the ranked hunt list from gated verdicts + fresh-flow candidates."""
    fresh = read_fresh_flow() if fresh is None else fresh

    # closest existing lanes (rejected but nearest to real) — the guided-improvement list
    closest = sorted([v for v in verdicts if not v.passed], key=lambda v: v.closeness, reverse=True)
    closest_rows = [{
        "lane_id": v.lane_id, "family": v.family, "closeness": v.closeness,
        "honest_net_usd_day": round(v.honest_net_usd_day, 4),
        "needs": v.needs, "known_dead": bool(v.known_dead),
    } for v in closest[:5]]

    # fresh/uncontested candidates: these are the ONLY structurally-open lane.
    # Score = uncontested(fresh) is satisfied by construction; the open questions are
    # transactable depth + meaningful/scaling + landable + non-toxic (probe to resolve).
    # Cross-reference each against the MM system's MEASURED per-symbol net (real data,
    # short paper sample) so the hunt points at the fresh markets actually showing edge.
    measured = _measured_per_symbol()
    fresh_rows = []
    for r in fresh:
        m = measured.get(r["name"])
        fresh_rows.append({
            "name": r["name"], "venue": r["venue"], "age_hint": r.get("age_hint"),
            "measured_net_usd": (round(m, 4) if m is not None else None),
            "matched": ["uncontested (fresh)"] + (["measured net>0"] if (m or 0) > 0 else []),
            "to_probe": (["extend tape to 72h + prove"] if m is not None else
                         ["transactable_depth", "meaningful_or_scaling", "landable"]),
            "why": "freshness window — earliness is the residential moat; probe depth+edge before crowding",
            "source": r["source"],
        })
    # rank: measured-positive first (best real signal), then unprobed, then measured-negative
    fresh_rows.sort(key=lambda x: (x["measured_net_usd"] is not None,
                                   (x["measured_net_usd"] or 0.0)), reverse=True)

    # PRIORITY: the one fresh class with UNCAPPED upside. Every other fresh game is
    # cents-capped by our ~$560 even if caught; a multi-outcome / dutch-book market
    # (sum(YES) < 1 = risk-free, no seat, no latency) scales with the MISPRICING, not
    # our capital. Surface it distinctly so our single best shot is never buried among
    # cent-markets. This is the highest-EV "improve our luck" lane.
    def _is_priority(r):
        blob = (str(r.get("name", "")) + " " + str(r.get("venue", ""))).lower()
        return any(t in blob for t in ("outcome", "predict", "binary", "dutch", "-yes", "_yes", "bracket", "hip4", "hip-4"))
    priority = [dict(r, priority="UNCAPPED_UPSIDE (risk-free dutch-book class)") for r in fresh_rows if _is_priority(r)]

    return {
        "edge_can_live": edge_can_live_profile(),
        "priority_uncapped": priority,
        "fresh_uncontested": fresh_rows,
        "fresh_count": len(fresh_rows),
        "closest_existing": closest_rows,
        "directive": ((f"PRIORITY: {len(priority)} uncapped-upside dutch-book market(s) live -- probe NOW (the one fresh edge not capped by our capital). " if priority else "")
                      + _directive(closest_rows, fresh_rows, k)),
    }


def _directive(closest: list[dict], fresh: list[dict], k) -> str:
    if fresh:
        return (f"HUNT: {len(fresh)} fresh/uncontested market(s) detected — the only structurally-open "
                f"lane. Probe each for real depth + a meaningful/scaling edge BEFORE it crowds.")
    if closest and closest[0]["closeness"] >= 0.8:
        c = closest[0]
        return (f"IMPROVE: closest real candidate is '{c['lane_id']}' (closeness {c['closeness']}). "
                f"It needs: {'; '.join(c['needs'][:2])}.")
    return ("NO OPEN LANE: no fresh uncontested market and no near-passing lane. Per the rule, do not "
            "prop a sub-meaningful lane — hold until a freshness window opens or capital/access changes.")


if __name__ == "__main__":
    from ingest import ingest_all
    from gate import evaluate
    verds = [evaluate(c) for c in ingest_all()]
    h = hunt(verds)
    print(json.dumps(h, indent=2))
