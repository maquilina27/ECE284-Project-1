import argparse
from gem5_utils import run_simulation, analyze_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="gem5 Automation Script")
    parser.add_argument("--model", type=str, default="bzip2", help="Benchmark name")
    parser.add_argument("--cpu", type=str, default="TimingSimpleCPU", help="CPU Type")
    parser.add_argument("--l1", type=str, default="128kB", help="L1 Cache Size")
    parser.add_argument("--l2", type=str, default="1MB", help="L2 Cache Size")
    parser.add_argument("--l1_assoc", type=int, default=2, help="Associativity")
    parser.add_argument("--l2_assoc", type=int, default=1, help="Associativity")
    parser.add_argument("--MAX_INST", type=int, default=100000000, help="Maximum Instructions")
    
    args = parser.parse_args()

    # 1. Run Simulation
    stats_file = run_simulation(args.model, args.cpu, args.l1, args.l2, args.l1_assoc, args.l2_assoc, args.MAX_INST)

    # 2. Analyze
    if stats_file:
        results = analyze_results(stats_file)
        print(f"\n--- Results for {args.model} ---")
        print(results["CPI"])
        print(results["Data"])
