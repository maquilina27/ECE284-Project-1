import argparse
from gem5_utils import run_simulation, analyze_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="gem5 Parameter Sweep")
    parser.add_argument("--model", type=str, default="mcf", help="Benchmark name")
    parser.add_argument("--cpu", type=str, default="TimingSimpleCPU", help="CPU Type")
    parser.add_argument("--MAX_INST", type=int, default=10000000, help="Max Instructions")
    
    args = parser.parse_args()

    # --- 1. Define Independent Sweep Parameters ---
    l1_sizes = ["64kB", "128kB", "256kB"]
    l2_sizes = ["512kB", "1MB", "2MB", "4MB"]
    
    # Define separate lists for associativities
    l1_assocs = [1, 2]
    l2_assocs = [1, 2]

    best_run = {"cpi": float('inf'), "config": None}
    worst_run = {"cpi": float('-inf'), "config": None}

    print(f"Starting Parameter Sweep for {args.model}...")
    print(f"{'L1':<7} | {'L1A':<4} | {'L2':<7} | {'L2A':<4} | {'CPI':<10}")
    print("-" * 50)

    # --- 2. The Four-Level Nested Loop ---
    for l1 in l1_sizes:
        for l1a in l1_assocs:
            for l2 in l2_sizes:
                for l2a in l2_assocs:
                    # Call run_simulation with DIFFERENT values for L1 and L2 assoc
                    stats_file = run_simulation(
                        args.model, args.cpu, l1, l2, l1a, l2a, args.MAX_INST
                    )

                    if stats_file:
                        res = analyze_results(stats_file)
                        
                        if isinstance(res, dict):
                            cpi = res["CPI"]
                            config_str = f"L1:{l1}({l1a}-way), L2:{l2}({l2a}-way)"
                            
                            print(f"{l1:<7} | {l1a:<4} | {l2:<7} | {l2a:<4} | {cpi:<10}")

                            if cpi < best_run["cpi"]:
                                best_run = {"cpi": cpi, "config": config_str}
                            
                            if cpi > worst_run["cpi"]:
                                worst_run = {"cpi": cpi, "config": config_str}

    # --- 3. Final Summary Report ---
    print("\n" + "="*45)
    print("SWEEP COMPLETE")
    print("-" * 45)
    print(f"BEST PERFORMANCE (Lowest CPI):")
    print(f"  CPI:    {best_run['cpi']}")
    print(f"  Config: {best_run['config']}")
    
    print(f"\nWORST PERFORMANCE (Highest CPI):")
    print(f"  CPI:    {worst_run['cpi']}")
    print(f"  Config: {worst_run['config']}")
    print("="*45)
