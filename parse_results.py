#!/usr/bin/env python3

import os
import re
import csv
import math

SPEC_DIR = os.path.expanduser("~/Downloads/Project1_SPEC-master")
RESULTS_DIR = os.path.join(SPEC_DIR, "results_corners")
OUTPUT_CSV = os.path.join(SPEC_DIR, "corner_results_table.csv")

# Same config metadata as the bash script
CONFIGS = {
    "baseline":    {"l1i_size": "128kB", "l1d_size": "128kB", "l2_size": "1MB",   "l1i_assoc": 2, "l1d_assoc": 2, "l2_assoc": 1, "line": 64},
    "small_direct":{"l1i_size": "32kB",  "l1d_size": "32kB",  "l2_size": "512kB", "l1i_assoc": 1, "l1d_assoc": 1, "l2_assoc": 1, "line": 64},
    "small_assoc": {"l1i_size": "32kB",  "l1d_size": "32kB",  "l2_size": "512kB", "l1i_assoc": 4, "l1d_assoc": 4, "l2_assoc": 4, "line": 64},
    "balanced":    {"l1i_size": "128kB", "l1d_size": "128kB", "l2_size": "2MB",   "l1i_assoc": 2, "l1d_assoc": 2, "l2_assoc": 2, "line": 64},
    "l1_heavy":    {"l1i_size": "256kB", "l1d_size": "256kB", "l2_size": "1MB",   "l1i_assoc": 2, "l1d_assoc": 2, "l2_assoc": 2, "line": 64},
    "l2_heavy":    {"l1i_size": "64kB",  "l1d_size": "64kB",  "l2_size": "4MB",   "l1i_assoc": 2, "l1d_assoc": 2, "l2_assoc": 4, "line": 64},
    "data_heavy":  {"l1i_size": "64kB",  "l1d_size": "256kB", "l2_size": "2MB",   "l1i_assoc": 2, "l1d_assoc": 2, "l2_assoc": 2, "line": 64},
    "instr_heavy": {"l1i_size": "256kB", "l1d_size": "64kB",  "l2_size": "2MB",   "l1i_assoc": 2, "l1d_assoc": 2, "l2_assoc": 2, "line": 64},
    "high_assoc":  {"l1i_size": "128kB", "l1d_size": "128kB", "l2_size": "2MB",   "l1i_assoc": 8, "l1d_assoc": 8, "l2_assoc": 8, "line": 64},
    "small_line":  {"l1i_size": "128kB", "l1d_size": "128kB", "l2_size": "2MB",   "l1i_assoc": 2, "l1d_assoc": 2, "l2_assoc": 2, "line": 32},
    "large_line":  {"l1i_size": "128kB", "l1d_size": "128kB", "l2_size": "2MB",   "l1i_assoc": 2, "l1d_assoc": 2, "l2_assoc": 2, "line": 128},
}

def size_to_kb(size_str):
    s = size_str.lower()
    if s.endswith("kb"):
        return float(s.replace("kb", ""))
    if s.endswith("mb"):
        return float(s.replace("mb", "")) * 1024
    raise ValueError(f"Unknown size format: {size_str}")

def assoc_penalty(assoc):
    # Simple associativity penalty:
    # direct mapped = 1.00
    # 2-way = 1.15
    # 4-way = 1.30
    # 8-way = 1.45
    if assoc <= 1:
        return 1.00
    return 1.00 + 0.15 * math.log2(assoc)

def cache_cost(cfg):
    l1i_kb = size_to_kb(cfg["l1i_size"])
    l1d_kb = size_to_kb(cfg["l1d_size"])
    l2_kb = size_to_kb(cfg["l2_size"])

    l1i_cost = 4.0 * l1i_kb * assoc_penalty(cfg["l1i_assoc"])
    l1d_cost = 4.0 * l1d_kb * assoc_penalty(cfg["l1d_assoc"])
    l2_cost = 1.0 * l2_kb * assoc_penalty(cfg["l2_assoc"])

    return l1i_cost + l1d_cost + l2_cost

def extract_stat(stats_text, stat_name):
    pattern = rf"^{re.escape(stat_name)}\s+([0-9.eE+\-]+)"
    match = re.search(pattern, stats_text, re.MULTILINE)
    if match:
        value = match.group(1)
        if value.lower() == "nan":
            return 0.0
        return float(value)
    return None

def first_existing_stat(stats_text, names):
    for name in names:
        val = extract_stat(stats_text, name)
        if val is not None:
            return val
    return None

def parse_stats(stats_path):
    with open(stats_path, "r") as f:
        text = f.read()

    # Total instructions.
    total_inst = first_existing_stat(text, [
        "simInsts",
        "system.cpu.numInsts",
        "system.cpu.commitStats0.numInsts",
        "system.cpu.committedInsts",
    ])

    # Miss counts. Different gem5 versions/configs may use slightly different names.
    il1_misses = first_existing_stat(text, [
        "system.cpu.icache.overallMisses::total",
        "system.cpu.icache.demandMisses::total",
    ])

    dl1_misses = first_existing_stat(text, [
        "system.cpu.dcache.overallMisses::total",
        "system.cpu.dcache.demandMisses::total",
    ])

    l2_misses = first_existing_stat(text, [
        "system.l2.overallMisses::total",
        "system.l2.demandMisses::total",
    ])

    # Miss rates.
    il1_miss_rate = first_existing_stat(text, [
        "system.cpu.icache.overallMissRate::total",
        "system.cpu.icache.demandMissRate::total",
    ])

    dl1_miss_rate = first_existing_stat(text, [
        "system.cpu.dcache.overallMissRate::total",
        "system.cpu.dcache.demandMissRate::total",
    ])

    l2_miss_rate = first_existing_stat(text, [
        "system.l2.overallMissRate::total",
        "system.l2.demandMissRate::total",
    ])

    # If any miss count is missing, use zero instead of crashing.
    # This keeps the table generation robust.
    il1_misses = il1_misses if il1_misses is not None else 0.0
    dl1_misses = dl1_misses if dl1_misses is not None else 0.0
    l2_misses = l2_misses if l2_misses is not None else 0.0

    if total_inst is None or total_inst == 0:
        cpi = None
    else:
        cpi = 1.0 + ((il1_misses + dl1_misses) * 6.0 + l2_misses * 50.0) / total_inst

    return {
        "total_inst": total_inst,
        "il1_misses": il1_misses,
        "dl1_misses": dl1_misses,
        "l2_misses": l2_misses,
        "il1_miss_rate": il1_miss_rate,
        "dl1_miss_rate": dl1_miss_rate,
        "l2_miss_rate": l2_miss_rate,
        "cpi": cpi,
    }

def main():
    rows = []

    for bench_name in sorted(os.listdir(RESULTS_DIR)):
        bench_path = os.path.join(RESULTS_DIR, bench_name)
        if not os.path.isdir(bench_path):
            continue

        for config_name in sorted(os.listdir(bench_path)):
            config_path = os.path.join(bench_path, config_name)
            stats_path = os.path.join(config_path, "stats.txt")

            if not os.path.exists(stats_path):
                print(f"Missing stats.txt: {stats_path}")
                continue

            if config_name not in CONFIGS:
                print(f"Skipping unknown config: {config_name}")
                continue

            cfg = CONFIGS[config_name]
            stats = parse_stats(stats_path)
            cost = cache_cost(cfg)

            rows.append({
                "benchmark": bench_name,
                "config": config_name,
                "l1i_size": cfg["l1i_size"],
                "l1d_size": cfg["l1d_size"],
                "l2_size": cfg["l2_size"],
                "l1i_assoc": cfg["l1i_assoc"],
                "l1d_assoc": cfg["l1d_assoc"],
                "l2_assoc": cfg["l2_assoc"],
                "cache_line": cfg["line"],
                "total_inst": stats["total_inst"],
                "il1_misses": stats["il1_misses"],
                "dl1_misses": stats["dl1_misses"],
                "l2_misses": stats["l2_misses"],
                "il1_miss_rate": stats["il1_miss_rate"],
                "dl1_miss_rate": stats["dl1_miss_rate"],
                "l2_miss_rate": stats["l2_miss_rate"],
                "cpi": stats["cpi"],
                "cost": cost,
                "eval_cpi_cost": None if stats["cpi"] is None else stats["cpi"] * (1.0 + 0.1 * cost / 2201.6),
            })

    fieldnames = [
        "benchmark",
        "config",
        "l1i_size",
        "l1d_size",
        "l2_size",
        "l1i_assoc",
        "l1d_assoc",
        "l2_assoc",
        "cache_line",
        "total_inst",
        "il1_misses",
        "dl1_misses",
        "l2_misses",
        "il1_miss_rate",
        "dl1_miss_rate",
        "l2_miss_rate",
        "cpi",
        "cost",
        "eval_cpi_cost",
    ]

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote results table to: {OUTPUT_CSV}")

    # Print best CPI config per benchmark.
    print("\nBest CPI per benchmark:")
    benchmarks = sorted(set(row["benchmark"] for row in rows))
    for bench in benchmarks:
        bench_rows = [row for row in rows if row["benchmark"] == bench and row["cpi"] is not None]
        if not bench_rows:
            continue
        best = min(bench_rows, key=lambda x: x["cpi"])
        print(f"{bench}: {best['config']} | CPI={best['cpi']:.6f} | Cost={best['cost']:.2f}")

    # Print best CPI-cost eval config per benchmark.
    print("\nBest CPI-cost evaluation per benchmark:")
    for bench in benchmarks:
        bench_rows = [row for row in rows if row["benchmark"] == bench and row["eval_cpi_cost"] is not None]
        if not bench_rows:
            continue
        best = min(bench_rows, key=lambda x: x["eval_cpi_cost"])
        print(f"{bench}: {best['config']} | Eval={best['eval_cpi_cost']:.6f} | CPI={best['cpi']:.6f} | Cost={best['cost']:.2f}")

if __name__ == "__main__":
    main()