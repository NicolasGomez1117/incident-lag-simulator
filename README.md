# incident-lag-simulator

**G2 Canonicalization repo. Single incident only. No variants.**

This repository freezes exactly one replayable incident where **observability lag**
causes a wrong operator/automation decision.

## The incident (3-minute explanation)
A role attachment is ACKed by the **control plane**, but **data-plane enforcement lags**.
Requests fail with `PERMISSION_DENIED(region)` during propagation.
The observer caches RED (stale health), and automation interprets sustained RED as
compromise/misconfiguration and **revokes the service account**.

Result: a transient propagation delay becomes a sustained outage (`SERVICE_ACCOUNT_REVOKED`).

## Replay
Frozen artifacts:
- `output/timeline.log`
- `output/metrics.csv`

Run replay and verify frozen outputs:
```bash
pip install pyyaml
python simulate_incident.py --verify
```

## Contract

### Scope
This repository freezes **exactly one** lag-induced failure.
It is intentionally **not** a framework, library, or collection of scenarios.
Any change to the incident requires re-freezing the canonical outputs.

### Timeline anchor
`output/timeline.log` is the authoritative event sequence.
All narratives, metrics, and explanations must reference specific ticks
in this file.
