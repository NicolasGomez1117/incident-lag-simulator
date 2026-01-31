from __future__ import annotations

import argparse
import csv
import hashlib
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml  # pip install pyyaml
except ImportError as e:
    raise SystemExit("Missing dependency: pyyaml. Install with: pip install pyyaml") from e


# ----------------------------
# Model (minimal, deterministic)
# ----------------------------

@dataclass(frozen=True)
class Params:
    propagation_lag_ticks: int
    observer_cache_ttl_ticks: int
    automation_trigger_after_ticks: int


@dataclass
class State:
    tick: int = 0

    # Control-plane state
    role_attached_tick: Optional[int] = None
    required_role: str = "unknown"

    # Service identity lifecycle
    service_account_deployed: bool = False
    service_account_in_use: bool = False
    service_account_revoked: bool = False

    # Observability (lag via caching)
    cached_red_until_tick: Optional[int] = None
    consecutive_observed_red: int = 0

    # Audit fields
    operator_assumption_tick: Optional[int] = None
    automation_action_tick: Optional[int] = None

    # Counters for metrics
    total_requests: int = 0
    denied_requests: int = 0
    revoked_requests: int = 0


def _load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _region_enforces_role(tick: int, role_attached_tick: Optional[int], lag: int) -> bool:
    if role_attached_tick is None:
        return False
    return tick >= (role_attached_tick + lag)


def _service_request(state: State, params: Params, regions: List[str]) -> Tuple[bool, str]:
    """
    One request per tick. Fails if:
    - SA not deployed/in use (pre-start)
    - SA revoked (post-wrong decision)
    - any region hasn't enforced role yet (simple multi-region dependency)
    """
    if not state.service_account_in_use:
        return False, "SERVICE_NOT_STARTED"
    if state.service_account_revoked:
        return False, "SERVICE_ACCOUNT_REVOKED"

    for r in regions:
        if not _region_enforces_role(state.tick, state.role_attached_tick, params.propagation_lag_ticks):
            return False, f"PERMISSION_DENIED({r})"

    return True, "OK"


def _observer_color(state: State, params: Params, request_ok: bool) -> str:
    """
    Observability lag: cache RED for TTL ticks.
    If OK arrives while cache active, observer still reports RED.
    """
    if not request_ok:
        state.cached_red_until_tick = state.tick + params.observer_cache_ttl_ticks
        return "RED"

    if state.cached_red_until_tick is not None and state.tick <= state.cached_red_until_tick:
        return "RED"
    return "GREEN"


def _automation_step(state: State, params: Params, observed_color: str) -> Optional[str]:
    """
    Wrong decision:
    If observer reports RED for N consecutive ticks, revoke SA.
    """
    if observed_color == "RED":
        state.consecutive_observed_red += 1
    else:
        state.consecutive_observed_red = 0

    if (not state.service_account_revoked) and (state.consecutive_observed_red >= params.automation_trigger_after_ticks):
        state.service_account_revoked = True
        state.automation_action_tick = state.tick
        return "AUTOMATION_REVOKE_SERVICE_ACCOUNT (misclassified propagation lag as compromise/misconfig)"
    return None


def _apply_event(state: State, event: Dict[str, Any]) -> str:
    e = event["event"]
    if e == "deploy_service_account":
        state.service_account_deployed = True
        return "deploy_service_account"
    if e == "attach_required_role":
        state.role_attached_tick = state.tick
        state.required_role = event.get("details", {}).get("role", "unknown_role")
        return f"attach_required_role({state.required_role}) control_plane_ack"
    if e == "service_starts_using_service_account":
        if not state.service_account_deployed:
            # Keep deterministic and explicit: if config is wrong, fail hard.
            raise ValueError("service started using SA before SA deployed")
        state.service_account_in_use = True
        return "service_starts_using_service_account"
    if e == "operator_assumes_propagation_complete":
        state.operator_assumption_tick = state.tick
        return "operator_assumes_propagation_complete (control-plane view)"
    raise ValueError(f"Unknown event: {e}")


def run(config_path: str) -> Tuple[List[str], List[Dict[str, Any]], Dict[str, Any]]:
    cfg = _load_config(config_path)

    scenario = cfg["scenario"]
    max_tick = int(scenario["max_tick"])

    p = cfg["parameters"]
    params = Params(
        propagation_lag_ticks=int(p["propagation_lag_ticks"]),
        observer_cache_ttl_ticks=int(p["observer_cache_ttl_ticks"]),
        automation_trigger_after_ticks=int(p["automation_trigger_after_ticks"]),
    )

    regions = list(cfg["actors"]["regions"])

    events_by_tick: Dict[int, List[Dict[str, Any]]] = {}
    for item in cfg["incident_events"]:
        t = int(item["tick"])
        events_by_tick.setdefault(t, []).append(item)

    state = State()
    timeline_lines: List[str] = []
    metrics_rows: List[Dict[str, Any]] = []

    for t in range(0, max_tick + 1):
        state.tick = t

        # Apply external incident events (deterministic order as listed)
        for ev in events_by_tick.get(t, []):
            action = _apply_event(state, ev)
            timeline_lines.append(f"T{t}: EVENT {action}")

        # Service request
        ok, reason = _service_request(state, params, regions)
        state.total_requests += 1
        if "PERMISSION_DENIED" in reason:
            state.denied_requests += 1
        if reason == "SERVICE_ACCOUNT_REVOKED":
            state.revoked_requests += 1

        timeline_lines.append(f"T{t}: REQUEST {reason}")

        # Observer
        obs = _observer_color(state, params, ok)
        timeline_lines.append(f"T{t}: OBSERVER {obs} consecutive_red={state.consecutive_observed_red}")

        # Automation
        auto = _automation_step(state, params, obs)
        if auto:
            timeline_lines.append(f"T{t}: DECISION WRONG {auto}")

        # Metrics per tick (simple + interview-readable)
        metrics_rows.append(
            {
                "tick": t,
                "request_result": reason,
                "observer": obs,
                "consecutive_observed_red": state.consecutive_observed_red,
                "service_account_revoked": int(state.service_account_revoked),
                "role_attached_tick": "" if state.role_attached_tick is None else state.role_attached_tick,
            }
        )

    summary = {
        "scenario_name": scenario["name"],
        "max_tick": max_tick,
        "required_role": state.required_role,
        "role_attached_tick": state.role_attached_tick,
        "operator_assumption_tick": state.operator_assumption_tick,
        "automation_action_tick": state.automation_action_tick,
        "total_requests": state.total_requests,
        "denied_requests": state.denied_requests,
        "revoked_requests": state.revoked_requests,
        "propagation_lag_ticks": params.propagation_lag_ticks,
        "observer_cache_ttl_ticks": params.observer_cache_ttl_ticks,
        "automation_trigger_after_ticks": params.automation_trigger_after_ticks,
    }

    return timeline_lines, metrics_rows, summary


# ----------------------------
# Frozen artifact contract
# ----------------------------

def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _read_bytes(path: str) -> Optional[bytes]:
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _serialize_csv(rows: List[Dict[str, Any]]) -> bytes:
    if not rows:
        return b""
    import io
    buf = io.StringIO()
    fieldnames = list(rows[0].keys())
    w = csv.DictWriter(buf, fieldnames=fieldnames)
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue().encode("utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Deterministic incident replay + frozen-output verifier")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--outdir", default="output")
    ap.add_argument("--write", action="store_true", help="write/overwrite frozen artifacts")
    ap.add_argument("--verify", action="store_true", help="verify frozen artifacts (default)")
    args = ap.parse_args()

    if not args.write and not args.verify:
        args.verify = True

    timeline_lines, metrics_rows, summary = run(args.config)

    timeline_text = "\n".join(timeline_lines) + "\n"
    metrics_bytes = _serialize_csv(metrics_rows)

    timeline_path = os.path.join(args.outdir, "timeline.log")
    metrics_path = os.path.join(args.outdir, "metrics.csv")

    existing_tl = _read_bytes(timeline_path)
    existing_mx = _read_bytes(metrics_path)

    new_tl = timeline_text.encode("utf-8")
    new_mx = metrics_bytes

    if args.verify and not args.write:
        if existing_tl is None or existing_mx is None:
            raise SystemExit(
                "Frozen artifacts missing. Run once with: python simulate_incident.py --write"
            )
        if _sha256_bytes(existing_tl) != _sha256_bytes(new_tl):
            raise SystemExit(
                "timeline.log mismatch vs canonical replay. If intentional, re-freeze with --write and commit."
            )
        if _sha256_bytes(existing_mx) != _sha256_bytes(new_mx):
            raise SystemExit(
                "metrics.csv mismatch vs canonical replay. If intentional, re-freeze with --write and commit."
            )
        # Print compact summary for human sanity (does not affect artifacts)
        print("VERIFY OK")
        for k in [
            "scenario_name",
            "role_attached_tick",
            "operator_assumption_tick",
            "automation_action_tick",
            "denied_requests",
            "revoked_requests",
        ]:
            print(f"{k}={summary.get(k)}")
        return

    # --write path (freeze artifacts)
    _write_text(timeline_path, timeline_text)
    _write_csv(metrics_path, metrics_rows)

    print("WROTE FROZEN ARTIFACTS")
    print(f"{timeline_path}")
    print(f"{metrics_path}")
    for k in [
        "scenario_name",
        "role_attached_tick",
        "operator_assumption_tick",
        "automation_action_tick",
        "denied_requests",
        "revoked_requests",
    ]:
        print(f"{k}={summary.get(k)}")


if __name__ == "__main__":
    main()
