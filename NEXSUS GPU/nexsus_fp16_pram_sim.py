#!/usr/bin/env python3
"""NEXSUS FP16 + per-Line PRAM access model (architectural simulation, not hardware benchmark).

Default model:
- 4 Groups x 8 Lines = 32 Lines
- Each Line owns two independent 16 KiB PRAM pages
- Per-page read/write port counts are configurable (default: 2 each)
- Each Line has two FP16 execution paths
- An operation reads two FP16 operands and writes one FP16 result
- Distinct addresses may be accessed in parallel
- Read/read to the same address can broadcast; any access involving a write
  conflicts with another access to the same address in the same cycle
- Each Line may issue at most two FP16 operations per cycle
- FP16 arithmetic latency is configurable; issue interval is one cycle

This models address conflicts only. Real implementation still needs a defined
register/PRAM port structure, arbitration, bank timing, and physical validation.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple

Address = Tuple[int, int, int]  # (line_id, page_id, FP16-word offset)

@dataclass
class Operation:
    op_id: int
    group: int
    line: int
    path: int
    index: int
    src_a: Address
    src_b: Address
    dst: Address
    state: str = "waiting_reads"  # waiting_reads, computing, waiting_write, done
    reads_done_cycle: int = -1
    ready_write_cycle: int = -1
    done_cycle: int = -1


def make_address(line_id: int, page: int, offset: int) -> Address:
    if page not in (0, 1):
        raise ValueError("page must be 0 or 1")
    if not 0 <= offset < (16 * 1024 // 2):
        raise ValueError("FP16 offset must fit in a 16 KiB page")
    return (line_id, page, offset)


def build_operations(ops_per_path: int, pattern: str) -> List[Operation]:
    ops: List[Operation] = []
    op_id = 0
    for group in range(4):
        for local_line in range(8):
            line_id = group * 8 + local_line
            # Interleave the two paths' operation queues so both paths can issue
            # in the same cycle instead of accidentally favoring path 0.
            for i in range(ops_per_path):
                for path in range(2):
                    if pattern == "unique":
                        # Each operation uses distinct source/destination addresses.
                        base = (path * ops_per_path + i) * 3
                        src_a = make_address(line_id, 0, base)
                        src_b = make_address(line_id, 1, base + 1)
                        dst = make_address(line_id, 0, base + 2)
                    elif pattern == "path_collision":
                        # The two paths of each Line deliberately write the same
                        # destination address at corresponding indices. Reads can
                        # broadcast, but the duplicate writes must be serialized.
                        base = i * 3
                        src_a = make_address(line_id, 0, base + path)
                        src_b = make_address(line_id, 1, base + path)
                        dst = make_address(line_id, 0, base + 2)
                    else:
                        raise ValueError(f"unknown pattern: {pattern}")
                    ops.append(Operation(op_id, group, line_id, path, i, src_a, src_b, dst))
                    op_id += 1
    return ops


def address_accesses_conflict(accesses: List[Tuple[Address, str]], read_broadcast: bool,
                              ports_per_page: int | None = None) -> bool:
    """Return True if the set cannot all be served in one cycle.

    Access type is 'R' or 'W'. Read/read to the same address is allowed when
    read_broadcast=True; all other duplicate-address combinations conflict.
    """
    by_addr: Dict[Address, List[str]] = defaultdict(list)
    for addr, kind in accesses:
        by_addr[addr].append(kind)
    for kinds in by_addr.values():
        if len(kinds) > 1:
            if read_broadcast and all(k == "R" for k in kinds):
                continue
            return True
    if ports_per_page is not None:
        unique_per_page = defaultdict(set)
        for addr, _kind in accesses:
            unique_per_page[addr[:2]].add(addr)
        if any(len(addresses) > ports_per_page for addresses in unique_per_page.values()):
            return True
    return False


def simulate(ops_per_path: int = 16, latency: int = 2,
             pattern: str = "unique", read_broadcast: bool = True,
             read_ports_per_page: int = 2, write_ports_per_page: int = 2,
             max_cycles: int = 100000) -> dict:
    ops = build_operations(ops_per_path, pattern)
    pending_reads = list(ops)
    computing: List[Operation] = []
    pending_writes: List[Operation] = []
    done: List[Operation] = []
    cycle = 0
    conflict_cycles = 0
    total_conflict_rejections = 0
    access_count = 0

    while len(done) < len(ops):
        if cycle > max_cycles:
            raise RuntimeError("simulation exceeded max_cycles; check model or workload")

        # Move completed arithmetic operations to the write queue.
        for op in list(computing):
            if op.ready_write_cycle <= cycle:
                op.state = "waiting_write"
                pending_writes.append(op)
                computing.remove(op)

        # READ phase: each Line has two FP16 issue paths. Each operation needs
        # both source reads accepted in this cycle in this simplified model.
        selected_reads: List[Operation] = []
        per_line_path = defaultdict(int)
        read_accesses: List[Tuple[Address, str]] = []
        rejected_reads: List[Operation] = []
        for op in pending_reads:
            if per_line_path[(op.line, op.path)] >= 1:
                continue
            trial = read_accesses + [(op.src_a, "R"), (op.src_b, "R")]
            if address_accesses_conflict(trial, read_broadcast, read_ports_per_page):
                rejected_reads.append(op)
                continue
            selected_reads.append(op)
            per_line_path[(op.line, op.path)] += 1
            read_accesses = trial
        if rejected_reads:
            total_conflict_rejections += len(rejected_reads)
            conflict_cycles += 1
        for op in selected_reads:
            pending_reads.remove(op)
            op.state = "computing"
            op.reads_done_cycle = cycle
            op.ready_write_cycle = cycle + latency
            computing.append(op)
            access_count += 2

        # WRITE phase: one write per distinct address per cycle. Writes can be
        # serviced in parallel if they target distinct addresses.
        selected_writes: List[Operation] = []
        write_addresses = set()
        writes_per_page = defaultdict(set)
        rejected_writes: List[Operation] = []
        for op in pending_writes:
            page_key = op.dst[:2]
            if op.dst in write_addresses or (op.dst not in writes_per_page[page_key]
                    and len(writes_per_page[page_key]) >= write_ports_per_page):
                rejected_writes.append(op)
                continue
            selected_writes.append(op)
            write_addresses.add(op.dst)
            writes_per_page[page_key].add(op.dst)
        if rejected_writes:
            total_conflict_rejections += len(rejected_writes)
            conflict_cycles += 1
        for op in selected_writes:
            pending_writes.remove(op)
            op.state = "done"
            op.done_cycle = cycle
            done.append(op)
            access_count += 1

        cycle += 1

    total_ops = len(ops)
    elapsed_cycles = max(op.done_cycle for op in done) + 1
    return {
        "pattern": pattern,
        "groups": 4,
        "lines": 32,
        "pages_per_line": 2,
        "total_pages": 64,
        "page_size_kib": 16,
        "total_pram_kib": 1024,
        "fp16_paths_per_line": 2,
        "ops_per_path": ops_per_path,
        "total_fp16_ops": total_ops,
        "arithmetic_latency_cycles": latency,
        "read_broadcast": read_broadcast,
        "read_ports_per_page": read_ports_per_page,
        "write_ports_per_page": write_ports_per_page,
        "elapsed_cycles": elapsed_cycles,
        "average_ops_per_cycle": total_ops / elapsed_cycles,
        "ideal_issue_cycles_without_memory_conflicts": ops_per_path,
        "conflict_cycles": conflict_cycles,
        "conflict_rejections": total_conflict_rejections,
        "accepted_memory_accesses": access_count,
        "cycles_per_operation": elapsed_cycles / total_ops,
    }


def print_result(result: dict) -> None:
    print("\nNEXSUS FP16 + PRAM architecture simulation")
    print("=" * 44)
    for key, value in result.items():
        print(f"{key:42s}: {value}")
    print("\nNOTE: idealized model only; not a silicon benchmark.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ops-per-path", type=int, default=16,
                        help="FP16 operations per path per Line (default: 16)")
    parser.add_argument("--latency", type=int, default=2,
                        help="FP16 arithmetic latency in cycles (default: 2)")
    parser.add_argument("--pattern", choices=("unique", "path_collision"), default="unique",
                        help="unique addresses or deliberate same-Line path conflicts")
    parser.add_argument("--no-read-broadcast", action="store_true",
                        help="serialize reads to the same address instead of broadcasting")
    parser.add_argument("--read-ports-per-page", type=int, default=2,
                        help="simultaneous distinct reads per page per cycle (default: 2)")
    parser.add_argument("--write-ports-per-page", type=int, default=2,
                        help="simultaneous distinct writes per page per cycle (default: 2)")
    parser.add_argument("--compare-fp16", action="store_true",
                        help="print idealized scalar/packed FP16 issue reference models")
    args = parser.parse_args()
    if args.ops_per_path < 1 or args.latency < 1:
        parser.error("ops-per-path and latency must be >= 1")
    if args.read_ports_per_page < 1 or args.write_ports_per_page < 1:
        parser.error("page port counts must be >= 1")
    result = simulate(args.ops_per_path, args.latency, args.pattern,
                      not args.no_read_broadcast, args.read_ports_per_page,
                      args.write_ports_per_page)
    print_result(result)
    if args.compare_fp16:
        print("\nIdealized FP16 issue reference (same 32 logical work items)")
        print("=" * 58)
        total_values = 32 * 2 * args.ops_per_path
        models = [
            ("NEXSUS: 2 scalar paths/Line", 32 * 2),
            ("NVIDIA reference: scalar, 1 value/thread/cycle", 32),
            ("NVIDIA reference: packed half2, 2 values/thread/cycle", 64),
        ]
        for name, values_per_cycle in models:
            issue_cycles = (total_values + values_per_cycle - 1) // values_per_cycle
            completion_cycles = issue_cycles + args.latency
            print(f"{name:58s} values/cycle={values_per_cycle:3d} "
                  f"issue_cycles={issue_cycles:4d} completion_cycles={completion_cycles:4d}")
        print("NOTE: throughput references are simplified issue models, not measured GPU results.")


if __name__ == "__main__":
    main()
