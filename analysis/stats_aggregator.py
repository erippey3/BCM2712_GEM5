#!/usr/bin/env python3
"""
Aggregate recursive hardware perf CSV logs and gem5 stats.txt files into one CSV.

Run:
  python3 stats_aggregator.py /path/to/root -o combined_stats.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

META_COLUMNS = [
    "algorithm",
    "backend",
    "iteration",
    "problem_size",
    "threads",
    "source_path",
]

# Unified columns intended to be comparable between hardware perf and gem5.
# Not every backend can fill every column; missing values are left blank.
CANONICAL_COLUMNS = [
    # Time / execution
    "runtime_sec",              # benchmark/runtime.txt for hardware; simSeconds for gem5
    "perf_duration_sec",        # perf duration_time, hardware only
    "task_clock_sec",           # perf task-clock, hardware only
    "cpus_utilized",            # perf metric, hardware only
    "sim_seconds",              # gem5 only
    "host_seconds",             # gem5 simulator wall time, not equivalent to hardware runtime
    "host_tick_rate",
    "host_memory_bytes",
    "clock_ghz",                # perf metric for hardware; derived from gem5 clk_domain.clock

    # Instructions / cycles
    "cycles",                   # hardware: perf cycles; gem5: sum of CPU cycles
    "cycles_sum",               # gem5 sum of system.cpu*.numCycles
    "cycles_max",               # gem5 max core cycles, closer to elapsed simulated wall cycles
    "instructions",             # hardware: perf instructions; gem5: sum commitStats0.numInsts
    "instructions_not_nop",     # gem5 only when present
    "ops",                      # gem5 micro-ops when present
    "ipc",                      # hardware: instructions/cycles; gem5: instructions/cycles_sum
    "ipc_wall",                 # gem5: instructions/cycles_max
    "cpi",                      # 1/ipc when available
    "core_ipc_mean",
    "core_ipc_min",
    "core_ipc_max",

    # User/system time
    "user_time_sec",
    "system_time_sec",

    # Branches
    "branches",
    "branch_misses",
    "branch_miss_rate",
    "branch_predicted",
    "branch_mispredicted",
    "btb_lookups",
    "btb_hits",
    "btb_misses",
    "btb_hit_rate",

    # L1D / L1I cache-ish counters
    "l1d_accesses",
    "l1d_reads",
    "l1d_writes",
    "l1d_misses",
    "l1d_read_misses",
    "l1d_write_misses",
    "l1d_miss_rate",
    "l1i_accesses",
    "l1i_misses",
    "l1i_miss_rate",

    # L2 data/unified cache-ish counters
    "l2d_accesses",
    "l2d_reads",
    "l2d_writes",
    "l2d_misses",
    "l2d_miss_rate",
    "l2_accesses_total",
    "l2_misses_total",
    "l2_miss_rate_total",

    # TLB-ish counters
    "l1d_tlb_accesses",
    "l1d_tlb_misses",
    "l1d_tlb_miss_rate",
    "l1i_tlb_accesses",
    "l1i_tlb_misses",
    "l1i_tlb_miss_rate",
    "l2d_tlb_accesses",
    "l2d_tlb_misses",
    "l2d_tlb_miss_rate",

    # Memory/reference counters
    "mem_accesses",
    "mem_reads",
    "mem_writes",
    "load_insts",
    "store_insts",
    "vec_insts",
    "fp_insts",
    "int_insts",

    # gem5 pipeline-ish counters useful for model analysis, not hardware-equivalent
    "issue_rate",
    "fu_busy",
    "fu_busy_rate",
    "iq_full_events",
    "lsq_full_events",
    "rob_full_events",
    "sq_full_events",
    "dcache_blocked_no_mshrs_cycles",
    "icache_stall_cycles",
]


def clean_num(x: str) -> Optional[float]:
    """Convert perf/gem5 numeric strings to float, returning None for missing/nan-ish values."""
    if x is None:
        return None
    s = str(x).strip()
    if not s or s in {"<not", "not", "counted>", "supported>"}:
        return None
    s = s.replace("%", "")
    # perf -x, normally has no thousands separators. This still handles copied values.
    s = s.replace(",", "")
    try:
        v = float(s)
    except ValueError:
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return v


def div(num: Optional[float], den: Optional[float]) -> Optional[float]:
    if num is None or den is None or den == 0:
        return None
    return num / den


def add(row: Dict[str, Optional[float]], key: str, value: Optional[float]) -> None:
    if value is not None:
        row[key] = value


def unit_to_seconds(value: Optional[float], unit: str) -> Optional[float]:
    if value is None:
        return None
    unit = (unit or "").strip().lower()
    if unit in {"sec", "secs", "second", "seconds", "s"}:
        return value
    if unit in {"msec", "ms", "millisecond", "milliseconds"}:
        return value / 1e3
    if unit in {"usec", "us", "microsecond", "microseconds"}:
        return value / 1e6
    if unit in {"nsec", "ns", "nanosecond", "nanoseconds"}:
        return value / 1e9
    return value


def normalize_perf_event(name: str) -> str:
    """Turn perf event names like instructions:u or branch-misses into stable snake_case."""
    name = name.strip()
    name = re.sub(r":[ukhGHIpPS]+$", "", name)  # common perf privilege suffixes, e.g. :u
    name = name.replace("-", "_")
    name = name.replace("/", "_")
    name = re.sub(r"[^A-Za-z0-9_]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name


def parse_runtime_txt(path: Path) -> Optional[float]:
    if not path.exists():
        return None
    text = path.read_text(errors="replace")
    m = re.search(r"Elapsed\s+Time:\s*([0-9.eE+-]+)\s*seconds", text)
    if not m:
        return None
    return clean_num(m.group(1))


def parse_perf_csvs(run_dir: Path) -> Dict[str, object]:
    """Parse all group*.csv files in a hardware run directory."""
    events: Dict[str, float] = {}
    event_units: Dict[str, str] = {}
    event_stddev_pct: Dict[str, float] = {}
    metric_values: Dict[str, float] = {}
    metric_units: Dict[str, str] = {}

    for csv_path in sorted(run_dir.glob("group*.csv")):
        with csv_path.open(newline="", errors="replace") as f:
            reader = csv.reader(f)
            for fields in reader:
                if not fields:
                    continue
                if fields[0].strip().startswith("#"):
                    continue
                if len(fields) < 3:
                    continue

                value = clean_num(fields[0])
                unit = fields[1].strip() if len(fields) > 1 else ""
                event_raw = fields[2].strip() if len(fields) > 2 else ""
                if value is None or not event_raw:
                    continue

                event = normalize_perf_event(event_raw)
                # If the same event appears in multiple groups, keep the first occurrence.
                events.setdefault(event, value)
                event_units.setdefault(event, unit)

                if len(fields) > 3:
                    sd = clean_num(fields[3])
                    if sd is not None:
                        event_stddev_pct.setdefault(event, sd)

                # In your perf CSVs the last two fields are often metric value/unit, e.g. IPC or GHz.
                if len(fields) >= 8:
                    metric_val = clean_num(fields[6])
                    metric_unit = fields[7].strip()
                    if metric_val is not None and metric_unit:
                        metric_values.setdefault(event, metric_val)
                        metric_units.setdefault(event, metric_unit)

    row: Dict[str, Optional[float]] = {}

    runtime_sec = parse_runtime_txt(run_dir / "runtime.txt")
    add(row, "runtime_sec", runtime_sec)

    # Time-ish perf counters
    if "duration_time" in events:
        add(row, "perf_duration_sec", unit_to_seconds(events.get("duration_time"), event_units.get("duration_time", "ns")))
    if "task_clock" in events:
        add(row, "task_clock_sec", unit_to_seconds(events.get("task_clock"), event_units.get("task_clock", "msec")))
        add(row, "cpus_utilized", metric_values.get("task_clock"))
    if "user_time" in events:
        add(row, "user_time_sec", unit_to_seconds(events.get("user_time"), event_units.get("user_time", "ns")))
    if "system_time" in events:
        add(row, "system_time_sec", unit_to_seconds(events.get("system_time"), event_units.get("system_time", "ns")))

    # Core instructions/cycles
    cycles = events.get("cycles")
    instr = events.get("instructions", events.get("inst_retired"))
    add(row, "cycles", cycles)
    add(row, "instructions", instr)
    add(row, "ipc", div(instr, cycles))
    ipc = row.get("ipc")
    add(row, "cpi", div(1.0, ipc))
    add(row, "clock_ghz", metric_values.get("cycles"))

    # Branches
    branches = events.get("branches", events.get("br_retired", events.get("br_pred")))
    branch_misses = events.get("branch_misses", events.get("br_mis_pred_retired", events.get("br_mis_pred")))
    add(row, "branches", branches)
    add(row, "branch_misses", branch_misses)
    add(row, "branch_predicted", events.get("br_pred"))
    add(row, "branch_mispredicted", events.get("br_mis_pred"))
    add(row, "branch_miss_rate", div(branch_misses, branches))

    # Caches. ARM PMU event names use *_refill for misses/refills.
    l1d = events.get("l1d_cache")
    l1d_m = events.get("l1d_cache_refill")
    add(row, "l1d_accesses", l1d)
    add(row, "l1d_reads", events.get("l1d_cache_rd"))
    add(row, "l1d_writes", events.get("l1d_cache_wr"))
    add(row, "l1d_misses", l1d_m)
    add(row, "l1d_miss_rate", div(l1d_m, l1d))

    l1i = events.get("l1i_cache")
    l1i_m = events.get("l1i_cache_refill")
    add(row, "l1i_accesses", l1i)
    add(row, "l1i_misses", l1i_m)
    add(row, "l1i_miss_rate", div(l1i_m, l1i))

    l2d = events.get("l2d_cache")
    l2d_m = events.get("l2d_cache_refill")
    add(row, "l2d_accesses", l2d)
    add(row, "l2d_reads", events.get("l2d_cache_rd"))
    add(row, "l2d_writes", events.get("l2d_cache_wr"))
    add(row, "l2d_misses", l2d_m)
    add(row, "l2d_miss_rate", div(l2d_m, l2d))

    # TLBs
    for prefix, access_event, miss_event in [
        ("l1d_tlb", "l1d_tlb", "l1d_tlb_refill"),
        ("l1i_tlb", "l1i_tlb", "l1i_tlb_refill"),
        ("l2d_tlb", "l2d_tlb", "l2d_tlb_refill"),
    ]:
        a = events.get(access_event)
        m = events.get(miss_event)
        add(row, f"{prefix}_accesses", a)
        add(row, f"{prefix}_misses", m)
        add(row, f"{prefix}_miss_rate", div(m, a))

    # Memory/speculation-ish events
    add(row, "mem_accesses", events.get("mem_access"))
    add(row, "mem_reads", events.get("mem_access_rd"))
    add(row, "mem_writes", events.get("mem_access_wr"))
    add(row, "load_insts", events.get("ld_spec"))
    add(row, "store_insts", events.get("st_spec"))
    add(row, "fp_insts", events.get("vfp_spec"))

    # Optional raw perf columns. These are useful for debugging without exploding gem5 columns.
    raw = {f"perf_raw_{k}": v for k, v in events.items()}
    raw.update({f"perf_stddev_pct_{k}": v for k, v in event_stddev_pct.items()})

    return {"canonical": row, "raw": raw}


GEM5_STAT_RE = re.compile(r"^(?P<key>\S+)\s+(?P<value>[-+]?nan|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\b")
CPU_RE = re.compile(r"^system\.cpu(\d+)\.")
L2CACHE_RE = re.compile(r"^system\.l2cache\d+\.")


def parse_gem5_stats_file(path: Path) -> Dict[str, float]:
    stats: Dict[str, float] = {}
    with path.open(errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("-"):
                continue
            before_comment = line.split("#", 1)[0].rstrip()
            m = GEM5_STAT_RE.match(before_comment)
            if not m:
                continue
            value = clean_num(m.group("value"))
            if value is None:
                continue
            stats[m.group("key")] = value
    return stats


def sum_keys(stats: Dict[str, float], pattern: str) -> Optional[float]:
    rx = re.compile(pattern)
    vals = [v for k, v in stats.items() if rx.match(k)]
    if not vals:
        return None
    return float(sum(vals))


def values_for_keys(stats: Dict[str, float], pattern: str) -> List[float]:
    rx = re.compile(pattern)
    return [v for k, v in stats.items() if rx.match(k)]


def cpu_ids(stats: Dict[str, float]) -> List[int]:
    ids = set()
    for key in stats:
        m = CPU_RE.match(key)
        if m:
            ids.add(int(m.group(1)))
    return sorted(ids)


def sum_cpu_suffix(stats: Dict[str, float], suffix: str) -> Optional[float]:
    vals = []
    for cid in cpu_ids(stats):
        key = f"system.cpu{cid}.{suffix}"
        if key in stats:
            vals.append(stats[key])
    if not vals:
        return None
    return float(sum(vals))


def cpu_values(stats: Dict[str, float], suffix: str) -> List[float]:
    vals = []
    for cid in cpu_ids(stats):
        key = f"system.cpu{cid}.{suffix}"
        if key in stats:
            vals.append(stats[key])
    return vals


def parse_gem5_run(stats_path: Path) -> Dict[str, object]:
    stats = parse_gem5_stats_file(stats_path)
    row: Dict[str, Optional[float]] = {}

    sim_seconds = stats.get("simSeconds")
    add(row, "sim_seconds", sim_seconds)
    add(row, "runtime_sec", sim_seconds)
    add(row, "host_seconds", stats.get("hostSeconds"))
    add(row, "host_tick_rate", stats.get("hostTickRate"))
    add(row, "host_memory_bytes", stats.get("hostMemory"))

    sim_freq = stats.get("simFreq")
    clk_ticks = stats.get("system.clk_domain.clock")
    if sim_freq is not None and clk_ticks not in (None, 0):
        add(row, "clock_ghz", (sim_freq / clk_ticks) / 1e9)

    cycles_per_core = cpu_values(stats, "numCycles")
    cycles_sum = float(sum(cycles_per_core)) if cycles_per_core else None
    cycles_max = float(max(cycles_per_core)) if cycles_per_core else None
    add(row, "cycles", cycles_sum)
    add(row, "cycles_sum", cycles_sum)
    add(row, "cycles_max", cycles_max)

    instructions = sum_cpu_suffix(stats, "commitStats0.numInsts") or stats.get("simInsts")
    instructions_not_nop = sum_cpu_suffix(stats, "commitStats0.numInstsNotNOP") or sum_cpu_suffix(stats, "thread_0.numInsts")
    ops = sum_cpu_suffix(stats, "commitStats0.numOps") or stats.get("simOps")
    add(row, "instructions", instructions)
    add(row, "instructions_not_nop", instructions_not_nop)
    add(row, "ops", ops)
    add(row, "ipc", div(instructions, cycles_sum))
    add(row, "ipc_wall", div(instructions, cycles_max))
    add(row, "cpi", div(cycles_sum, instructions))

    ipcs = cpu_values(stats, "ipc")
    if ipcs:
        add(row, "core_ipc_mean", sum(ipcs) / len(ipcs))
        add(row, "core_ipc_min", min(ipcs))
        add(row, "core_ipc_max", max(ipcs))

    # Branches. Prefer committed branches and committed mispredicts.
    branches = sum_cpu_suffix(stats, "commitStats0.committedControl::IsControl")
    branch_misses = sum_cpu_suffix(stats, "branchPred.mispredicted_0::total") or sum_cpu_suffix(stats, "commit.branchMispredicts")
    add(row, "branches", branches)
    add(row, "branch_misses", branch_misses)
    add(row, "branch_miss_rate", div(branch_misses, branches))
    add(row, "branch_predicted", sum_cpu_suffix(stats, "fetch.predictedBranches"))
    add(row, "branch_mispredicted", sum_cpu_suffix(stats, "branchPred.mispredicted_0::total"))
    add(row, "btb_lookups", sum_cpu_suffix(stats, "branchPred.BTBLookups"))
    add(row, "btb_hits", sum_cpu_suffix(stats, "branchPred.BTBHits"))
    btb_lookups = row.get("btb_lookups")
    btb_hits = row.get("btb_hits")
    add(row, "btb_misses", None if btb_lookups is None or btb_hits is None else btb_lookups - btb_hits)
    add(row, "btb_hit_rate", div(btb_hits, btb_lookups))

    # L1D / L1I. demand* maps more closely to demand-side accesses than overall* because overall includes prefetches.
    l1d = sum_cpu_suffix(stats, "dcache.demandAccesses::total")
    l1d_m = sum_cpu_suffix(stats, "dcache.demandMisses::total")
    add(row, "l1d_accesses", l1d)
    add(row, "l1d_misses", l1d_m)
    add(row, "l1d_miss_rate", div(l1d_m, l1d))
    add(row, "l1d_reads", sum_cpu_suffix(stats, "dcache.ReadReq.accesses::total"))
    add(row, "l1d_writes", sum_cpu_suffix(stats, "dcache.WriteReq.accesses::total"))
    add(row, "l1d_read_misses", sum_cpu_suffix(stats, "dcache.ReadReq.misses::total"))
    add(row, "l1d_write_misses", sum_cpu_suffix(stats, "dcache.WriteReq.misses::total"))

    l1i = sum_cpu_suffix(stats, "icache.demandAccesses::total")
    l1i_m = sum_cpu_suffix(stats, "icache.demandMisses::total")
    add(row, "l1i_accesses", l1i)
    add(row, "l1i_misses", l1i_m)
    add(row, "l1i_miss_rate", div(l1i_m, l1i))

    # L2. Some configs have one l2cache per core; some have shared names. Sum all l2cacheN totals.
    l2_total = sum_keys(stats, r"^system\.l2cache\d+\.demandAccesses::total$")
    l2_m_total = sum_keys(stats, r"^system\.l2cache\d+\.demandMisses::total$")
    add(row, "l2_accesses_total", l2_total)
    add(row, "l2_misses_total", l2_m_total)
    add(row, "l2_miss_rate_total", div(l2_m_total, l2_total))

    # Data-side L2 if requestor names include cpuN.data.
    l2d = sum_keys(stats, r"^system\.l2cache\d+\.demandAccesses::cpu\d+\.data$")
    l2d_m = sum_keys(stats, r"^system\.l2cache\d+\.demandMisses::cpu\d+\.data$")
    add(row, "l2d_accesses", l2d)
    add(row, "l2d_misses", l2d_m)
    add(row, "l2d_miss_rate", div(l2d_m, l2d))

    # gem5 TLB stats often read as zero in SE mode depending on configuration; still collect them.
    l1d_tlb_a = (sum_cpu_suffix(stats, "mmu.dtb.readAccesses") or 0.0) + (sum_cpu_suffix(stats, "mmu.dtb.writeAccesses") or 0.0)
    l1d_tlb_m = (sum_cpu_suffix(stats, "mmu.dtb.readMisses") or 0.0) + (sum_cpu_suffix(stats, "mmu.dtb.writeMisses") or 0.0)
    add(row, "l1d_tlb_accesses", l1d_tlb_a)
    add(row, "l1d_tlb_misses", l1d_tlb_m)
    add(row, "l1d_tlb_miss_rate", div(l1d_tlb_m, l1d_tlb_a))

    l1i_tlb_a = sum_cpu_suffix(stats, "mmu.itb.instAccesses")
    l1i_tlb_m = sum_cpu_suffix(stats, "mmu.itb.instMisses")
    add(row, "l1i_tlb_accesses", l1i_tlb_a)
    add(row, "l1i_tlb_misses", l1i_tlb_m)
    add(row, "l1i_tlb_miss_rate", div(l1i_tlb_m, l1i_tlb_a))

    l2_tlb_a = sum_cpu_suffix(stats, "mmu.l2_shared.accesses")
    l2_tlb_m = sum_cpu_suffix(stats, "mmu.l2_shared.misses")
    add(row, "l2d_tlb_accesses", l2_tlb_a)
    add(row, "l2d_tlb_misses", l2_tlb_m)
    add(row, "l2d_tlb_miss_rate", div(l2_tlb_m, l2_tlb_a))

    # Memory refs and instruction classes from commit stats.
    add(row, "mem_accesses", sum_cpu_suffix(stats, "commitStats0.numMemRefs"))
    add(row, "mem_reads", sum_cpu_suffix(stats, "commitStats0.numLoadInsts"))
    add(row, "mem_writes", sum_cpu_suffix(stats, "commitStats0.numStoreInsts"))
    add(row, "load_insts", sum_cpu_suffix(stats, "commitStats0.numLoadInsts"))
    add(row, "store_insts", sum_cpu_suffix(stats, "commitStats0.numStoreInsts"))
    add(row, "vec_insts", sum_cpu_suffix(stats, "commitStats0.numVecInsts"))
    add(row, "fp_insts", sum_cpu_suffix(stats, "commitStats0.numFpInsts"))
    add(row, "int_insts", sum_cpu_suffix(stats, "commitStats0.numIntInsts"))

    # Pipeline/debug stats. Summed because there may be multiple CPUs.
    add(row, "issue_rate", div(sum_cpu_suffix(stats, "instsIssued"), cycles_sum))
    add(row, "fu_busy", sum_cpu_suffix(stats, "fuBusy"))
    add(row, "fu_busy_rate", div(row.get("fu_busy"), sum_cpu_suffix(stats, "executeStats0.numInsts")))
    add(row, "iq_full_events", sum_cpu_suffix(stats, "iew.iqFullEvents"))
    add(row, "lsq_full_events", sum_cpu_suffix(stats, "iew.lsqFullEvents"))
    add(row, "rob_full_events", sum_cpu_suffix(stats, "rename.ROBFullEvents"))
    add(row, "sq_full_events", sum_cpu_suffix(stats, "rename.SQFullEvents"))
    add(row, "dcache_blocked_no_mshrs_cycles", sum_cpu_suffix(stats, "dcache.blockedCycles::no_mshrs"))
    add(row, "icache_stall_cycles", sum_cpu_suffix(stats, "fetchStats0.icacheStallCycles"))

    # Selected raw gem5 stats for auditing. Avoid dumping thousands of columns by default.
    raw = {
        "gem5_raw_simInsts": stats.get("simInsts"),
        "gem5_raw_simOps": stats.get("simOps"),
        "gem5_raw_simTicks": stats.get("simTicks"),
        "gem5_raw_finalTick": stats.get("finalTick"),
    }
    return {"canonical": row, "raw": {k: v for k, v in raw.items() if v is not None}}


def infer_metadata(run_path: Path, stats_root_name: str = "stats") -> Optional[Dict[str, object]]:
    """
    Infer algorithm/backend/iteration/problem_size/thread from a run directory.

    Supported layouts:

      GEMM/stats/hardware/256/t2
      GEMM/stats/gem5/i2/256/t2

    Hardware has no iteration directory, so iteration is set to "none".
    """
    parts = run_path.resolve().parts

    for i, part in enumerate(parts):
        if part != stats_root_name:
            continue

        # Need at least:
        #   <algorithm>/stats/<backend>/...
        if i < 1 or i + 2 >= len(parts):
            continue

        algorithm = parts[i - 1]
        backend = parts[i + 1]

        if backend == "hardware":
            # <algorithm>/stats/hardware/<problem_size>/tN
            if i + 3 >= len(parts):
                continue

            iteration = "none"
            problem_size = parts[i + 2]
            thread_part = parts[i + 3]

        elif backend == "gem5":
            # <algorithm>/stats/gem5/<iteration>/<problem_size>/tN
            if i + 4 >= len(parts):
                continue

            iteration = parts[i + 2]
            problem_size = parts[i + 3]
            thread_part = parts[i + 4]

        else:
            continue

        m = re.fullmatch(r"t(\d+)", thread_part)
        if not m:
            continue

        return {
            "algorithm": algorithm,
            "backend": backend,
            "iteration": iteration,
            "problem_size": problem_size,
            "threads": int(m.group(1)),
            "source_path": str(run_path),
        }

    return None


def find_hardware_run_dirs(root: Path) -> Iterable[Path]:
    seen = set()
    for p in root.rglob("group*.csv"):
        d = p.parent
        if d in seen:
            continue
        seen.add(d)
        yield d
    # In case a hardware run only has runtime.txt and no perf CSVs.
    for p in root.rglob("runtime.txt"):
        d = p.parent
        if d in seen:
            continue
        seen.add(d)
        yield d


def find_gem5_stats_files(root: Path) -> Iterable[Path]:
    yield from root.rglob("stats.txt")


def build_rows(root: Path, include_raw: bool = False) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []

    hardware_dirs = find_hardware_run_dirs(root)
    for run_dir in hardware_dirs:
        meta = infer_metadata(run_dir)
        if meta is None:
            continue
        parsed = parse_perf_csvs(run_dir)
        row: Dict[str, object] = dict(meta)
        row.update(parsed["canonical"])
        if include_raw:
            row.update(parsed["raw"])
        rows.append(row)

    gem5_dirs = find_gem5_stats_files(root)
    for stats_path in gem5_dirs:
        run_dir = stats_path.parent
        meta = infer_metadata(run_dir)
        if meta is None:
            continue
        parsed = parse_gem5_run(stats_path)
        row = dict(meta)
        row.update(parsed["canonical"])
        if include_raw:
            row.update(parsed["raw"])
        rows.append(row)

    def sort_key(r: Dict[str, object]) -> Tuple[str, str, str, float, int]:
        # Numeric problem sizes sort numerically; otherwise lexicographically after numeric ones.
        ps = str(r.get("problem_size", ""))
        try:
            ps_key = float(ps)
        except ValueError:
            ps_key = float("inf")
        return (
            str(r.get("algorithm", "")),
            str(r.get("backend", "")),
            str(r.get("iteration", "")),
            ps_key,
            int(r.get("threads", 0) or 0),
        )

    rows.sort(key=sort_key)
    return rows


def write_csv(rows: List[Dict[str, object]], out_path: Path, include_raw: bool = False) -> None:
    # Stable first columns, then any extra raw columns sorted.
    base = META_COLUMNS + CANONICAL_COLUMNS
    extra = sorted({k for r in rows for k in r.keys()} - set(base))
    fieldnames = base + extra

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def main() -> None:
    ap = argparse.ArgumentParser(description="Aggregate perf hardware logs and gem5 stats into one comparable CSV.")
    ap.add_argument("root", type=Path, help="Root directory containing BFS/GEMM/FFT subtrees")
    ap.add_argument("-o", "--output", type=Path, default=Path("combined_stats.csv"), help="Output CSV path")
    ap.add_argument("--include-raw", action="store_true", help="Include raw perf/gem5 audit columns")
    args = ap.parse_args()

    rows = build_rows(args.root, include_raw=args.include_raw)
    write_csv(rows, args.output, include_raw=args.include_raw)
    print(f"wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
