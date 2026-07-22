#!/usr/bin/env python3
"""verify_estate.py — third-party verifier for a published estate track record.

Don't trust the operator's numbers. Recompute them.

  python3 verify_estate.py --address 0x...            # live public equity, right now
  python3 verify_estate.py --chain estate_chain.jsonl # validate the hash chain + curve
  python3 verify_estate.py --address 0x... --chain estate_chain.jsonl   # both + drift

What each mode proves:
  --address : queries ONLY Hyperliquid's public info API (clearinghouseState,
              spotClearinghouseState, spotMetaAndAssetCtxs). No keys, no cookies.
              Anyone gets the same answer for the same address at the same moment.
  --chain   : every record embeds sha256(previous line). Editing any historical
              record breaks every later link. Validates integrity and prints the
              equity curve (first/last/min/max/days) from `public.total_public_usd`.
  both      : compares the live recomputation against the newest chain record so
              you can see the snapshot is the same account you just measured.

stdlib only. No dependencies. ~200 lines you can read before running.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from typing import Any, Dict, List, Optional

HL_INFO = "https://api.hyperliquid.xyz/info"


def post(url: str, payload: Dict[str, Any], timeout: float = 12.0) -> Any:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def spot_mids() -> Dict[str, Any]:
    """token -> {px, quote}. NOTE: ctxs is NOT positionally aligned with universe
    (315 pairs vs 706 ctxs observed) — match ctx.coin to pair.name, never zip."""
    meta, ctxs = post(HL_INFO, {"type": "spotMetaAndAssetCtxs"})
    tokens = {t["index"]: t["name"] for t in meta["tokens"]}
    ctx_by_coin = {c.get("coin"): c for c in ctxs}
    mids: Dict[str, Any] = {"USDC": {"px": 1.0, "quote": "USDC"}}
    for preferred in ("USDC", "USDT0", "USDH", "USDE"):
        for pair in meta["universe"]:
            ctx = ctx_by_coin.get(pair.get("name"))
            if not ctx or ctx.get("midPx") is None:
                continue
            b, q = tokens.get(pair["tokens"][0]), tokens.get(pair["tokens"][1])
            if b and q == preferred and b not in mids:
                mids[b] = {"px": float(ctx["midPx"]), "quote": preferred}
    return mids


def live_equity(addr: str, mids: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    perp = float(post(HL_INFO, {"type": "clearinghouseState", "user": addr})
                 ["marginSummary"]["accountValue"])
    mids = spot_mids() if mids is None else mids
    spot_total, rows, unpriced = 0.0, [], []
    for b in post(HL_INFO, {"type": "spotClearinghouseState", "user": addr}).get("balances", []):
        qty = float(b["total"])
        if qty == 0:
            continue
        m = mids.get(b["coin"])
        if m is None:
            unpriced.append(b["coin"])
            rows.append((b["coin"], qty, None, None))
        else:
            spot_total += qty * m["px"]
            rows.append((b["coin"], qty, qty * m["px"], m["quote"]))
    return {"address": addr, "perp_equity_usd": perp, "spot_usd": spot_total,
            "total_usd": perp + spot_total, "spot_rows": rows, "unpriced": unpriced}


def verify_chain(path: str) -> Dict[str, Any]:
    lines = [ln for ln in open(path).read().splitlines() if ln.strip()]
    prev, curve = "genesis", []
    for i, ln in enumerate(lines):
        rec = json.loads(ln)
        if rec.get("prev_sha256") != prev:
            return {"ok": False, "reason": f"CHAIN BREAK at record {i} "
                    f"(prev_sha256 mismatch — history was edited)", "records": len(lines)}
        prev = hashlib.sha256(ln.encode()).hexdigest()
        pub = rec.get("public", {})
        if isinstance(pub.get("total_public_usd"), (int, float)):
            curve.append((rec.get("ts", "?"), float(pub["total_public_usd"])))
    out: Dict[str, Any] = {"ok": True, "records": len(lines), "tip_sha256": prev}
    if curve:
        vals = [v for _, v in curve]
        out["curve"] = {"first": curve[0], "last": curve[-1],
                        "min": min(vals), "max": max(vals), "points": len(curve)}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Recompute a published estate track record from public data")
    ap.add_argument("--address", action="append", default=[],
                    help="Hyperliquid account address (repeatable)")
    ap.add_argument("--chain", help="path to estate_chain.jsonl to validate")
    args = ap.parse_args()
    if not args.address and not args.chain:
        ap.print_help()
        return 2

    rc = 0
    mids = spot_mids() if args.address or args.chain else None
    live_by_addr: Dict[str, float] = {}
    for a in args.address:
        e = live_equity(a, mids)
        live_by_addr[a.lower()] = e["total_usd"]
        print(f"[live] {a}")
        print(f"       perp equity ${e['perp_equity_usd']:.2f} + spot ${e['spot_usd']:.2f} "
              f"= ${e['total_usd']:.2f}")
        for coin, qty, usd, quote in e["spot_rows"]:
            print(f"         {coin:<8} {qty:>14.6f}  " +
                  (f"${usd:.2f} (vs {quote})" if usd is not None else "(no USD-quote mid — not valued)"))
        if e["unpriced"]:
            print(f"       unpriced (excluded, listed for honesty): {', '.join(e['unpriced'])}")

    if args.chain:
        v = verify_chain(args.chain)
        if not v["ok"]:
            print(f"[chain] INVALID: {v['reason']}")
            rc = 1
        else:
            print(f"[chain] VALID — {v['records']} records, tip {v['tip_sha256'][:16]}…")
            if "curve" in v:
                c = v["curve"]
                print(f"        equity curve ({c['points']} pts): first {c['first'][0]} "
                      f"${c['first'][1]:.2f} -> last {c['last'][0]} ${c['last'][1]:.2f} "
                      f"(min ${c['min']:.2f} / max ${c['max']:.2f})")
            # like-for-like cross-check: recompute the SAME hyperliquid addresses the
            # newest record claims, and compare only that subset (chains also hold
            # non-HL accounts; a one-address vs whole-estate diff proves nothing).
            last = json.loads([ln for ln in open(args.chain) if ln.strip()][-1])
            hl_accts = [x for x in last.get("public", {}).get("accounts", [])
                        if x.get("venue") == "hyperliquid"]
            if hl_accts:
                snap_sum = sum(x["perp_equity_usd"] + x.get("spot_usd", 0) for x in hl_accts)
                live_sum = 0.0
                for x in hl_accts:
                    a = x["address"]
                    if a.lower() not in live_by_addr:
                        live_by_addr[a.lower()] = live_equity(a, mids)["total_usd"]
                    live_sum += live_by_addr[a.lower()]
                drift = live_sum - snap_sum
                print(f"[cross] HL accounts in newest snapshot: recomputed live ${live_sum:.2f} "
                      f"vs recorded ${snap_sum:.2f} (drift ${drift:+.2f} — prices move; large "
                      f"drift on a fresh snapshot = red flag)")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
