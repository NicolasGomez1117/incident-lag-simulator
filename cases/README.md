# Supporting Cases

This directory contains **supporting incident artifacts** that instantiate the
same failure pattern as the canonical incident frozen at the repository root.

These cases are **not additional simulations** and do not alter the repository
contract. They exist to demonstrate how the same lag-induced decision failure
manifests across different substrates (hardware, infrastructure, automation).

The authoritative incident for this repository remains the replay defined by:
- `output/timeline.log`
- `simulate_incident.py`

## Purpose

Supporting cases serve to:
- ground abstract lag dynamics in real systems
- show invariant violations outside the simulated environment
- demonstrate operator decision boundaries under partial observability

## Structure

cases/
└── <case-name>/
└── incident.md


Each `incident.md` is a frozen, closed artifact describing:
- the invariant under test
- the observed violation
- the diagnostic actions taken
- the decision to halt investigation and mitigate

Supporting cases do **not** introduce variants, counterfactuals, or alternative
timelines.

## Constraints

- Supporting cases must align with the lag/decision failure pattern of the
  canonical incident.
- They do not modify or expand the simulation.
- They are reference material, not executable scenarios.