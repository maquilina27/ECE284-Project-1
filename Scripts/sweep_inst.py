import argparse
from gem5_utils import run_simulation, analyze_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="gem5 Automation Script")
    parser.add_argument("--model", type=str, default="bzip2", help="Benchmark name")
    parser.add_argument("--cpu", type=str, default="TimingSimpleCPU", help="CPU Type")
    parser.add_argument("--l1", type=str, default="128kB", help="L1 Cache Size")
    parser.add_argument("--l2", type=str, default="1MB", help="L2 Cache Size")
    parser.add_argument("--l1_assoc", type=int, default=2, help="L1 Associativity")
    parser.add_argument("--l2_assoc", type=int, default=1, help="L2 Associativity")
    
    args = parser.parse_args()

    max_inst_sizes = [10, 100, 1000, 10000, 100000, 1000000, 10000000, 100000000]

    cpi_list = []
    for max_inst in max_inst_sizes:
        stats_file = run_simulation(
            args.model, args.cpu, args.l1, args.l2, args.l1_assoc, args.l2_assoc, max_inst
        )

        if stats_file:
            res = analyze_results(stats_file)
            
            if isinstance(res, dict):
                cpi = res["CPI"]
                cpi_list.append(cpi)

    print("SWEEP COMPLETE")
    print(cpi_list)
