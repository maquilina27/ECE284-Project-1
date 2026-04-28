#!/usr/bin/env python3

import os
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# Paths
# =========================

SPEC_DIR = os.path.expanduser("~/Downloads/")
CSV_PATH = os.path.join(SPEC_DIR, "corner_results_table.csv")
FIG_DIR = os.path.join(SPEC_DIR, "Figures")

os.makedirs(FIG_DIR, exist_ok=True)

# =========================
# Load data
# =========================

df = pd.read_csv(CSV_PATH)

# Clean ordering
benchmark_order = ["401.bzip2", "429.mcf", "456.hmmer", "458.sjeng", "470.lbm"]
config_order = [
    "small_direct",
    "small_assoc",
    "baseline",
    "balanced",
    "l1_heavy",
    "l2_heavy",
    "data_heavy",
    "instr_heavy",
    "high_assoc",
    "small_line",
    "large_line",
]

df["benchmark"] = pd.Categorical(df["benchmark"], categories=benchmark_order, ordered=True)
df["config"] = pd.Categorical(df["config"], categories=config_order, ordered=True)
df = df.sort_values(["benchmark", "config"])

# =========================
# Helper functions
# =========================

def save_plot(filename):
    path = os.path.join(FIG_DIR, filename)
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")

def plot_bar_by_benchmark(metric, ylabel, filename_prefix):
    for bench in benchmark_order:
        sub = df[df["benchmark"] == bench].copy()
        if sub.empty:
            continue

        plt.figure(figsize=(12, 5))
        plt.bar(sub["config"].astype(str), sub[metric])
        plt.xticks(rotation=45, ha="right")
        plt.ylabel(ylabel)
        plt.title(f"{ylabel} Across Configurations: {bench}")
        plt.grid(axis="y", alpha=0.3)
        save_plot(f"{filename_prefix}_{bench.replace('.', '_')}.png")

def plot_grouped_metric(metric, ylabel, filename):
    plt.figure(figsize=(14, 6))

    x = range(len(config_order))
    width = 0.15

    for i, bench in enumerate(benchmark_order):
        sub = df[df["benchmark"] == bench].set_index("config").reindex(config_order)
        offsets = [j + (i - 2) * width for j in x]
        plt.bar(offsets, sub[metric], width=width, label=bench)

    plt.xticks(list(x), config_order, rotation=45, ha="right")
    plt.ylabel(ylabel)
    plt.title(f"{ylabel} Across Configurations and Benchmarks")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    save_plot(filename)

# =========================
# Task 2/3: CPI plots
# =========================

plot_bar_by_benchmark("cpi", "CPI", "cpi_by_config")
plot_grouped_metric("cpi", "CPI", "cpi_grouped_all_benchmarks.png")

# =========================
# Task 3: Miss count plots
# =========================

plot_bar_by_benchmark("il1_misses", "L1 Instruction Cache Misses", "il1_misses_by_config")
plot_bar_by_benchmark("dl1_misses", "L1 Data Cache Misses", "dl1_misses_by_config")
plot_bar_by_benchmark("l2_misses", "L2 Cache Misses", "l2_misses_by_config")

# =========================
# Task 3: Miss rate plots
# =========================

plot_bar_by_benchmark("il1_miss_rate", "L1 Instruction Cache Miss Rate", "il1_miss_rate_by_config")
plot_bar_by_benchmark("dl1_miss_rate", "L1 Data Cache Miss Rate", "dl1_miss_rate_by_config")
plot_bar_by_benchmark("l2_miss_rate", "L2 Cache Miss Rate", "l2_miss_rate_by_config")

# =========================
# Task 4: Cost plots
# =========================

# Cost is configuration-dependent, not benchmark-dependent, so take first occurrence.
cost_df = df.drop_duplicates("config").sort_values("config")

plt.figure(figsize=(12, 5))
plt.bar(cost_df["config"].astype(str), cost_df["cost"])
plt.xticks(rotation=45, ha="right")
plt.ylabel("Cost [Arbitrary Units]")
plt.title("Cost Function Across Cache Configurations")
plt.grid(axis="y", alpha=0.3)
save_plot("task4_cost_by_config.png")

# Cost breakdown proxy based on your model assumptions
def size_to_kb(size):
    size = str(size).lower()
    if size.endswith("kb"):
        return float(size.replace("kb", ""))
    if size.endswith("mb"):
        return float(size.replace("mb", "")) * 1024
    raise ValueError(size)

def assoc_penalty(assoc):
    import math
    if assoc <= 1:
        return 1.0
    return 1.0 + 0.15 * math.log2(assoc)

breakdown_rows = []
for _, row in cost_df.iterrows():
    l1i = 4.0 * size_to_kb(row["l1i_size"]) * assoc_penalty(row["l1i_assoc"])
    l1d = 4.0 * size_to_kb(row["l1d_size"]) * assoc_penalty(row["l1d_assoc"])
    l2 = 1.0 * size_to_kb(row["l2_size"]) * assoc_penalty(row["l2_assoc"])

    breakdown_rows.append({
        "config": row["config"],
        "L1I Cost": l1i,
        "L1D Cost": l1d,
        "L2 Cost": l2,
    })

breakdown = pd.DataFrame(breakdown_rows)

plt.figure(figsize=(12, 5))
bottom = None
for col in ["L1I Cost", "L1D Cost", "L2 Cost"]:
    if bottom is None:
        plt.bar(breakdown["config"].astype(str), breakdown[col], label=col)
        bottom = breakdown[col]
    else:
        plt.bar(breakdown["config"].astype(str), breakdown[col], bottom=bottom, label=col)
        bottom = bottom + breakdown[col]

plt.xticks(rotation=45, ha="right")
plt.ylabel("Cost [Arbitrary Units]")
plt.title("Cost Function Breakdown by Cache Level")
plt.legend()
plt.grid(axis="y", alpha=0.3)
save_plot("task4_cost_breakdown_by_config.png")

# =========================
# Task 5: CPI-cost tradeoff
# =========================

for bench in benchmark_order:
    sub = df[df["benchmark"] == bench].copy()
    if sub.empty:
        continue

    plt.figure(figsize=(8, 6))
    plt.scatter(sub["cost"], sub["cpi"])

    for _, row in sub.iterrows():
        plt.annotate(
            str(row["config"]),
            (row["cost"], row["cpi"]),
            fontsize=8,
            xytext=(5, 3),
            textcoords="offset points"
        )

    plt.xlabel("Cost [Arbitrary Units]")
    plt.ylabel("CPI")
    plt.title(f"CPI vs Cost Tradeoff: {bench}")
    plt.grid(alpha=0.3)
    save_plot(f"task5_cpi_vs_cost_{bench.replace('.', '_')}.png")

# Combined CPI-cost scatter
plt.figure(figsize=(9, 6))
for bench in benchmark_order:
    sub = df[df["benchmark"] == bench]
    plt.scatter(sub["cost"], sub["cpi"], label=bench)

plt.xlabel("Cost [Arbitrary Units]")
plt.ylabel("CPI")
plt.title("CPI vs Cost Tradeoff Across All Benchmarks")
plt.legend()
plt.grid(alpha=0.3)
save_plot("task5_cpi_vs_cost_all_benchmarks.png")

# Evaluation function plot
plot_bar_by_benchmark("eval_cpi_cost", "CPI-Cost Evaluation Score", "task5_eval_score_by_config")
plot_grouped_metric("eval_cpi_cost", "CPI-Cost Evaluation Score", "task5_eval_score_grouped_all.png")

# =========================
# Best configuration tables
# =========================

best_cpi = df.loc[df.groupby("benchmark")["cpi"].idxmin()]
best_eval = df.loc[df.groupby("benchmark")["eval_cpi_cost"].idxmin()]

best_cpi.to_csv(os.path.join(FIG_DIR, "best_cpi_configs.csv"), index=False)
best_eval.to_csv(os.path.join(FIG_DIR, "best_eval_configs.csv"), index=False)

print("\nBest CPI configurations:")
print(best_cpi[["benchmark", "config", "cpi", "cost", "eval_cpi_cost"]])

print("\nBest CPI-cost evaluation configurations:")
print(best_eval[["benchmark", "config", "cpi", "cost", "eval_cpi_cost"]])

# =========================
# Average across all benchmarks
# =========================

avg_df = df.groupby("config", observed=False).agg({
    "cpi": "mean",
    "cost": "mean",
    "eval_cpi_cost": "mean",
    "il1_misses": "mean",
    "dl1_misses": "mean",
    "l2_misses": "mean",
    "il1_miss_rate": "mean",
    "dl1_miss_rate": "mean",
    "l2_miss_rate": "mean",
}).reset_index()

avg_df.to_csv(os.path.join(FIG_DIR, "average_results_by_config.csv"), index=False)

plt.figure(figsize=(12, 5))
plt.bar(avg_df["config"].astype(str), avg_df["cpi"])
plt.xticks(rotation=45, ha="right")
plt.ylabel("Average CPI")
plt.title("Average CPI Across All Benchmarks")
plt.grid(axis="y", alpha=0.3)
save_plot("average_cpi_by_config.png")

plt.figure(figsize=(12, 5))
plt.bar(avg_df["config"].astype(str), avg_df["eval_cpi_cost"])
plt.xticks(rotation=45, ha="right")
plt.ylabel("Average CPI-Cost Evaluation Score")
plt.title("Average CPI-Cost Evaluation Across All Benchmarks")
plt.grid(axis="y", alpha=0.3)
save_plot("average_eval_score_by_config.png")

plt.figure(figsize=(8, 6))
plt.scatter(avg_df["cost"], avg_df["cpi"])

for _, row in avg_df.iterrows():
    plt.annotate(
        str(row["config"]),
        (row["cost"], row["cpi"]),
        fontsize=8,
        xytext=(5, 3),
        textcoords="offset points"
    )

plt.xlabel("Cost [Arbitrary Units]")
plt.ylabel("Average CPI")
plt.title("Average CPI vs Cost Across All Benchmarks")
plt.grid(alpha=0.3)
save_plot("average_cpi_vs_cost.png")

print(f"\nAll figures saved in: {FIG_DIR}")