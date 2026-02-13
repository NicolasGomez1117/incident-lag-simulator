# Artifact ID: incident_gpu_driver_branch_regression_win11_25h2_2026q1

# Layered Graphics Stack Failure Isolation Under Capital Constraint

## Incident Type
Layered fault isolation under partial observability

## Invariant
Graphics stack initialization must complete under stable subsystem stress, with no deterministic hardware-fault signal in CPU, memory, or board telemetry.

## Initial Symptom Surface
- Failed to initialize graphics device
- Immediate error on application launch
- No full system crash

## Initial Hypothesis
- Possible power surge damage
- IMC lane failure suspicion
- Hardware replacement consideration

## Observability & Stress Testing
- Prime95 Blend (30 min clean)
- HWiNFO thermals stable
- No WHEA errors
- Controlled GPU stack reset

## Controlled Remediation
- DDU in Safe Mode
- Offline rollback to 581.57 Studio
- Shader cache purge
- Deterministic state rebuild

## Capital Constraint Influence
- No immediate hardware swap
- Forced deeper diagnostic rigor
- Avoided premature CPU/motherboard replacement

## Layer Boundary Lessons
- Error surface != failure surface
- Application-level DX failure != GPU silicon fault
- Driver branch regression under Windows 11 25H2 classified as root cause after hardware stress isolation and deterministic rollback restored function.

## Reliability Principles Extracted
- Eliminate hardware before replacing hardware
- Always stress subsystems independently
- Remove entropy before testing hypothesis
- Control auto-update mechanisms

## Hypothesis Evolution
1. Starting hypothesis: IMC or board-path damage after instability signal.
2. Isolation evidence: Prime95 Blend completed, HWiNFO remained stable, and no WHEA events were observed during stress.
3. Stack manipulation evidence: failure behavior changed only after GPU driver branch reset and offline rollback workflow.
4. Controlled rollback to 581.57 Studio WHQL resulted in immediate restoration of graphics stack initialization.
5. Hardware-fault hypothesis falsified under subsystem stress and telemetry review.
6. Driver-branch regression under Windows 11 25H2 classified as incident root cause with bounded confidence.

## Layered Stack Frame
1. Power
2. IMC
3. RAM
4. Driver
5. DX
6. Application

## Outcome
- Application (League of Legends) successfully initialized and loaded into match environment after driver rollback.
- No recurrence of "failed to initialize graphics device" error under normal load.
- No system instability observed post-remediation.
- Remediation confirmed reproducible across restarts.

Status: Incident resolved under current driver branch (581.57 Studio WHQL).

## Remediation Confirmation Conditions
- Driver version pinned to 581.57 Studio WHQL.
- NVIDIA auto-update disabled.
- No GeForce Experience installed.
- No WHEA or driver reset events observed post-fix.
- System stable under Prime95 and application-level GPU load.

This classification remains valid unless:
- Regression reappears under identical configuration.
- Independent subsystem instability emerges.

## Economic Constraint Impact
Capital limitation prevented premature hardware replacement.
Constraint increased diagnostic rigor and reduced probabilistic hardware replacement error.

Counterfactual:
Absent constraint, CPU or motherboard replacement may have occurred without evidence.

## Cross-References
- Related hardware-first artifact: `incident-lag-simulator/cases/deterministic-memory-corruption/incident.md`
- Mirror path for this artifact: `failure-under-lag/simulator/cases/incident_gpu_driver_branch_regression_win11_25h2_2026q1/incident.md`
