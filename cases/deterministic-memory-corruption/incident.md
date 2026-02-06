# Incident: Deterministic Memory Corruption Under Stock Configuration

## Incident Type
Structural correctness failure under partial observability

## Summary
A system exhibited persistent instability traced to deterministic memory corruption.
Through controlled isolation and invariant-based testing, the fault was localized to the motherboard memory subsystem rather than RAM modules, CPU configuration, or environmental factors.
Mitigation was selected over further diagnosis due to unfavorable cost–benefit tradeoffs.

---

## System Context
- Platform: AMD AM4
- CPU: Ryzen 5 5600
- Motherboard: MSI B550 Gaming GEN3
- Memory: Multiple DDR4 DIMMs (known-good)
- Environment: Stock clocks, stable power, normal ambient temperature

---

## Invariant
**Memory reads must be stable and deterministic across identical inputs under stock (JEDEC) configuration.**

Violation of this invariant constitutes a correctness failure independent of OS or workload.

---

## Observed Violation
- MemTest86+ reported repeatable bit errors
- Errors reproduced across reboots
- Bit flip location consistent across runs

---

## Diagnostic Actions

### Baseline Enforcement
- Disabled XMP
- Disabled CPU boost
- Restored JEDEC memory settings

### Deterministic Testing
- Bare-metal MemTest86+ execution
- No operating system involved

### Fault Isolation
- Tested multiple independent RAM sticks
- Tested multiple DIMM slots
- Failure persisted across all combinations

### Variables Explicitly Ruled Out
- Defective RAM modules
- Slot-specific DIMM failure
- Overclocking or timing misconfiguration
- Environmental instability

---

## Root Cause Classification
**Structural motherboard-level memory-path integrity failure**

Likely involving signal integrity or PCB routing defect.
Not recoverable via firmware, configuration, or software mitigation.

---

## Decision
Further debugging halted.

**Mitigation selected:** full motherboard replacement.

### Rationale
- Deterministic correctness violation
- High risk of silent data corruption
- Diminishing diagnostic returns
- Replacement cost lower than continued investigation

---

## Outcome
- Board marked defective
- Replacement initiated
- Incident closed

---

## Lessons
- Deterministic corruption across independent components strongly indicates structural failure.
- Stock-baseline enforcement is mandatory before attribution.
- Knowing when to stop debugging is a core reliability skill.

---
