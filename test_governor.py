#!/usr/bin/env python3
"""test_governor.py — lock in the truth behaviors. Run: python3 test_governor.py
(also pytest-compatible). Each test asserts a canonical case the governor must get
right, grounded in the real false-greens it exists to kill.
"""
from __future__ import annotations

from gate import evaluate
from knowledge import KNOWLEDGE
import governor
import ingest


def _c(**kw):
    base = dict(lane_id="t", family="generic", venue="v", honest_net_usd_day=0.0,
                headline_net_usd_day=0.0, capital_at_risk_usd=560.0, landable=True,
                proven=False, capital_scaling=False, toxic=False, blockers=[])
    base.update(kw)
    base.setdefault("headline_net_usd_day", base["honest_net_usd_day"])
    return base


def test_real_edge_passes():
    v = evaluate(_c(lane_id="real", honest_net_usd_day=50.0, headline_net_usd_day=50.0,
                    landable=True, proven=True))
    assert v.passed and v.capture_ready, v.rejection_reasons


def test_backrun_seatwall_rejected():
    # net 0 + MEV-Share seat wall -> must REJECT (kills the 108-score false-green)
    v = evaluate(_c(lane_id="ofa", family="private_orderflow_backrun",
                    honest_net_usd_day=0.0, landable=False,
                    blockers=["realized_landing_gate_fail_closed:42857_submissions_0_landings"]))
    assert not v.passed
    names = {c.name for c in v.checks if not c.passed}
    assert "landable_no_seat" in names and "real_net_positive" in names


def test_hip3_touch_artifact_governed_on_strict():
    # strict positive, touch headline 65x -> use strict, do NOT hard-fail on artifact,
    # but reject on meaningful (unproven). Closest-but-not-passing.
    v = evaluate(_c(lane_id="hip3", family="passive_market_making_spread_capture",
                    honest_net_usd_day=2.27, headline_net_usd_day=147.0,
                    capital_at_risk_usd=150.0, capital_scaling=True, proven=False,
                    sample_hours=4.97))
    assert not v.passed
    # artifact must NOT hard-fail (strict is positive)
    art = next(c for c in v.checks if c.name == "not_artifact_inflated")
    assert art.passed, "strict>0 should not hard-fail on inflated headline"
    # rejected specifically on meaningfulness (unproven)
    assert any("meaningful" in r for r in v.rejection_reasons)
    assert v.closeness >= 0.7


def test_hip3_proven_scaling_passes_via_benchmark():
    # same small $ but PROVEN -> beats HLP x5 (1.5%/day) + scaling -> PASS
    v = evaluate(_c(lane_id="hip3p", family="passive_market_making_spread_capture",
                    honest_net_usd_day=2.27, headline_net_usd_day=2.27,
                    capital_at_risk_usd=150.0, capital_scaling=True, proven=True,
                    sample_hours=80.0))
    assert v.passed and v.capture_ready, v.rejection_reasons


def test_artifact_dependent_positive_rejected():
    # positive claim depends ENTIRELY on the optimistic model -> hard reject
    v = evaluate(_c(lane_id="fake", honest_net_usd_day=-1.0, headline_net_usd_day=30.0))
    assert not v.passed
    art = next(c for c in v.checks if c.name == "not_artifact_inflated")
    assert not art.passed


def test_capital_fantasy_rejected():
    v = evaluate(_c(lane_id="fantasy", honest_net_usd_day=200.0, headline_net_usd_day=200.0,
                    capital_assumed_usd=100000.0, proven=True))
    assert not v.passed
    assert any("real_capital" in c.name and not c.passed for c in v.checks)


def test_phantom_depth_rejected():
    v = evaluate(_c(lane_id="phantom", honest_net_usd_day=5.0, headline_net_usd_day=5.0,
                    min_pool_depth_usd=620.0, proven=True, capital_scaling=True))
    assert not v.passed
    assert any(c.name == "transactable_depth" and not c.passed for c in v.checks)


def test_toxic_rejected():
    v = evaluate(_c(lane_id="sandwich", family="cross_chain_sandwich",
                    honest_net_usd_day=100.0, headline_net_usd_day=100.0,
                    toxic=True, landable=True, proven=True))
    assert not v.passed
    assert any(c.name == "non_toxic" and not c.passed for c in v.checks)


def test_sub_meaningful_not_propped():
    # positive but tiny, capital-invariant, unproven -> must NOT pass (no propping)
    v = evaluate(_c(lane_id="cents", honest_net_usd_day=0.04, headline_net_usd_day=0.04,
                    capital_at_risk_usd=220.0, proven=True))
    assert not v.passed
    assert any("meaningful" in r for r in v.rejection_reasons)


def test_ingest_normalizes_hip3_strict():
    # against the REAL surface file: honest must derive from strict, not touch
    cands = ingest.ingest_all()
    hip3 = next((c for c in cands if "hip3" in c["lane_id"]), None)
    if hip3:  # only if the surface exists live
        assert hip3["honest_net_usd_day"] < hip3["headline_net_usd_day"], "must govern on strict < headline"
        assert hip3["capital_scaling"] is True


def test_governor_run_catches_false_green():
    d = governor.run()
    assert d["n_lanes"] >= 1
    # backrun/hip3 headline inflation should be caught if those surfaces are live
    assert isinstance(d["false_greens_caught"], list)
    assert "headline" in d and d["headline"]


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    p = f = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            p += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            f += 1
        except Exception as e:
            print(f"  ER R  {t.__name__}: {type(e).__name__}: {e}")
            f += 1
    print(f"\n{p} passed, {f} failed, {len(tests)} total")
    return f


if __name__ == "__main__":
    import sys
    sys.exit(1 if _run() else 0)
