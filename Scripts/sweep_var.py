import argparse
from gem5_utils import run_simulation, analyze_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="gem5 Automation Script")
    parser.add_argument("--model", type=str, default="lbm", help="Benchmark name")
    parser.add_argument("--cpu", type=str, default="TimingSimpleCPU", help="CPU Type")
    parser.add_argument("--l1", type=str, default="128kB", help="L1 Cache Size")
    parser.add_argument("--l2", type=str, default="1MB", help="L2 Cache Size")
    parser.add_argument("--l1_assoc", type=int, default=2, help="L1 Associativity")
    parser.add_argument("--l2_assoc", type=int, default=1, help="L2 Associativity")
    parser.add_argument("--MAX_INST", type=int, default=10000000, help="MAX INST")
    
    args = parser.parse_args()
    model_list = ["bzip2", "mcf", "hmmer", "sjeng", "lbm"]
    #l1_size = ["512B", "1kB", "2kB", "4kB", "8kB", "16kB", "32kB", "64kB", "128kB", "256kB"]
    #l2_size = ["8kB", "16kB", "32kB", "64kB", "128kB", "256kB", "512kB", "1MB", "2MB", "4MB"]
    #l1_assoc = [1, 2, 4, 8, 16]
    l2_assoc = [1, 2, 4, 8, 16]

    all_results = []
    for model in model_list:
        cpi_list = []
        for l2a in l2_assoc:
            stats_file = run_simulation(
                model, args.cpu, args.l1, args.l2, args.l1_assoc, l2a, args.MAX_INST
                )

            if stats_file:
                res = analyze_results(stats_file)
                
                if isinstance(res, dict):
                    cpi = res["CPI"]
                    cpi_list.append(cpi)
        all_results.append(cpi_list)

    print("SWEEP COMPLETE")
    for i in range(5):
        print(all_results[i])
