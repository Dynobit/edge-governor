# Edge Governor — reproducible verdicts + verifiable estate

Two claims, both checkable from this repo alone:

1. **The edge map is receipt-backed.** `governor.py` is the truth-gate that produced
   ATLAS.md / CREDENTIAL.md. Run it against the bundled receipts:

       EDGE_TOPO=fixtures/topology python3 governor.py
       python3 test_governor.py        # 11 gate tests

2. **The track record derives from public data.** `verify_estate.py` recomputes the
   estate from Hyperliquid's public info API and validates the published hash-chained
   history (each record embeds sha256 of the previous line — edit anything and every
   later link breaks):

       python3 verify_estate.py --address <published address> --chain estate_chain.jsonl

stdlib only. No keys. Nothing here signs, deploys, or moves funds.
Fixture surfaces are sanitized copies of the live lane state the governor gated on
(internal hosts redacted; verdict-relevant numbers untouched).

## Published estate (verify it yourself)

Main Hyperliquid account: `0xbe6C1b09662BbE52CC93279D103Feb27985DdBc1`
The committed `estate_chain.jsonl` is the hash-chained history for the whole estate
(all addresses inside it). Recompute right now:

    python3 verify_estate.py --address 0xbe6C1b09662BbE52CC93279D103Feb27985DdBc1 --chain estate_chain.jsonl

Anything that doesn't recompute is a lie — call it out.
