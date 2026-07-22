#!/usr/bin/env python3
"""governor.py — end-to-end. The single authority that decides whether the live MEV
system has a real, meaningful, capturable edge — and if not, where to hunt for one.

  ingest (all live lane surfaces)  ->  gate (truth filter)  ->  scan (hunt list)
    ->  capture (fail-closed packets)  ->  verdict + ledger + governed surface

Supersedes the raw router score: any lane the router calls "top" that the governor
REJECTS is flagged a false-green (e.g. the 108-score backrun that nets $0/seat-walled).
Encodes the operator rule: sub-meaningful lanes are NOT propped as progress.

CLI:  python3 governor.py            # run once + human report
      python3 governor.py --json     # machine verdict
      python3 governor.py --watch 300  # loop every 300s
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from ingest import ingest_all
from gate import evaluate
from scanner import hunt
from capture import build_captures
from knowledge import KNOWLEDGE

STATE = Path(os.path.expanduser(os.environ.get("GOV_STATE", "state")))
STATE.mkdir(parents=True, exist_ok=True)
SURFACE = STATE / "governed-surface.json"
LEDGER = STATE / "governor-ledger.jsonl"
TOP_LANE = STATE / "governed_top_lane.json"


def _ts(clock: float | None) -> str:
    t = time.gmtime(clock) if clock is not None else time.gmtime()
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", t)


def run(clock: float | None = None, k=KNOWLEDGE) -> dict:
    cands = ingest_all()
    by_id = {c["lane_id"]: c for c in cands}
    verds = [evaluate(c, k) for c in cands]
    verds.sort(key=lambda v: (v.passed, v.capture_ready, v.closeness), reverse=True)

    passing = [v for v in verds if v.passed]
    captures = build_captures(verds, by_id)
    huntlist = hunt(verds)

    # false-greens caught: headline inflated vs strict, OR net<=0 but a positive raw claim
    false_greens = []
    for v in verds:
        if v.headline_net_usd_day > max(v.honest_net_usd_day, 0) * k.artifact_ratio and v.headline_net_usd_day > 1:
            false_greens.append({
                "lane_id": v.lane_id,
                "headline_usd_day": round(v.headline_net_usd_day, 2),
                "governed_honest_usd_day": round(v.honest_net_usd_day, 4),
                "inflation_x": round(v.headline_net_usd_day / max(v.honest_net_usd_day, 1e-9), 1),
            })

    if passing:
        top = passing[0]
        headline = f"LIVE EDGE: {top.lane_id} — ${top.honest_net_usd_day:.2f}/day, capture-ready ({'proven' if top.capture_ready else 'gate-passed'})."
        governed_top = {"lane_id": top.lane_id, "verdict": "CAPTURE_READY",
                        "honest_net_usd_day": round(top.honest_net_usd_day, 4)}
    else:
        closest = huntlist["closest_existing"][0] if huntlist["closest_existing"] else None
        if closest and closest["closeness"] >= 0.8:
            headline = (f"NO EDGE PASSES. Closest: {closest['lane_id']} "
                        f"(${closest['honest_net_usd_day']:.2f}/day, closeness {closest['closeness']}) — "
                        f"needs: {'; '.join(closest['needs'][:2])}. Do NOT arm.")
        else:
            headline = ("NO MEANINGFUL EDGE PASSES the gate. " + huntlist["directive"])
        governed_top = {"lane_id": (closest["lane_id"] if closest else None),
                        "verdict": "NO_EDGE_PASSES",
                        "closest_needs": (closest["needs"] if closest else [])}

    decision = {
        "ts": _ts(clock),
        "bar": {"meaningful_usd_day": k.meaningful_usd_day,
                "benchmark": f"HLP ~{k.benchmark_daily_pct*365*100:.0f}% APR = {k.benchmark_daily_pct*100:.3f}%/day; must beat x{k.benchmark_margin:.0f}",
                "real_capital_usd": k.real_capital_usd},
        "n_lanes": len(cands),
        "n_passing": len(passing),
        "headline": headline,
        "governed_top_lane": governed_top,
        "capture_packets": captures,
        "verdicts": [v.to_dict() for v in verds],
        "false_greens_caught": false_greens,
        "hunt": huntlist,
    }
    return decision


def emit(decision: dict) -> None:
    SURFACE.write_text(json.dumps(decision, indent=2))
    TOP_LANE.write_text(json.dumps(decision["governed_top_lane"], indent=2))
    with open(LEDGER, "a") as f:
        f.write(json.dumps({"ts": decision["ts"], "headline": decision["headline"],
                            "n_passing": decision["n_passing"],
                            "false_greens": [fg["lane_id"] for fg in decision["false_greens_caught"]]}) + "\n")


def report(decision: dict) -> str:
    L = []
    L.append("=" * 78)
    L.append(f"EDGE GOVERNOR — {decision['ts']}   (bar: ${decision['bar']['meaningful_usd_day']:.0f}/day, must beat {decision['bar']['benchmark'].split(';')[0]})")
    L.append("=" * 78)
    L.append(f"VERDICT: {decision['headline']}")
    L.append("")
    if decision["false_greens_caught"]:
        L.append("FALSE-GREENS CAUGHT (headline inflated vs strict/executable):")
        for fg in decision["false_greens_caught"]:
            L.append(f"   ✗ {fg['lane_id']:<28} headline ${fg['headline_usd_day']}/d → governed ${fg['governed_honest_usd_day']}/d ({fg['inflation_x']}x)")
        L.append("")
    L.append(f"LANES GOVERNED: {decision['n_lanes']}   PASSING: {decision['n_passing']}")
    for v in decision["verdicts"][:8]:
        tag = "PASS " if v["passed"] else ("CLOSE" if v["closeness"] >= 0.7 else "REJECT")
        L.append(f"   [{tag}] {v['lane_id']:<28} ${v['honest_net_usd_day']:>9.3f}/d  close={v['closeness']}")
        if not v["passed"] and v["needs"]:
            L.append(f"           needs: {v['needs'][0]}")
    L.append("")
    hl = decision["hunt"]
    L.append(f"HUNT (where a live edge can live): {hl['directive']}")
    if hl["fresh_uncontested"]:
        L.append("   top fresh markets (ranked by MEASURED MM net, short paper sample):")
        for r in hl["fresh_uncontested"][:6]:
            m = r.get("measured_net_usd")
            mtag = f"measured ${m:+.4f}" if m is not None else "unprobed"
            L.append(f"   ◦ FRESH {r['name']:<14} @ {r['venue']:<10} [{mtag}] → {', '.join(r['to_probe'])}")
    if decision["capture_packets"]:
        L.append("")
        L.append("CAPTURE PACKETS (fail-closed, operator-arm required):")
        for p in decision["capture_packets"]:
            L.append(f"   ⚡ {p['lane_id']} — ${p['honest_net_usd_day']}/day — {p['action']}")
    L.append("=" * 78)
    return "\n".join(L)


def main(argv: list[str]) -> int:
    if "--watch" in argv:
        interval = int(argv[argv.index("--watch") + 1]) if len(argv) > argv.index("--watch") + 1 else 300
        while True:
            d = run()
            emit(d)
            print(report(d), flush=True)
            time.sleep(interval)
    d = run()
    emit(d)
    if "--json" in argv:
        print(json.dumps(d, indent=2))
    else:
        print(report(d))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
