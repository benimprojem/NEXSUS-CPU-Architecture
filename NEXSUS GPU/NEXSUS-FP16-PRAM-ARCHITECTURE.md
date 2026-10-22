# NEXSUS FP16 Execution and Per-Line PRAM Architecture

**Document code:** NEXSUS-GPU-FP16-PRAM-001  
**Topic:** FP16 execution paths and conflict-aware local PRAM  
**Status:** Conceptual architecture / simulation model — not validated hardware

## 1. Purpose

This document defines the current conceptual model for testing NEXSUS FP16 execution alongside independently addressable PRAM pages owned by each Line. The goal is to model parallel access and serialize only true address conflicts, rather than treating all PRAM accesses as a single shared bottleneck.

## 2. Current structural model

- 4 Groups
- 8 Lines per Group
- 32 Lines total
- 2 independent FP16 execution paths per Line
- 2 independent PRAM pages owned by each Line
- 16 KiB per PRAM page

This yields 64 PRAM pages and a total capacity of 1 MiB across the four Groups.

| Resource | Per Line | Per Group | Four Groups |
|---|---:|---:|---:|
| Lines | 1 | 8 | 32 |
| FP16 execution paths | 2 | 16 | 64 |
| PRAM pages | 2 | 16 | 64 |
| PRAM capacity | 32 KiB | 256 KiB | 1 MiB |

## 3. Addressing and access rules

1. Each Line's two pages are separately addressable resources.
2. Requests to distinct addresses may proceed in parallel, subject to the eventual physical implementation's access ports and timing.
3. Requests that conflict on the same address are arbitrated. In the test model, repeated reads can be broadcast when enabled; a write that overlaps another access to the same address conflicts.
4. A conflict delays only the affected request(s); unrelated addresses and Lines continue.
5. Page capacity does not itself specify bandwidth. Actual throughput still depends on port count, access granularity, arbitration, and read/write timing.
6. The simulator exposes `--read-ports-per-page` and `--write-ports-per-page`. Defaults are two distinct-address reads and two distinct-address writes per page per cycle. These are **test parameters**, not finalized hardware guarantees.
7. Reads and writes are modeled in separate phases. This simplified schedule does not yet model a true dual-port SRAM timing diagram, read-after-write hazards, or address-bank layout.

The Python model intentionally implements address-conflict behavior, not a complete physical SRAM/PRAM port design. Its assumptions must be revisited once the electrical memory structure and number of simultaneous ports are defined.

## 4. FP16 execution workload

Each Line can issue up to two FP16 operations per cycle in the ideal execution model. For a workload of 16 operations per path:

- 32 Lines × 2 paths × 16 operations = 1,024 FP16 operations.
- Ideal issue lower bound: 16 cycles, if all paths remain supplied and memory introduces no stalls.
- Arithmetic latency is modeled separately from issue interval. The default arithmetic latency is 2 cycles, but the parameter is configurable.

The ideal issue lower bound is not a predicted end-to-end completion time: operand availability, result writes, arbitration, and physical timing can increase it.

## 5. Python simulation

File: `nexsus_fp16_pram_sim.py`

Default run:

```bash
python nexsus_fp16_pram_sim.py
```

Deliberate same-Line address conflict case:

```bash
python nexsus_fp16_pram_sim.py --pattern path_collision
```

Disable same-address read broadcast:

```bash
python nexsus_fp16_pram_sim.py --pattern path_collision --no-read-broadcast
```

Increase operations per FP16 path:

```bash
python nexsus_fp16_pram_sim.py --ops-per-path 64 --latency 2
```

Compare simplified scalar and packed FP16 issue models:

```bash
python nexsus_fp16_pram_sim.py --compare-fp16
```

Test a narrower page interface:

```bash
python nexsus_fp16_pram_sim.py --read-ports-per-page 1 --write-ports-per-page 1
```

The default of two read and two write ports per page is an adjustable architectural assumption. The simulator's `conflict_rejections` counter counts rejected attempts across cycles, not unique operations, so one stalled request may be counted more than once.

The `unique` pattern assigns distinct operand and destination addresses to demonstrate the conflict-free case. The `path_collision` pattern intentionally makes both execution paths within a Line access the same addresses, to exercise arbitration. These are controlled test patterns, not claims about a real application workload.

## 6. Port-count sweep (simulation output)

Default workload: 1,024 operations, 2-cycle arithmetic latency, 32 Lines, two FP16 paths per Line. The table sets read and write ports per page to the same value.

| Pattern | Read/write ports per page | Elapsed cycles | Average FP16 operations/cycle | Conflict cycles |
|---|---:|---:|---:|---:|
| Unique addresses | 1 | 34 | 30.12 | 31 |
| Unique addresses | 2 | 18 | 56.89 | 0 |
| Unique addresses | 4 | 18 | 56.89 | 0 |
| Unique addresses | 8 | 18 | 56.89 | 0 |
| Same-Line path destination collision | 1 | 34 | 30.12 | 31 |
| Same-Line path destination collision | 2 | 19 | 53.89 | 16 |
| Same-Line path destination collision | 4 | 19 | 53.89 | 16 |
| Same-Line path destination collision | 8 | 19 | 53.89 | 16 |

Interpretation: for this synthetic address pattern, two read and two write ports per page are sufficient to feed the two FP16 paths without port stalls. Raising the port count above two does not improve this workload. When both paths target the same destination address, the duplicate write remains a conflict even with more ports; additional ports cannot remove a same-address hazard.

These values are simulator outputs under explicit assumptions, not measured hardware performance. `conflict_cycles` counts cycles in which at least one request was rejected; `conflict_rejections` counts rejected attempts across cycles, so a stalled request can be counted repeatedly.

## 7. Comparison with NVIDIA

A fair comparison must distinguish the programming model and the actual device. NVIDIA CUDA groups threads into 32-thread warps; a warp normally issues a common instruction across active lanes, while the throughput of FP16 operations depends on GPU generation, instruction form, and whether packed two-value operations such as `half2` are used. NVIDIA's documentation explicitly reports architecture-dependent throughput and describes packed FP16 operations.

The optional `--compare-fp16` output therefore uses transparent idealized issue models, not measured NVIDIA results:

- NEXSUS reference: 32 Lines × 2 scalar FP16 paths = 64 values/cycle.
- NVIDIA scalar reference: 32 values/cycle for one 32-thread warp issuing one scalar FP16 operation per lane per cycle.
- NVIDIA packed reference: 64 values/cycle for one 32-thread warp issuing one suitable `half2` operation per lane per cycle.

These are deliberately simplified instruction-issue references. Real throughput depends on GPU generation, instruction type, occupancy, scheduling, and data movement. The comparison does not claim NEXSUS is faster than a specific NVIDIA GPU.

References:

- NVIDIA, [CUDA C++ Programming Guide 12.9.2 — Instruction Throughput](https://docs.nvidia.com/cuda/archive/12.9.2/cuda-c-programming-guide/index.html)
- NVIDIA, [CUDA Best Practices Guide — Native Arithmetic Throughput](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html)
- NVIDIA, [Mixed-Precision Programming with CUDA 8 — FP16 and half2](https://developer.nvidia.com/blog/mixed-precision-programming-cuda-8/)

## 8. Limitations and next decisions

The current model does not yet specify:

- Whether the selected per-page read/write port counts are physically realizable in the intended memory-cell design.
- Whether reads and writes can occur simultaneously on the same page.
- Whether each execution path has dedicated operand ports or uses a shared Line-level access network.
- Read and write latency, arbitration policy, and clock-domain details.
- Register-file behavior versus PRAM behavior.
- FP16 instruction semantics, rounding mode, fused operations, and dependency chains.
- The exact NVIDIA GPU and kernel used for an apples-to-apples comparison.

These are open design parameters, not implicit guarantees. The next step is to settle the per-page access contract and extend the simulator with configurable read/write port limits, then validate the scheduling model with several address patterns.
